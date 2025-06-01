import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const MyRequests = () => {
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const navigate = useNavigate();

  const fetchRequests = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      const url = `${process.env.REACT_APP_API_URL}/certificates/certificate-requests/${
        statusFilter ? `?status=${statusFilter}` : ''
      }`;
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRequests(response.data);
    } catch (err) {
      if (err.response?.status === 401) {
        try {
          const refreshResponse = await axios.post(
            `${process.env.REACT_APP_API_URL}/auth/refresh/`,
            { refresh: localStorage.getItem('refresh') }
          );
          localStorage.setItem('token', refreshResponse.data.access);
          fetchRequests(); // Retry
        } catch (refreshErr) {
          setError('Session expired. Please log in again.');
          navigate('/login');
        }
      } else {
        setError(err.response?.data?.detail || 'Failed to fetch requests');
      }
    }
  };

  const handleCertificateAction = async (requestId) => {
    try {
      const token = localStorage.getItem('token');
      console.log('Token:', token); // Отладка токена
      if (!token) {
        setError('Please log in to proceed.');
        navigate('/login');
        return;
      }

      // Find the request to get its csr_pem and status
      const request = requests.find(req => req.id === requestId);
      if (!request || !request.csr_pem) {
        setError('Request or CSR not found.');
        return;
      }

      let certPem;
      let certId;
      let message = 'Certificate downloaded successfully!';

      // If request is signed, fetch existing certificate
      if (request.status === 'signed') {
        console.log('Fetching certificate for requestId:', requestId);
        const signResponse = await axios.get(
          `${process.env.REACT_APP_API_URL}/certificates/certificates/${requestId}/get_by_scr/`,
          {
            headers: { Authorization: `Bearer ${token}` },
            params: { csr_id: requestId } // Query-параметр
          }
        );
        if (!signResponse.data.id || !signResponse.data.cert_pem) {
          throw new Error('Invalid certificate data in response');
        }
        if (signResponse.data.revoked) {
          setError('Certificate has been revoked and cannot be downloaded.');
          return;
        }
        certId = signResponse.data.id;
        certPem = signResponse.data.cert_pem;
        message = 'Existing certificate downloaded successfully!';
      } else if (request.status === 'approved') {
        // Create new certificate
        console.log('Creating certificate for requestId:', requestId);
        const signResponse = await axios.post(
          `${process.env.REACT_APP_API_URL}/certificates/certificate-requests/${requestId}/sign/`,
          { csr_pem: request.csr_pem },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (signResponse.data.detail === 'Certificate already exists.') {
          certId = signResponse.data.cert_id;
          message = 'Existing certificate downloaded successfully!';
        } else if (!signResponse.data.cert_id) {
          throw new Error('Certificate ID not found in response');
        } else {
          certId = signResponse.data.cert_id;
          message = 'Certificate created and downloaded successfully!';
        }

        // Fetch the certificate content
        console.log('Fetching certificate content for certId:', certId);
        const certResponse = await axios.get(
          `${process.env.REACT_APP_API_URL}/certificates/certificates/${certId}/`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (!certResponse.data.cert_pem) {
          throw new Error('Certificate PEM not found in response');
        }
        if (certResponse.data.revoked) {
          setError('Certificate has been revoked and cannot be downloaded.');
          return;
        }
        certPem = certResponse.data.cert_pem;
      } else {
        setError('Certificate can only be created for approved requests.');
        return;
      }

      // Download certificate as .pem file
      const blob = new Blob([certPem], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `certificate_${certId}.pem`;
      a.click();
      window.URL.revokeObjectURL(url);

      // Update request status to 'signed' if it was 'approved'
      if (request.status === 'approved') {
        setRequests(requests.map(req =>
          req.id === requestId ? { ...req, status: 'signed' } : req
        ));
      }

      alert(message);
    } catch (err) {
      console.error('Error:', err.response || err.message); // Детальная отладка
      if (err.response?.status === 401) {
        try {
          const refreshResponse = await axios.post(
            `${process.env.REACT_APP_API_URL}/auth/refresh/`,
            { refresh: localStorage.getItem('refresh') }
          );
          localStorage.setItem('token', refreshResponse.data.access);
          handleCertificateAction(requestId); // Retry
        } catch (refreshErr) {
          console.error('Refresh Error:', refreshErr.response || refreshErr.message);
          setError('Session expired. Please log in again.');
          navigate('/login');
        }
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to process certificate');
      }
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [statusFilter]);

  return (
    <div className="card p-4">
      <h2>My Certificate Requests</h2>
      <div className="mb-3">
        <label htmlFor="statusFilter" className="form-label">Filter by Status</label>
        <select
          id="statusFilter"
          className="form-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="signed">Signed</option>
        </select>
      </div>
      {error && <div className="alert alert-danger">{error}</div>}
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Common Name</th>
            <th>Status</th>
            <th>Created At</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {requests.map(req => (
            <tr key={req.id}>
              <td>{req.id}</td>
              <td>{req.csr_pem.match(/CN=([^\/]+)/)?.[1] || 'N/A'}</td>
              <td>{req.status}</td>
              <td>{new Date(req.created_at).toLocaleString()}</td>
              <td>
                {req.status === 'approved' && (
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => handleCertificateAction(req.id)}
                  >
                    Create Certificate
                  </button>
                )}
                {req.status === 'signed' && (
                  <button
                    className="btn btn-success btn-sm"
                    onClick={() => handleCertificateAction(req.id)}
                  >
                    Download Certificate
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

export default MyRequests;