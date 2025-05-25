from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_pem():
    # === Настройки ===
    common_name = "root@mail.ru"  # Замени на нужный CN
    key_file = "C:\\Users\\alienforever\\PycharmProjects\\cpi-system\\user_key\\root.key"
    csr_file = "C:\\Users\\alienforever\\PycharmProjects\\cpi-system\\user_key\\root.csr"

    # === Генерация приватного ключа RSA ===
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # === Сохраняем приватный ключ в файл ===
    with open(key_file, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # === Создание CSR ===
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
        )
        .sign(key, hashes.SHA256())
    )

    # === Сохраняем CSR в файл ===
    with open(csr_file, "wb") as f:
        f.write(csr.public_bytes(serialization.Encoding.PEM))

    # === Вывод PEM CSR в консоль ===
    csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()

    return csr_pem, key_file, csr_file

if __name__ == "__main__":
    csr_pem, key_file, csr_file = generate_pem()
    print("\n===== CSR PEM (вставь это в API) =====\n")
    print(csr_pem)