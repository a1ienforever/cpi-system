import React, { useState, useEffect } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import axios from 'axios';

const NavMenu = () => {
  const navigate = useNavigate();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await axios.get(
          `${process.env.REACT_APP_API_URL}/api/auth/user/`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        setIsAdmin(response.data.is_admin || false); // Используем is_admin, как в LoginForm
      } catch (err) {
        console.error('Не удалось получить информацию о пользователе:', err);
      }
    };

    fetchUserInfo();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    navigate('/login');
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-light mb-4">
      <div className="container-fluid">
        <span className="navbar-brand">PKI System</span>
        <div className="collapse navbar-collapse">
          <ul className="navbar-nav me-auto mb-2 mb-lg-0">
            {isAdmin ? (
              <li className="nav-item">
                <NavLink className="nav-link" activeClassName="active" to="/admin/requests">
                  Список запросов
                </NavLink>
              </li>
            ) : (
              <li className="nav-item">
                <NavLink className="nav-link" activeClassName="active" to="/my-requests">
                  Мои запросы
                </NavLink>
              </li>
            )}
            <li className="nav-item">
              <NavLink className="nav-link" activeClassName="active" to="/sign-file">
                Подписать файл
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink className="nav-link" activeClassName="active" to="/csr">
                Отправить запрос
              </NavLink>
            </li>
            <li className="nav-item">
              <NavLink className="nav-link" activeClassName="active" to="/download-certificate">
                Скачать сертификат
              </NavLink>
            </li>
            {isAdmin && (
              <li className="nav-item">
                <NavLink className="nav-link" activeClassName="active" to="/admin/certificates">
                  Сертификаты (админ)
                </NavLink>
              </li>
            )}
          </ul>
          <button className="btn btn-outline-danger" onClick={handleLogout}>
            Выйти
          </button>
        </div>
      </div>
    </nav>
  );
};

export default NavMenu;