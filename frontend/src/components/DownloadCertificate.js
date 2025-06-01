import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const DownloadCertificate = () => {
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchApprovedRequests = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/certificates/certificate-requests/?status=approved`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setRequests(response.data);
    } catch (err) {
      if (err.response?.status === 401) {
        try {
          const refreshResponse = await axios.post(
            `${process.env.REACT_APP_API_URL}/auth/refresh/`,
            { refresh: localStorage.getItem('refresh') }
          );
          localStorage.setItem('token', refreshResponse.data.access);
          fetchApprovedRequests(); // Retry
        } catch (refreshErr) {
          setError('Session expired. Please log in again.');
          navigate('/login');
        }
      } else {
        setError(err.response?.data?.detail || 'Failed to fetch certificates');
      }
    }
  };

  const handleDownload = async (id) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/certificates/certificates/${id}/`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const certPem = response.data.cert_pem;
      const blob = new Blob([certPem], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `certificate_${id}.pem`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to download certificate');
    }
  };

  useEffect(() => {
    fetchApprovedRequests();
  }, []);

  return (
    <div className="card p-4">
      <h2>Download Certificates</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Common Name</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {requests.map(req => (
            <tr key={req.id}>
              <td>{req.id}</td>
              <td>{req.csr_pem.match(/CN=([^\/]+)/)?.[1] || 'N/A'}</td>
              <td>{req.status}</td>
              <td>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => handleDownload(req.id)}
                >
                  Download
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DownloadCertificate;