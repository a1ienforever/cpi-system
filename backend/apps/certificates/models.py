from django.conf import settings
from django.db import models
from django.utils import timezone

class CertificateRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='csr_requests')
    csr_pem = models.TextField()  # PEM формат CSR
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'CSR #{self.id} by {self.user.email} - {self.status}'


class Certificate(models.Model):
    cert_pem = models.TextField()  # PEM сертификат
    serial_number = models.CharField(max_length=128, unique=True)
    issued_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    issued_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    # Связь с CSR, на основе которого выпущен сертификат
    csr = models.OneToOneField(CertificateRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='certificate')

    def __str__(self):
        return f'Cert SN:{self.serial_number} for {self.issued_to.email}'


class Revocation(models.Model):
    certificate = models.OneToOneField(Certificate, on_delete=models.CASCADE, related_name='revocation')
    revoked_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True)  # Например, компрометация, потеря ключа и т.п.

    def __str__(self):
        return f'Revocation of cert SN:{self.certificate.serial_number} at {self.revoked_at}'

