from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse
from apps.certificates.models import Certificate
from services.sign_file import SignatureService
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate
from django.utils import timezone

class SignFileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Подпись файла",
        operation_description="""
        Принимает файл для подписи, приватный ключ в формате PEM и ID сертификата.
        Сертификат извлекается из базы данных по certificate_id.
        Возвращает подпись в формате PKCS#7 (файл .p7s, DER).

        Ожидаемые данные:
        - `file`: Файл для подписи (любой формат).
        - `key`: Приватный ключ в формате PEM.
        - `certificate_id`: ID сертификата, хранящегося на сервере.

        Пример приватного ключа:
        ```
        -----BEGIN PRIVATE KEY-----
        MII...
        -----END PRIVATE KEY-----
        ```

        Возвращает файл подписи с MIME-типом `application/pkcs7-signature` и именем `signature.p7s`.
        """,
        manual_parameters=[
            openapi.Parameter(
                name='file',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description='Файл для подписи (любой формат)',
                required=True,
            ),
            openapi.Parameter(
                name='key',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description='Приватный ключ в формате PEM',
                required=True,
            ),
            openapi.Parameter(
                name='certificate_id',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                description='ID сертификата в базе данных',
                required=True,
            ),
        ],
        consumes=['multipart/form-data'],
        produces=['application/pkcs7-signature'],
        responses={
            200: openapi.Response(
                description="Файл подписи PKCS#7",
                schema=openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description="Файл подписи в формате .p7s (DER)"
                ),
                headers={
                    'Content-Disposition': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='attachment; filename="signature.p7s"'
                    ),
                    'Content-Type': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='application/pkcs7-signature'
                    ),
                }
            ),
            400: openapi.Response(
                description="Неверный запрос",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: openapi.Response(
                description="Сертификат не найден",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            500: openapi.Response(
                description="Ошибка сервера",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
        },
        tags=['Подпись файлов'],
    )
    def post(self, request):
        """
        Принимает файл для подписи, приватный ключ и ID сертификата.
        Возвращает подпись в формате PKCS#7 (.p7s, DER).
        """
        try:
            # Проверяем наличие данных
            if 'file' not in request.FILES or 'key' not in request.FILES or 'certificate_id' not in request.data:
                return Response(
                    {"detail": "Необходимо предоставить файл, приватный ключ и ID сертификата."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Получаем содержимое файлов
            file_content = request.FILES['file'].read()
            private_key_pem = request.FILES['key'].read()
            certificate_id = request.data.get('certificate_id')

            # Проверяем формат приватного ключа
            if not private_key_pem.startswith(b'-----BEGIN PRIVATE KEY-----'):
                return Response(
                    {"detail": "Некорректный формат приватного ключа."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Получаем сертификат из базы
            try:
                certificate = Certificate.objects.get(
                    id=certificate_id,
                    issued_to=request.user,
                    revoked=False
                )
            except Certificate.DoesNotExist:
                return Response(
                    {"detail": "Сертификат не найден или недоступен."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Проверяем срок действия сертификата
            if certificate.expires_at < timezone.now():
                return Response(
                    {"detail": "Сертификат просрочен."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if certificate.revoked:
                return Response(
                    {"detail": "Сертификат отозван."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Валидация соответствия ключа и сертификата
            cert = load_pem_x509_certificate(certificate.cert_pem.encode())
            key = serialization.load_pem_private_key(private_key_pem, password=None)
            if cert.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ) != key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ):
                return Response(
                    {"detail": "Приватный ключ не соответствует сертификату."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Вызываем сервис для подписи
            signature = SignatureService.sign_file(
                file_content=file_content,
                certificate_pem=certificate.cert_pem.encode(),
                private_key_pem=private_key_pem
            )

            # Возвращаем подпись как файл
            response = HttpResponse(
                content=signature,
                content_type='application/pkcs7-signature'
            )
            response['Content-Disposition'] = 'attachment; filename="signature.p7s"'
            return response

        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Ошибка: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )