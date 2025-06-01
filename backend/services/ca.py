# services/ca.py
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from datetime import timedelta
from django.utils import timezone

import uuid

from apps.certificates.models import Authority, Certificate


def sign_csr(csr_pem: str, authority: Authority, user) -> Certificate:
    # Загружаем CSR
    csr = x509.load_pem_x509_csr(csr_pem.encode())

    # Проверка корректности CSR
    if not csr.is_signature_valid:
        raise ValueError("Invalid CSR signature")
    with open(authority.key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    # Готовим серийный номер и срок действия
    serial_number = uuid.uuid4().hex
    valid_from = timezone.now()
    valid_to = valid_from + timedelta(days=365)

    # Строим сертификат
    cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(x509.load_pem_x509_certificate(authority.cert_pem.encode()).subject)
        .public_key(csr.public_key())
        .serial_number(int(serial_number, 16))
        .not_valid_before(valid_from)
        .not_valid_after(valid_to)
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Сохраняем как строку
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()

    # Возвращаем объект Certificate (не сохраняем автоматически)
    return Certificate(
        cert_pem=cert_pem,
        serial_number=serial_number,
        issued_to=user,
        issued_at=valid_from,
        expires_at=valid_to,
        revoked=False,
        issued_by=authority,
    )
