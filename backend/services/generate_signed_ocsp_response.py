from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509 import ocsp, ReasonFlags
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend


def generate_signed_ocsp_response(certificate_obj, issuer_obj, issuer_private_key,
                                  revoked=False, revoked_at=None,
                                  reason=ReasonFlags.key_compromise) -> bytes:
    """
    Генерация и подпись OCSP-ответа для сертификата Certificate.

    :param certificate_obj: экземпляр Certificate (модель Django)
    :param issuer_obj: экземпляр Authority (модель Django, выдавший УЦ)
    :param issuer_private_key: приватный ключ выдавшего УЦ (cryptography private key object)
    :param revoked: True если сертификат отозван
    :param revoked_at: datetime отзыва (если revoked=True)
    :param reason: причина отзыва (cryptography.x509.ReasonFlags)
    :return: OCSP-ответ в DER формате (bytes)
    """
    # Загружаем сертификаты из PEM
    cert = x509.load_pem_x509_certificate(certificate_obj.cert_pem.encode(), backend=default_backend())
    issuer_cert = x509.load_pem_x509_certificate(issuer_obj.cert_pem.encode(), backend=default_backend())

    builder = ocsp.OCSPResponseBuilder()

    cert_status = ocsp.OCSPCertStatus.REVOKED if revoked else ocsp.OCSPCertStatus.GOOD
    revocation_time = revoked_at if revoked else None
    revocation_reason = reason if revoked else None

    builder = builder.add_response(
        cert=cert,
        issuer=issuer_cert,
        algorithm=hashes.SHA256(),
        cert_status=cert_status,
        this_update=datetime.utcnow(),
        next_update=datetime.utcnow() + timedelta(days=7),
        revocation_time=revocation_time,
        revocation_reason=revocation_reason,
    )

    ocsp_response = builder.sign(
        private_key=issuer_private_key,
        algorithm=hashes.SHA256(),
        responder_id=ocsp.OCSPResponderEncoding.HASH,
        certificates=[issuer_cert]
    )

    return ocsp_response.public_bytes(serialization.Encoding.DER)
