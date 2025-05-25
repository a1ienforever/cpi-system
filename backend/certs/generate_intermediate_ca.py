import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend


def create_intermediate_ca(name="Intermediate CA", out_dir="certs/ca_intermediate"):
    os.makedirs(out_dir, exist_ok=True)

    # --- Шаг 1: генерируем ключ ---
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)

    key_path = os.path.join(out_dir, "intermediate_ca_key.pem")
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # --- Шаг 2: создаём CSR ---
    csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"RU"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"My Intermediate CA Org"),
        x509.NameAttribute(NameOID.COMMON_NAME, name),
    ])).sign(key, hashes.SHA256())

    # --- Шаг 3: загружаем root CA ---
    with open("ca_root/root_ca_cert.pem", "rb") as f:
        root_cert = x509.load_pem_x509_certificate(f.read(), default_backend())

    with open("ca_root/root_ca_key.pem", "rb") as f:
        root_key = serialization.load_pem_private_key(f.read(), password=None)

    # --- Шаг 4: подписываем сертификат ---
    cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(root_cert.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=1825))  # 5 лет
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .sign(private_key=root_key, algorithm=hashes.SHA256())
    )

    cert_path = os.path.join(out_dir, "intermediate_ca_cert.pem")
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"✅ Intermediate CA created at: {out_dir}")
    print(f"🔑 Key: {key_path}")
    print(f"📄 Certificate: {cert_path}")


if __name__ == "__main__":
    create_intermediate_ca("Users Intermediate CA", "ca_intermediate_users")
    create_intermediate_ca("Services Intermediate CA", "ca_intermediate_services")


