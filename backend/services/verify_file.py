#
# import logging
# from asn1crypto import cms, x509
# from OpenSSL import crypto
# from cryptography.hazmat.primitives import serialization, hashes
# from cryptography.x509 import load_pem_x509_certificate
# from django.utils import timezone
# from apps.certificates.models import Certificate, Authority
#
# logger = logging.getLogger(__name__)
#
# class SignatureVerificationService:
#     @staticmethod
#     def verify_signature(
#         file_content: bytes,
#         signature_bytes: bytes,
#         certificate: Certificate = None,
#     ) -> dict:
#         """
#         Проверяет подпись PKCS#7 (CMS) для файла.
#
#         Args:
#             file_content (bytes): Содержимое исходного файла.
#             signature_bytes (bytes): Подпись PKCS#7 в формате DER (.p7s).
#             certificate (Certificate, optional): Объект сертификата для проверки.
#
#         Returns:
#             dict: Результат проверки: {'valid': bool, 'message': str}.
#         """
#         try:
#             # Парсим подпись PKCS#7
#             try:
#                 pkcs7 = cms.ContentInfo.load(signature_bytes)
#                 if pkcs7['content_type'].native != 'signed_data':
#                     logger.error("Невалидный тип содержимого PKCS#7")
#                     return {"valid": False, "message": "Файл не является подписью PKCS#7."}
#                 signed_data = pkcs7['content'].parsed
#             except Exception as e:
#                 logger.error(f"Ошибка парсинга PKCS#7: {e}")
#                 return {"valid": False, "message": "Невалидный формат подписи PKCS#7."}
#
#             # Извлекаем сертификаты из подписи
#             certs = signed_data['certificates']
#             if not certs:
#                 logger.error("В подписи отсутствуют сертификаты")
#                 return {"valid": False, "message": "В подписи отсутствуют сертификаты."}
#             signer_cert_der = certs[0].dump()  # Первый сертификат — сертификат подписанта
#             signer_x509 = load_pem_x509_certificate(signer_cert_der)  # Загружаем как X509
#
#             # Проверяем соответствие сертификата, если предоставлен
#             if certificate:
#                 provided_cert = load_pem_x509_certificate(certificate.cert_pem.encode())
#                 if provided_cert.serial_number != signer_x509.serial_number:
#                     logger.error("Указанный сертификат не соответствует подписи")
#                     return {"valid": False, "message": "Указанный сертификат не соответствует подписи."}
#
#             # Проверяем срок действия сертификата
#             if signer_x509.not_valid_after < timezone.now():
#                 logger.error("Сертификат подписи истёк")
#                 return {"valid": False, "message": "Сертификат подписи истёк."}
#             if signer_x509.not_valid_before > timezone.now():
#                 logger.error("Сертификат подписи ещё не действителен")
#                 return {"valid": False, "message": "Сертификат подписи ещё не действителен."}
#
#             # Проверяем отзыв сертификата, если предоставлен
#             if certificate and certificate.revoked:
#                 logger.error("Сертификат отозван")
#                 return {"valid": False, "message": "Сертификат отозван."}
#
#             # Проверяем цепочку доверия
#             ca_cert_pem = None
#             try:
#                 ca = Authority.objects.first()
#                 ca_cert_pem = ca.cert_pem.encode() if ca else None
#             except Exception as e:
#                 logger.warning(f"Не удалось загрузить CA-сертификат: {e}")
#
#             if ca_cert_pem:
#                 try:
#                     ca_cert = load_pem_x509_certificate(ca_cert_pem)
#                     ca_x509 = crypto.X509.from_cryptography(ca_cert)
#                     signer_x509_openssl = crypto.X509.from_cryptography(signer_x509)
#                     store = crypto.X509Store()
#                     store.add_cert(ca_x509)
#                     store_ctx = crypto.X509StoreContext(store, signer_x509_openssl)
#                     store_ctx.verify_certificate()
#                     logger.debug("Цепочка доверия проверена успешно")
#                 except crypto.Error as e:
#                     logger.error(f"Ошибка проверки цепочки доверия: {e}")
#                     return {"valid": False, "message": f"Ошибка проверки цепочки доверия: {str(e)}"}
#
#             # Проверяем подпись
#             signer_info = signed_data['signer_infos'][0]
#             digest_algorithm = signer_info['digest_algorithm']['algorithm'].native
#             if digest_algorithm != 'sha256':
#                 logger.error(f"Неподдерживаемый алгоритм хеширования: {digest_algorithm}")
#                 return {"valid": False, "message": f"Неподдерживаемый алгоритм хеширования: {digest_algorithm}."}
#
#             # Вычисляем хеш файла
#             digest = hashes.Hash(hashes.SHA256())
#             digest.update(file_content)
#             computed_hash = digest.finalize()
#
#             # Проверяем подпись
#             try:
#                 public_key = signer_x509.public_key()
#                 signature = signer_info['signature'].native
#                 public_key.verify(
#                     signature,
#                     computed_hash,
#                     padding=signer_info['signature_algorithm']['algorithm'].native,
#                     algorithm=hashes.SHA256()
#                 )
#                 logger.info("Подпись проверена успешно")
#                 return {"valid": True, "message": "Подпись валидна."}
#             except Exception as e:
#                 logger.error(f"Ошибка проверки подписи: {e}")
#                 return {"valid": False, "message": f"Подпись невалидна: {str(e)}"}
#
#         except Exception as e:
#             logger.error(f"Ошибка верификации: {e}")
#             return {"valid": False, "message": f"Ошибка проверки подписи: {str(e)}"}
