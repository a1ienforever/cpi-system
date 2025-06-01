import React, { useState } from 'react';
import KJUR from 'jsrsasign';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const SignFile = () => {
  const [file, setFile] = useState(null);
  const [privateKeyFile, setPrivateKeyFile] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handlePrivateKeyChange = (e) => {
    setPrivateKeyFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!file || !privateKeyFile) {
      setError('Please upload both a file and a private key.');
      return;
    }

    try {
      // Read file content
      const fileReader = new FileReader();
      const fileContent = await new Promise((resolve) => {
        fileReader.onload = () => resolve(fileReader.result);
        fileReader.readAsArrayBuffer(file);
      });

      // Read private key
      const keyReader = new FileReader();
      const privateKeyPem = await new Promise((resolve) => {
        keyReader.onload = () => resolve(keyReader.result);
        keyReader.readAsText(privateKeyFile);
      });

      // Load private key
      const privateKey = KJUR.KEYUTIL.getKey(privateKeyPem);

      // Create signature
      const sig = new KJUR.crypto.Signature({ alg: 'SHA256withRSA' });
      sig.init(privateKey);
      sig.updateString(new TextDecoder().decode(fileContent));
      const signature = sig.sign();

      // Convert signature to base64
      const signatureBase64 = KJUR.hextob64(signature);

      // Send signature to backend (optional)
      const token = localStorage.getItem('token');
      await axios.post(
        `${process.env.REACT_APP_API_URL}/signatures/`,
        { file_name: file.name, signature: signatureBase64 },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Download signature
      const blob = new Blob([signatureBase64], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${file.name}.sig`;
      a.click();
      window.URL.revokeObjectURL(url);

      setSuccess('File signed successfully!');
    } catch (err) {
      if (err.response?.status === 401) {
        try {
          const refreshResponse = await axios.post(
            `${process.env.REACT_APP_API_URL}/auth/refresh/`,
            { refresh: localStorage.getItem('refresh') }
          );
          localStorage.setItem('token', refreshResponse.data.access);
          handleSubmit(e); // Retry
        } catch (refreshErr) {
          setError('Session expired. Please log in again.');
          navigate('/login');
        }
      } else {
        setError(err.message || 'Failed to sign file');
      }
    }
  };

  return (
    <div className="card p-4">
      <h2>Sign File</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="file" className="form-label">Upload File</label>
          <input
            type="file"
            className="form-control"
            id="file"
            onChange={handleFileChange}
            required
          />
        </div>
        <div className="mb-3">
          <label htmlFor="privateKey" className="form-label">Upload Private Key</label>
          <input
            type="file"
            className="form-control"
            id="privateKey"
            onChange={handlePrivateKeyChange}
            required
          />
        </div>
        {error && <div className="alert alert-danger">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}
        <button type="submit" className="btn btn-primary">Sign File</button>
      </form>
    </div>
  );
};

export default SignFile;