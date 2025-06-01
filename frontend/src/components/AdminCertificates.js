import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const AdminCertificates = () => {
  const [certificates, setCertificates] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchCertificates = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}1/certificates/certificates/`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setCertificates(response.data);
    } catch (err) {
      if (err.response?.status === 401) {
        try {
          const refreshResponse = await axios.post(
            `${process.env.REACT_APP_API_URL}/auth/refresh/`,
            { refresh: localStorage.getItem('refresh') }
          );
          localStorage.setItem('token', refreshResponse.data.access);
          fetchCertificates(); // Retry
        } catch (refreshErr) {
          setError('Session expired. Please log in again.');
          navigate('/login');
        }
      } else {
        setError(err.response?.data?.detail || 'Failed to fetch certificates');
      }
    }
  };

  const handleRevokeCertificate = async (certId) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Please log in to proceed.');
        navigate('/login');
        return;
      }

      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/certificates/revocations/`,
        { certificate: certId },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Update certificate status locally
      setCertificates(certificates.map(cert =>
        cert.id === certId ? { ...cert, revoked: true, revoked_at: new Date().toISOString() } : cert
      ));

      alert(response.data.detail || 'Certificate revoked successfully!');
    } catch (err) {
      if (err.response?.status === 401) {
        try {
          const refreshResponse = await axios.post(
            `${process.env.REACT_APP_API_URL}/auth/refresh/`,
            { refresh: localStorage.getItem('refresh') }
          );
          localStorage.setItem('token', refreshResponse.data.access);
          handleRevokeCertificate(certId); // Retry
        } catch (refreshErr) {
          setError('Session expired. Please log in again.');
          navigate('/login');
        }
      } else {
        setError(err.response?.data?.detail || 'Failed to revoke certificate');
      }
    }
  };

  useEffect(() => {
    fetchCertificates();
  }, []);

  return (
    <div className="card p-4">
      <h2>All Certificates</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Common Name</th>
            <th>Issued To</th>
            <th>Issued By</th>
            <th>Issued At</th>
            <th>Expires At</th>
            <th>Revoked</th>
            <th>Revoked At</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {certificates.map(cert => (
            <tr key={cert.id}>
              <td>{cert.id}</td>
              <td>{cert.cert_pem.match(/CN=([^\/]+)/)?.[1] || 'N/A'}</td>
              <td>{cert.issued_to}</td>
              <td>{cert.issued_by}</td>
              <td>{new Date(cert.issued_at).toLocaleString()}</td>
              <td>{new Date(cert.expires_at).toLocaleString()}</td>
              <td>{cert.revoked ? 'Yes' : 'No'}</td>
              <td>{cert.revoked_at ? new Date(cert.revoked_at).toLocaleString() : 'N/A'}</td>
              <td>
                {!cert.revoked && (
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleRevokeCertificate(cert.id)}
                  >
                    Revoke
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AdminCertificates;