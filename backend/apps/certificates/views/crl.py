from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.certificates.models import Authority
from services.crl import generate_and_save_crl


class CRLView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Получить CRL (список отозванных сертификатов)",
        operation_description="""
Возвращает действующий CRL (Certificate Revocation List) для пользовательского подчинённого УЦ (purpose="users").
Используется клиентами или браузерами для проверки отзыва сертификатов.
        """,
        responses={
            200: openapi.Response(
                description="CRL PEM (application/pem-certificate-chain)",
                examples={
                    "application/pem-certificate-chain": (
                        "-----BEGIN X509 CRL-----\n"
                        "MIIBfDCBuwIBATANBgkqhkiG9w0BAQUFADB..."
                        "\n-----END X509 CRL-----"
                    )
                },
                schema=openapi.Schema(type=openapi.TYPE_STRING, format="pem")
            ),
            404: openapi.Response(description="CA not found."),
            500: openapi.Response(description="Internal error while generating CRL.")
        }
    )
    def get(self, request):
        try:
            ca = Authority.objects.get(purpose="users", is_root=False)
            crl_record = generate_and_save_crl(ca)

            return Response(
                str(crl_record.crl_pem),
                content_type="application/pem-certificate-chain",
                status=status.HTTP_200_OK
            )
        except Authority.DoesNotExist:
            return Response({"detail": "CA not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
