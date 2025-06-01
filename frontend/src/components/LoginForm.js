import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      // Запрос на логин
      const loginResponse = await axios.post(
        `${process.env.REACT_APP_API_URL}/auth/login/`,
        { email, password }
      );
      const { access, refresh } = loginResponse.data;
      localStorage.setItem('token', access);
      localStorage.setItem('refresh', refresh);

      // Запрос информации о пользователе
      const userResponse = await axios.get(
        `${process.env.REACT_APP_API_URL}/auth/users/about_me/`,
        {
          headers: { Authorization: `Bearer ${access}` },
        }
      );

      console.log('User data:', userResponse.data);
      console.log('is_admin:', userResponse.data.is_admin);

      if (userResponse.data.is_admin) {
        console.log('Navigating to /admin/requests as admin');
        navigate('/admin/requests', { replace: true });
      } else {
        console.log('Navigating to /csr as non-admin');
        navigate('/csr', { replace: true });
      }
    } catch (err) {
      console.error('Login error:', err.response || err.message);
      setError(err.response?.data?.detail || 'Ошибка входа. Проверьте логин и пароль.');
    }
  };

  return (
    <div className="card p-4">
      <h2>Вход</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="email" className="form-label">Имя пользователя</label>
          <input
            type="text"
            className="form-control"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="mb-3">
          <label htmlFor="password" className="form-label">Пароль</label>
          <input
            type="password"
            className="form-control"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary">Войти</button>
      </form>
    </div>
  );
};

export default LoginForm;