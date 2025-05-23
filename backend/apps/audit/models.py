from django.conf import settings
from django.db import models
from django.utils import timezone

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('issue_cert', 'Issue Certificate'),
        ('revoke_cert', 'Revoke Certificate'),
        ('login', 'User Login'),
        ('logout', 'User Logout'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_model = models.CharField(max_length=50, blank=True)  # Например, 'Certificate', 'CertificateRequest'
    target_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.timestamp.isoformat()} | {self.user} | {self.action} | {self.target_model}({self.target_id})'

