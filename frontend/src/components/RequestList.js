import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const RequestList = () => {
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchRequests = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }
      const response = await axios.get(
        `${process.env.REACT_APP_API_URL}/certificates/certificate-requests/`,
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

  const handleAction = async (id, action) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/certificates/certificate-requests/${id}/${action}/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setRequests(requests.map(req =>
        req.id === id ? { ...req, status: action === 'approve' ? 'approved' : 'rejected' } : req
      ));
      alert(response.data.detail);
    } catch (err) {
      if (err.response?.status === 401) {
        try {
          const refreshResponse = await axios.post(
            `${process.env.REACT_APP_API_URL}/auth/refresh/`,
            { refresh: localStorage.getItem('refresh') }
          );
          localStorage.setItem('token', refreshResponse.data.access);
          handleAction(id, action); // Retry
        } catch (refreshErr) {
          setError('Session expired. Please log in again.');
          navigate('/login');
        }
      } else {
        setError(err.response?.data?.detail || `Failed to ${action} request`);
      }
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  return (
    <div className="card p-4">
      <h2>Certificate Requests</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>User</th>
            <th>Common Name</th>
            <th>Status</th>
            <th>Created At</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {requests.map(req => (
            <tr key={req.id}>
              <td>{req.id}</td>
              <td>{req.user_email}</td>
              <td>{req.csr_pem.match(/CN=([^\/]+)/)?.[1] || 'N/A'}</td>
              <td>{req.status}</td>
              <td>{new Date(req.created_at).toLocaleString()}</td>
              <td>
                {req.status === 'pending' && (
                  <>
                    <button
                      className="btn btn-success btn-sm me-2"
                      onClick={() => handleAction(req.id, 'approve')}
                    >
                      Approve
                    </button>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleAction(req.id, 'reject')}
                    >
                      Reject
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default RequestList;