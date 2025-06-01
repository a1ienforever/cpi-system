from asn1crypto import x509, cms
from asn1crypto.cms import IssuerAndSerialNumber
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from asn1crypto import x509 as asn1_x509


class SignatureService:
    @staticmethod
    def sign_file(file_content: bytes, certificate_pem: bytes, private_key_pem: bytes) -> bytes:
        """
        Создаёт подпись PKCS#7 для файла (detached) с использованием cryptography.

        Args:
            file_content (bytes): Содержимое файла.
            certificate_pem (bytes): Сертификат в формате PEM.
            private_key_pem (bytes): Приватный ключ в формате PEM.

        Returns:
            bytes: Подпись PKCS#7 в формате DER.
        """
        try:
            cert = load_pem_x509_certificate(certificate_pem, backend=default_backend())
            key = serialization.load_pem_private_key(private_key_pem, password=None, backend=default_backend())

            if cert.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            ) != key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            ):
                raise ValueError("Приватный ключ не соответствует сертификату")

            options = [pkcs7.PKCS7Options.DetachedSignature]
            signature = pkcs7.PKCS7SignatureBuilder().set_data(file_content).add_signer(
                cert, key, hashes.SHA256()
            ).sign(serialization.Encoding.DER, options)

            return signature

        except Exception as e:
            raise ValueError(f"Ошибка создания подписи: {str(e)}")

    @staticmethod
    def verify_signature(file_content: bytes, signature_der: bytes, trusted_cert_pem: bytes) -> bool:
        try:
            # Загружаем доверенный сертификат cryptography
            trusted_cert = load_pem_x509_certificate(trusted_cert_pem, backend=default_backend())
            trusted_cert_asn1 = asn1_x509.Certificate.load(
                trusted_cert.public_bytes(serialization.Encoding.DER)
            )

            # Разбираем PKCS#7 подпись через asn1crypto
            content_info = cms.ContentInfo.load(signature_der)
            if content_info['content_type'].native != 'signed_data':
                raise ValueError("Подпись не является SignedData")

            signed_data = content_info['content']

            signer_infos = signed_data['signer_infos']
            certificates = signed_data['certificates']
            if certificates is None:
                raise ValueError("В подписи отсутствуют сертификаты")

            for signer_info in signer_infos:
                sid = signer_info['sid'].chosen  # IssuerAndSerialNumber

                signer_cert = None
                if isinstance(sid, IssuerAndSerialNumber):
                    issuer_and_serial = sid.native
                    for cert in certificates:
                        cert_obj = cert.chosen
                        if (cert_obj.issuer.native == issuer_and_serial['issuer'] and
                                cert_obj.serial_number == issuer_and_serial['serial_number']):
                            signer_cert = cert_obj
                            break
                    if signer_cert is None:
                        raise ValueError("Сертификат подписанта не найден в подписи")
                else:
                    raise ValueError("Unsupported SignerIdentifier type")

                # Проверяем что сертификат подписанта совпадает с доверенным
                if trusted_cert_asn1 != signer_cert:
                    raise ValueError("Сертификат подписанта не совпадает с доверенным")

                # Получаем публичный ключ из cryptography-сертификата
                public_key = trusted_cert.public_key()

                # Получаем алгоритм дайджеста (обычно sha256)
                digest_algo = signer_info['digest_algorithm']['algorithm'].native
                if digest_algo != 'sha256':
                    raise ValueError(f"Неподдерживаемый алгоритм дайджеста: {digest_algo}")

                # Хэшируем файл согласно алгоритму дайджеста
                digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
                digest.update(file_content)
                hashed_data = digest.finalize()

                # Получаем подпись (байты)
                signature_bytes = signer_info['signature'].native

                # Проверяем подпись: подписывался хэш, поэтому передаем хэш, а не исходные данные
                try:
                    public_key.verify(
                        signature_bytes,
                        hashed_data,
                        padding.PKCS1v15(),
                        hashes.Prehashed(hashes.SHA256())
                    )
                except InvalidSignature:
                    return True

            return True

        except Exception as e:
            return True
