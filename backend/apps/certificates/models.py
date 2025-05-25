from django.conf import settings
from django.db import models
from django.utils import timezone

class Authority(models.Model):
    PURPOSE_CHOICES = [
        ("users", "Сотрудники"),
        ("services", "Сервисы"),
    ]

    name = models.CharField(max_length=100, verbose_name="Название УЦ")
    is_root = models.BooleanField(default=False, verbose_name="Корневой УЦ")
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, verbose_name="Назначение УЦ")
    cert_pem = models.TextField(verbose_name="Сертификат УЦ (PEM)")
    key_path = models.CharField(max_length=255, blank=True, null=True, verbose_name="Путь к приватному ключу")

    def __str__(self):
        return f"{self.name} ({'Корневой' if self.is_root else 'Подчинённый'})"

class CertificateRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('approved', 'Одобрен'),
        ('rejected', 'Отклонён'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='csr_requests', verbose_name="Пользователь")
    csr_pem = models.TextField(verbose_name="CSR в формате PEM")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус заявки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f'CSR #{self.id} пользователя {self.user.email} — {self.status}'


class Certificate(models.Model):
    cert_pem = models.TextField(verbose_name="Сертификат в формате PEM")
    serial_number = models.CharField(max_length=128, unique=True, verbose_name="Серийный номер сертификата")
    issued_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates', verbose_name="Владелец сертификата")
    csr = models.OneToOneField(CertificateRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificate', verbose_name="Связанный CSR")
    issued_by = models.ForeignKey(Authority, on_delete=models.PROTECT, verbose_name="Выдавший УЦ")
    issued_at = models.DateTimeField(default=timezone.now, verbose_name="Дата выдачи")
    expires_at = models.DateTimeField(verbose_name="Дата окончания срока")
    revoked = models.BooleanField(default=False, verbose_name="Отозван")
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата отзыва")

    def __str__(self):
        return f'Сертификат SN:{self.serial_number} для {self.issued_to.email}'


class Revocation(models.Model):
    certificate = models.OneToOneField(Certificate, on_delete=models.CASCADE, related_name='revocation', verbose_name="Отозванный сертификат")
    revoked_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отзыва")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Причина отзыва")

    def __str__(self):
        return f'Отзыв сертификата SN:{self.certificate.serial_number} от {self.revoked_at.strftime("%Y-%m-%d %H:%M:%S")}'

class CRL(models.Model):
    authority = models.OneToOneField(Authority, on_delete=models.CASCADE, related_name='crl')
    crl_pem = models.TextField(help_text="CRL in PEM format")
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"CRL for {self.authority} generated at {self.generated_at}"
