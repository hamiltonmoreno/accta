import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../utils/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('accta_token');
    const storedUser = localStorage.getItem('accta_user');
    
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('accta_token');
        localStorage.removeItem('accta_user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (credentials) => {
    const response = await authAPI.login(credentials);
    const { access_token, user: userData } = response.data;
    
    localStorage.setItem('accta_token', access_token);
    localStorage.setItem('accta_user', JSON.stringify(userData));
    setUser(userData);
    
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('accta_token');
    localStorage.removeItem('accta_user');
    setUser(null);
  };

  const register = async (data) => {
    const response = await authAPI.register(data);
    return response.data;
  };

  const isAuthenticated = !!user;
  const isAdmin = user?.role === 'admin';
  const isFinanceiro = user?.role === 'financeiro';
  const isModerador = user?.role === 'moderador';
  const isAtivo = user?.status === 'ativo';

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        register,
        isAuthenticated,
        isAdmin,
        isFinanceiro,
        isModerador,
        isAtivo,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
