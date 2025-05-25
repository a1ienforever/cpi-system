from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID
import datetime


def create_root_ca():
    # Генерация ключа
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)

    # Создание самоподписанного сертификата
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"RU"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"My Root CA Org"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"My Root CA"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    # Сохраняем в файлы
    with open("ca_root/root_ca_key.pem", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open("ca_root/root_ca_cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))


if __name__ == "__main__":
    create_root_ca()
