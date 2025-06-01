import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import CSRForm from './components/CSRForm';
import LoginForm from './components/LoginForm';
import RequestList from './components/RequestList';
import MyRequests from './components/MyRequests';
import SignFile from './components/SignFile';
import DownloadCertificate from './components/DownloadCertificate';
import NavMenu from './components/NavMenu';
import AdminCertificates from './components/AdminCertificates';
import './styles.css';

const ProtectedRoute = ({ children, adminOnly }) => {
  const [isAdmin, setIsAdmin] = useState(null);
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!adminOnly || !token) {
      setIsAdmin(false);
      return;
    }

    const checkAdmin = async () => {
      try {
        const response = await axios.get(`${process.env.REACT_APP_API_URL}/auth/user/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setIsAdmin(response.data.is_staff || false);
      } catch (err) {
        console.error('Admin check failed:', err);
        setIsAdmin(false);
      }
    };

    checkAdmin();
  }, [adminOnly, token]);

  if (!token) {
    return <Navigate to="/login" />;
  }

  if (adminOnly && isAdmin === null) {
    return null; // Пока проверяется статус админа
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/csr" />;
  }

  return children;
};

function App() {
  return (
    <Router>
      <div className="container mt-5">
        <NavMenu />
        <Routes>
          <Route
            path="/admin/certificates"
            element={
              <ProtectedRoute adminOnly>
                <AdminCertificates />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/requests"
            element={
              <ProtectedRoute adminOnly>
                <RequestList />
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<LoginForm />} />
          <Route
            path="/csr"
            element={
              <ProtectedRoute>
                <CSRForm />
              </ProtectedRoute>
            }
          />
          <Route
            path="/my-requests"
            element={
              <ProtectedRoute>
                <MyRequests />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sign-file"
            element={
              <ProtectedRoute>
                <SignFile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/download-certificate"
            element={
              <ProtectedRoute>
                <DownloadCertificate />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;