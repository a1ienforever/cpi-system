import KJUR from 'jsrsasign';

// Generates a CSR and private key in PEM format
export const generateCSR = ({ commonName, organization, country, email }) => {
  // Validate required input
  if (!commonName || typeof commonName !== 'string' || commonName.trim() === '') {
    throw new Error('Common Name is required and must be a non-empty string');
  }

  try {
    // Generate 2048-bit RSA key pair
    const kp = KJUR.KEYUTIL.generateKeypair('RSA', 2048);
    const privateKey = kp.prvKeyObj;
    const publicKey = kp.pubKeyObj;

    // Build subject string
    let subject = `/CN=${commonName.replace(/[/=]/g, '')}`; // Sanitize input
    if (organization) subject += `/O=${organization.replace(/[/=]/g, '')}`;
    if (country) subject += `/C=${country.replace(/[/=]/g, '')}`;
    if (email) subject += `/emailAddress=${email.replace(/[/=]/g, '')}`;

    // Create CSR
    const csr = new KJUR.asn1.csr.CertificationRequest({
      subject: { str: subject },
      sbjpubkey: publicKey,
      sigalg: 'SHA256withRSA',
      sbjprvkey: privateKey,
    });

    // Get PEM-formatted CSR and private key
    const csrPem = csr.getPEM();
    const privateKeyPem = KJUR.KEYUTIL.getPEM(privateKey, 'PKCS8PRV');

    return { csrPem, privateKeyPem };
  } catch (error) {
    console.error('CSR generation error:', error);
    throw new Error(`Failed to generate CSR: ${error.message}`);
  }
};