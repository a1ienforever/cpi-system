from django.contrib import admin
from django import forms
from django.core.mail import send_mail
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone

from services.ca import sign_csr
from .models import CertificateRequest, Certificate, Authority

class ApproveRequestsForm(forms.Form):
    authority = forms.ModelChoiceField(
        queryset=Authority.objects.all(),
        label="Удостоверяющий центр",
        required=True,
    )

@admin.register(CertificateRequest)
class CertificateRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'user')
    search_fields = ('user__email', 'csr_pem')
    list_editable = ('status',)
    readonly_fields = ('user', 'csr_pem', 'created_at', 'updated_at')
    actions = ['approve_requests', 'reject_requests']
    ordering = ('-created_at',)

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'Email пользователя'

    def approve_requests(self, request, queryset):
        if request.POST.get('post'):
            # Обработка отправленной формы
            form = ApproveRequestsForm(request.POST)
            if form.is_valid():
                authority = form.cleaned_data['authority']
                updated = 0
                for req in queryset.filter(status='pending'):
                    try:
                        # Создаём сертификат с помощью сервиса
                        certificate = sign_csr(req.csr_pem, authority, req.user)
                        certificate.csr = req  # Связываем сертификат с заявкой
                        certificate.save()

                        # Обновляем статус заявки
                        req.status = 'approved'
                        req.save()
                        updated += 1

                        # Отправляем уведомление пользователю (опционально)
                        send_mail(
                            'Ваша заявка на сертификат одобрена',
                            f'Заявка #{req.id} одобрена. Скачайте сертификат в личном кабинете.',
                            'from@example.com',
                            [req.user.email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        self.message_user(request, f'Ошибка при обработке заявки #{req.id}: {str(e)}', level='error')
                self.message_user(request, f'Успешно обработано {updated} заявок.')
                return
            else:
                self.message_user(request, 'Выберите удостоверяющий центр.', level='error')
        else:
            # Отображаем форму для выбора УЦ
            return render(
                request,
                'admin/approve_requests_form.html',
                {
                    'title': 'Одобрение заявок',
                    'form': ApproveRequestsForm(),
                    'opts': self.model._meta,
                    'queryset': queryset,
                    'action': 'approve_requests',
                    'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
                }
            )

    approve_requests.short_description = 'Одобрить выбранные заявки'

    def reject_requests(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} заявок отклонено.')

    reject_requests.short_description = 'Отклонить выбранные заявки'

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    # Поля для отображения в списке
    list_display = (
        'serial_number',
        'issued_to_email',
        'issued_at',
        'expires_at',
        'revoked',
        'revoked_at',
        'csr_id',
    )

    # Поля, доступные для редактирования в списке
    list_editable = ('revoked',)

    # Фильтры в боковой панели
    list_filter = (
        'revoked',
        'issued_to',
        'issued_by',
        'issued_at',
        'expires_at',
    )

    # Поля для поиска
    search_fields = (
        'serial_number',
        'issued_to__email',
        'issued_by__full_name',
        'cert_pem',
    )

    # Поля для формы редактирования
    fields = (
        'cert_pem',
        'serial_number',
        'issued_to',
        'csr',
        'issued_by',
        'issued_at',
        'expires_at',
        'revoked',
        'revoked_at',
    )

    # Поля только для чтения
    readonly_fields = (
        'serial_number',
        'issued_at',
        'revoked_at',
    )

    # Действия
    actions = ['revoke_certificates']

    def issued_to_email(self, obj):
        return obj.issued_to.email

    def issued_by_name(self, obj):
        return obj.issued_by.name
    issued_by_name.short_description = 'УЦ'

    def csr_id(self, obj):
        return obj.csr.id if obj.csr else 'Нет'
    csr_id.short_description = 'ID CSR'

    # Действие для отзыва сертификатов
    def revoke_certificates(self, request, queryset):
        updated = queryset.filter(revoked=False).update(
            revoked=True,
            revoked_at=timezone.now()
        )
        self.message_user(
            request,
            f"Успешно отозвано {updated} сертификатов."
        )
    revoke_certificates.short_description = "Отозвать выбранные сертификаты"

    # Ограничение редактирования revoked_at
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.revoked:
            return self.readonly_fields + ('revoked',)
        return self.readonly_fields

    # Автоматическое обновление revoked_at при изменении revoked
    def save_model(self, request, obj, form, change):
        if form.cleaned_data.get('revoked') and not obj.revoked_at:
            obj.revoked_at = timezone.now()
        elif not form.cleaned_data.get('revoked'):
            obj.revoked_at = None
        super().save_model(request, obj, form, change)