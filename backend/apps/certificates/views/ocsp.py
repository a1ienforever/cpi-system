from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from apps.certificates.models import Certificate, Authority
from services.generate_signed_ocsp_response import generate_signed_ocsp_response


class OCSPResponderView(APIView):
    """
    Обработка OCSP-запросов (DER-формат) и возврат подписанного OCSP-ответа.
    """
    permission_classes = []
    parser_classes = [MultiPartParser]  # Обрабатывает multipart/form-data

    @swagger_auto_schema(
        operation_summary="OCSP-запрос",
        operation_description="Отправьте DER-файл запроса (OCSP) и получите DER-ответ.",
        manual_parameters=[
            openapi.Parameter(
                name="file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="OCSP-запрос в DER-формате",
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="OCSP-ответ в DER-формате",
                content={"application/ocsp-response": {}}
            ),
            400: "Невалидный запрос"
        }
    )
    def post(self, request):

        try:
            if 'file' not in request.FILES:
                return Response({"detail": "OCSP file is required."}, status=status.HTTP_400_BAD_REQUEST)
            #TODO: пройтись дебагером.
            ocsp_request_der = request.FILES["file"].read()
            ocsp_request = x509.ocsp.load_der_ocsp_request(ocsp_request_der)

            serial_number = ocsp_request.serial_number

            cert_obj = Certificate.objects.filter(serial_number=str(serial_number)).first()
            if not cert_obj:
                return Response({"detail": "Certificate not found."}, status=status.HTTP_404_NOT_FOUND)

            issuer_obj = cert_obj.issued_by
            if not issuer_obj.cert_pem or not issuer_obj.key_path:
                return Response({"detail": "Issuer CA data incomplete."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            with open(issuer_obj.key_path, "rb") as key_file:
                issuer_private_key = serialization.load_pem_private_key(
                    key_file.read(), password=None, backend=default_backend()
                )

            ocsp_response_der = generate_signed_ocsp_response(
                certificate_obj=cert_obj,
                issuer_obj=issuer_obj,
                issuer_private_key=issuer_private_key,
                revoked=cert_obj.revoked,
                revoked_at=cert_obj.revoked_at
            )

            return Response(
                ocsp_response_der,
                content_type="application/ocsp-response",
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"detail": f"Error processing OCSP request: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
