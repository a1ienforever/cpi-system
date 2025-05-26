import KJUR from 'jsrsasign';

export const generateCSR = ({ commonName, organization }) => {
  // Генерируем ключевую пару
  const kp = KJUR.KEYUTIL.generateKeypair('RSA', 2048);
  const privateKey = kp.prvKeyObj;
  const publicKey = kp.pubKeyObj;

  // Создаём CSR
  const csr = new KJUR.asn1.csr.CertificationRequest({
    subject: {
      str: `/CN=${commonName}${organization ? `/O=${organization}` : ''}`,
    },
    sbjpubkey: publicKey,
    sigalg: 'SHA256withRSA',
    sbjprvkey: privateKey,
  });

  const csrPem = csr.getPEM();
  const privateKeyPem = KJUR.KEYUTIL.getPEM(privateKey, 'PKCS8PRV');

  return { csrPem, privateKeyPem };
};