from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CertificateRequest, Certificate, Revocation, Authority

User = get_user_model()


class CertificateRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = CertificateRequest
        fields = [
            "id",
            "user",
            "user_email",
            "csr_pem",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]


class AuthoritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Authority
        fields = [
            "id",
            "name",
            "is_root",
            "purpose",
            "cert_pem",
            "key_path",
        ]
        read_only_fields = ["cert_pem", "key_path", "is_root"]


class CertificateSerializer(serializers.ModelSerializer):
    issued_to = serializers.StringRelatedField(read_only=True)
    issued_by = serializers.StringRelatedField(read_only=True)
    csr = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Certificate
        fields = [
            "id",
            "serial_number",
            "cert_pem",
            "issued_to",
            "issued_by",
            "csr",
            "issued_at",
            "expires_at",
            "revoked",
            "revoked_at",
        ]
        read_only_fields = ["cert_pem", "serial_number", "issued_to", "issued_by", "issued_at", "revoked", "revoked_at"]


class RevocationSerializer(serializers.ModelSerializer):
    cert_serial = serializers.CharField(source="certificate.serial_number", read_only=True)

    class Meta:
        model = Revocation
        fields = [
            "id",
            "certificate",
            "cert_serial",
            "revoked_at",
            "reason",
        ]
        read_only_fields = ["revoked_at"]
