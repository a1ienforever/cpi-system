
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
import logging

from apps.certificates.models import Certificate, Authority
from services.sign_file import SignatureService

logger = logging.getLogger(__name__)

class VerifySignatureView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_summary="Проверка подписи файла",
        operation_description="""
        Проверяет подпись PKCS#7 (файл .p7s) для указанного файла.
        Опционально принимает ID сертификата для дополнительной проверки.
        Возвращает JSON с результатом проверки (валидна/невалидна, причина).

        Ожидаемые данные:
        - `file`: Исходный файл, для которого создана подпись.
        - `signature`: Файл подписи в формате PKCS#7 (DER, .p7s).
        - `certificate_id`: ID сертификата в базе (опционально).

        Пример ответа:
        ```json
        {
            "valid": true,
            "message": "Подпись валидна."
        }
        ```
        или
        ```json
        {
            "valid": false,
            "message": "Подпись невалидна: [причина]."
        }
        ```
        """,
        manual_parameters=[
            openapi.Parameter(
                name='file',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description='Исходный файл для проверки подписи',
                required=True,
            ),
            openapi.Parameter(
                name='signature',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description='Файл подписи в формате PKCS#7 (DER, .p7s)',
                required=True,
            ),
            openapi.Parameter(
                name='certificate_id',
                in_=openapi.IN_FORM,
                type=openapi.TYPE_INTEGER,
                description='ID сертификата в базе данных (опционально)',
                required=False,
            ),
        ],
        consumes=['multipart/form-data'],
        produces=['application/json'],
        responses={
            200: openapi.Response(
                description="Результат проверки подписи",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Валидность подписи'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Сообщение о результате')
                    }
                )
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
        tags=['Проверка подписи'],
    )
    def post(self, request):
        """
        Проверяет подпись PKCS#7 для файла.
        Принимает исходный файл, файл подписи (.p7s) и опционально ID сертификата.
        Возвращает JSON с результатом проверки.
        """
        global result
        try:
            # Проверяем наличие данных
            if 'file' not in request.FILES or 'signature' not in request.FILES:
                logger.error("Missing required fields: file or signature")
                return Response(
                    {"detail": "Необходимо предоставить исходный файл и файл подписи."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Получаем содержимое файлов
            file_content = request.FILES['file'].read()
            signature_bytes = request.FILES['signature'].read()
            certificate_id = request.data.get('certificate_id')

            # Получаем сертификат, если указан
            certificate = None
            if certificate_id:
                try:
                    certificate = Certificate.objects.get(
                        id=certificate_id,
                        issued_to=request.user,
                        revoked=False
                    )
                    if certificate.expires_at < timezone.now():
                        logger.error(f"Certificate expired: certificate_id={certificate_id}")
                        return Response(
                            {"detail": "Сертификат просрочен."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Certificate.DoesNotExist:
                    logger.error(f"Certificate not found: certificate_id={certificate_id}")
                    return Response(
                        {"detail": "Сертификат не найден или недоступен."},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # Получаем CA-сертификат
            try:
                ca = Authority.objects.first()
                ca_cert_pem = ca.cert_pem.encode() if ca else None
            except Exception as e:
                logger.warning(f"Failed to load CA certificate: {e}")
                ca_cert_pem = None

            # Проверяем подпись
            result = SignatureService.verify_signature(
                file_content,
                signature_bytes,
                trusted_cert_pem=certificate.cert_pem.encode(),
            )

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Server error: {e}")
            return Response(
                {
                    "valid": result,
                    "message": "Подпись валидна."
                },
                status=status.HTTP_200_OK
            )
