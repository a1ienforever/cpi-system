import os
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.x509 import ReasonFlags  # <-- вот это правильно
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

from apps.certificates.models import Authority, Revocation, CRL


def generate_crl(ca: Authority) -> bytes:
    if not ca.cert_pem or not ca.key_path:
        raise ValueError("CA must have certificate and private key.")

    # Загружаем CA сертификат
    ca_cert = x509.load_pem_x509_certificate(ca.cert_pem.encode(), backend=default_backend())

    # Загружаем приватный ключ из файла
    if not os.path.exists(ca.key_path):
        raise FileNotFoundError(f"Private key not found at path: {ca.key_path}")
    with open(ca.key_path, "rb") as key_file:
        ca_key = serialization.load_pem_private_key(key_file.read(), password=None, backend=default_backend())

    # Начинаем сборку CRL
    now = datetime.utcnow()
    builder = x509.CertificateRevocationListBuilder()
    builder = builder.issuer_name(ca_cert.subject)
    builder = builder.last_update(now)
    builder = builder.next_update(now + timedelta(days=7))

    # Добавляем все отозванные сертификаты
    revoked = Revocation.objects.filter(certificate__issued_by=ca)
    for entry in revoked:
        revoked_cert = (
            x509.RevokedCertificateBuilder()
            .serial_number(entry.certificate.serial_number)
            .revocation_date(entry.revoked_at)
            .add_extension(
                x509.CRLReason(ReasonFlags.key_compromise),
                critical=False
            )
            .build(backend=default_backend())
        )
        builder = builder.add_revoked_certificate(revoked_cert)

    # Подписываем CRL
    crl = builder.sign(private_key=ca_key, algorithm=hashes.SHA256(), backend=default_backend())

    return crl.public_bytes(encoding=serialization.Encoding.PEM)

def generate_and_save_crl(ca: Authority) -> CRL:
    crl_pem = generate_crl(ca)  # Вызов твоей функции генерации

    # Парсим CRL, чтобы достать дату истечения
    crl_obj = x509.load_pem_x509_crl(crl_pem, backend=default_backend())
    expires_at = crl_obj.next_update

    crl_record, created = CRL.objects.update_or_create(
        authority=ca,
        defaults={
            "crl_pem": crl_pem.decode() if isinstance(crl_pem, bytes) else crl_pem,
            "generated_at": datetime.utcnow(),
            "expires_at": expires_at,
        }
    )
    return crl_record

