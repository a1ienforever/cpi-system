import React, { useState } from 'react';
import axios from 'axios';
import { generateCSR } from '../utils/crypto';
import { useNavigate } from 'react-router-dom';

const CSRForm = () => {
  const [formData, setFormData] = useState({
    commonName: '',
    organization: '',
    country: '',
    email: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const refreshToken = async () => {
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/auth/refresh/`,
        { refresh: localStorage.getItem('refresh') }
      );
      localStorage.setItem('token', response.data.access);
      return response.data.access;
    } catch (err) {
      console.error('Token refresh failed:', err);
      localStorage.removeItem('token');
      localStorage.removeItem('refresh');
      navigate('/login');
      throw new Error('Session expired. Please log in again.');
    }
  };

  // Функция для генерации уникального имени файла на основе временной метки
  const generateFileName = () => {
    const now = new Date();
    const timestamp = now.toISOString().replace(/[-:T.]/g, '').slice(0, 15); // Формат YYYYMMDD_HHMMSS
    return `private_key_${timestamp}.pem`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Please log in to submit a CSR.');
        navigate('/login');
        return;
      }

      // Generate CSR and private key
      const { csrPem, privateKeyPem } = generateCSR(formData);

      // Send CSR to server
      let response = await axios.post(
        `${process.env.REACT_APP_API_URL}/certificates/certificate-requests/`,
        { csr_pem: csrPem },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      setSuccess('CSR submitted successfully!');

      // Download private key with unique filename
      const blob = new Blob([privateKeyPem], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = generateFileName();
      a.click();
      window.URL.revokeObjectURL(url);

      // Clear form
      setFormData({ commonName: '', organization: '', country: '', email: '' });
    } catch (err) {
      if (err.response?.status === 401) {
        try {
          const newToken = await refreshToken();
          const { csrPem, privateKeyPem } = generateCSR(formData); // Regenerate for retry
          const response = await axios.post(
            `${process.env.REACT_APP_API_URL}/certificates/certificate-requests/`,
            { csr_pem: csrPem },
            {
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${newToken}`,
              },
            }
          );
          setSuccess('CSR submitted successfully!');

          // Download private key with unique filename
          const blob = new Blob([privateKeyPem], { type: 'text/plain' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = generateFileName();
          a.click();
          window.URL.revokeObjectURL(url);

          setFormData({ commonName: '', organization: '', country: '', email: '' });
        } catch (refreshErr) {
          setError(refreshErr.message || 'Failed to submit CSR after token refresh');
        }
      } else {
        setError(err.message || 'Failed to submit CSR');
        console.error('CSR submission error:', err);
      }
    }
  };

  return (
    <div className="card p-4">
      <h2>Generate Certificate Signing Request</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="commonName" className="form-label">Full Name (Common Name)</label>
          <input
            type="text"
            className="form-control"
            id="commonName"
            name="commonName"
            value={formData.commonName}
            onChange={handleChange}
            required
            placeholder="e.g., John Doe"
          />
        </div>
        <div className="mb-3">
          <label htmlFor="organization" className="form-label">Organization (Optional)</label>
          <input
            type="text"
            className="form-control"
            id="organization"
            name="organization"
            value={formData.organization}
            onChange={handleChange}
            placeholder="e.g., MyCompany"
          />
        </div>
        <div className="mb-3">
          <label htmlFor="country" className="form-label">Country (Optional)</label>
          <input
            type="text"
            className="form-control"
            id="country"
            name="country"
            value={formData.country}
            onChange={handleChange}
            placeholder="e.g., RU"
          />
        </div>
        <div className="mb-3">
          <label htmlFor="email" className="form-label">Email (Optional)</label>
          <input
            type="email"
            className="form-control"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="e.g., user@example.com"
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