from cryptography import x509
from cryptography.x509 import ocsp, load_pem_x509_certificate
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

def load_cert(path: str) -> x509.Certificate:
    with open(path, "rb") as f:
        return load_pem_x509_certificate(f.read(), backend=default_backend())

def generate_ocsp_request(cert_path: str, issuer_path: str, output_path: str):
    cert = load_cert(cert_path)
    issuer = load_cert(issuer_path)

    builder = ocsp.OCSPRequestBuilder()
    builder = builder.add_certificate(cert, issuer, hashes.SHA256())

    ocsp_req = builder.build()
    der_bytes = ocsp_req.public_bytes(encoding=x509.Encoding.DER)

    with open(output_path, "wb") as f:
        f.write(der_bytes)

    print(f"OCSP-запрос сохранён в: {output_path}")

if __name__ == "__main__":
    # Укажи пути к сертификатам
    cert_path = """-----BEGIN CERTIFICATE-----
MIID/zCCAeegAwIBAgIQUysSZ8vDQh2psVvGfwB6HjANBgkqhkiG9w0BAQsFADBO
MQswCQYDVQQGEwJSVTEfMB0GA1UECgwWTXkgSW50ZXJtZWRpYXRlIENBIE9yZzEe
MBwGA1UEAwwVVXNlcnMgSW50ZXJtZWRpYXRlIENBMB4XDTI1MDUyNTEyMzA1MloX
DTI2MDUyNTEyMzA1MlowFzEVMBMGA1UEAwwMcm9vdEBtYWlsLnJ1MIIBIjANBgkq
hkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvkmRZay0kqIklVD/QrqxQO9Y/rGI/XmU
NS1u1Jq2LmvVpzrgy1kHGuzVg+o43hTRbFRIwkBtsZ6LiZB7zhafZdcqCvFMoi42
ROytGnMJ3u5CmPDqNhBh3wq2orlq6cXrIWUgc0mj3Bf/lTQPbVFEa9tGeZzEFH1d
9KwSIBPC4RfgLkTcNf0tpTbL5MhOfy9xPEbBwSlbSgNp7mKuJpEn88LfCJl3P0Vq
98ZgR68YZSUva+grP5okPFBMnA0TH2jWNJTQIuAHYhBR9nRT+Xo9Grsw5S8Up+V7
+JVgGbrJEOTIY0h2hNmSIafRaImppZd9bcb0g0WeG0teWSoc/8gIDwIDAQABoxAw
DjAMBgNVHRMBAf8EAjAAMA0GCSqGSIb3DQEBCwUAA4ICAQAiJofqp6tjNCa/6G36
VORBD7jpvBDhGo0s8fLwK1Q0pmr+fbcmgsatthXg0ixa6m0yLoTclq9SQR5iw9Zi
dkRNUHkCBVAwwTV5taKVQlhZ3AMfrMlkPUoY9pBxRmZxG1M95TK4nK6LKsPL/SOa
7MAk9sZ2hG+aexhe91bP/dhSwxDHWMyuUd2PbBaabhl//9FtOiWp0NwlIyFpdflj
0l3ltCRwROEWt/BEwr921hgFr0NNFHICPPpPpn3w4IacaFxAOjcp4aDPJ9W6jLeI
Z5iIEKB5JiHjkD75GFw++FFbc2sdB3/rKlznCcTraGURBvUZ9mCuY2Bbp7Oidtpc
sZio8/i/mik+dLYh20KbVhbb6wok8MdRE5IPbVeRKbkHt2V2uOjJvRsAR8+odXw5
tJi1pA7zRVCA395dQX0Z4WDHKjOxDiydaMAlUpW0/8hmNYXKQO0AdwTJo3IpuKFQ
B9gvhetbnNutKHkEBVzJCdXQh1Zjfi0QrLM80om5SEcR4nU3muC/PvI4UGcM80lr
DV4QV9OMYxeo6YTkaeW2TPtkyeCLGlVxivBD9MBSzHMoWyDBIxrO2VCwB5R5/S7k
eRmhabYH03E2bXpUm5DSwIESajwYNxv8USeMOvxF0hW774saKQtytQO4Xe4pWOzm
t/uoDxg7JqPAtELtuTPk+On2eQ==
-----END CERTIFICATE-----
"""
    issuer_path = "issuer_cert.pem"
    output_path = "ocsp_request.der"

    generate_ocsp_request(cert_path, issuer_path, output_path)
