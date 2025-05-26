import React, { useState } from 'react';
import CSRForm from './components/CSRForm';
import LoginForm from './components/LoginForm';
import './styles.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('token'));

  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  return (
    <div className="container mt-5">
      <h1>PKI Certificate Request</h1>
      {isLoggedIn ? <CSRForm /> : <LoginForm onLogin={handleLogin} />}
    </div>
  );
}

export default App;