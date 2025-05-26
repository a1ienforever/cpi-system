import React, { useState } from 'react';
import axios from 'axios';
import { generateCSR } from '../utils/crypto';

const CSRForm = () => {
  const [formData, setFormData] = useState({
    commonName: '',
    organization: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      // Генерируем CSR и приватный ключ
      const { csrPem, privateKeyPem } = generateCSR(formData);

      // Отправляем CSR на сервер
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/api/certificate-requests/`,
        { csr_pem: csrPem },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer <your_token>', // Замени на динамический токен
          },
        }
      );

      setSuccess('CSR submitted successfully!');

      // Скачиваем приватный ключ
      const blob = new Blob([privateKeyPem], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'private_key.pem';
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit CSR');
    }
  };

  return (
    <div className="card p-4">
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="commonName" className="form-label">Full Name</label>
          <input
            type="text"
            className="form-control"
            id="commonName"
            name="commonName"
            value={formData.commonName}
            onChange={handleChange}
            required
          />
        </div>
        <div className="mb-3">
          <label htmlFor="organization" className="form-label">Organization</label>
          <input
            type="text"
            className="form-control"
            id="organization"
            name="organization"
            value={formData.organization}
            onChange={handleChange}
          />
        </div>
        {error && <div className="alert alert-danger">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}
        <button type="submit" className="btn btn-primary">Generate and Submit CSR</button>
      </form>
    </div>
  );
};

export default CSRForm;