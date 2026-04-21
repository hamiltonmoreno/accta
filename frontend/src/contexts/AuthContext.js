import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
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

  const clearAuth = useCallback(() => {
    localStorage.removeItem('accta_token');
    localStorage.removeItem('accta_user');
    setUser(null);
  }, []);

  useEffect(() => {
    const validateSession = async () => {
      const token = localStorage.getItem('accta_token');
      const storedUser = localStorage.getItem('accta_user');

      if (!token || !storedUser) {
        setLoading(false);
        return;
      }

      // Quick parse to show UI immediately
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        clearAuth();
        setLoading(false);
        return;
      }

      // Validate token with server in background
      try {
        const res = await authAPI.getMe();
        setUser(res.data);
        localStorage.setItem('accta_user', JSON.stringify(res.data));
      } catch {
        // Token expired or invalid — clear session
        clearAuth();
      }

      setLoading(false);
    };

    validateSession();
  }, [clearAuth]);

  // Listen for forced logout events (from 401 interceptor)
  useEffect(() => {
    const handleForceLogout = () => clearAuth();
    window.addEventListener('accta:force-logout', handleForceLogout);
    return () => window.removeEventListener('accta:force-logout', handleForceLogout);
  }, [clearAuth]);

  const login = async (credentials) => {
    const response = await authAPI.login(credentials);
    const { access_token, user: userData } = response.data;

    localStorage.setItem('accta_token', access_token);
    localStorage.setItem('accta_user', JSON.stringify(userData));
    setUser(userData);

    return userData;
  };

  const logout = () => {
    clearAuth();
  };

  const isAuthenticated = !!user;
  const isAdmin = user?.role === 'admin';
  const isFinanceiro = user?.role === 'financeiro';
  const isModerador = user?.role === 'moderador';
  const isAtivo = user?.status === 'ativo';

  const refreshUser = async () => {
    try {
      const res = await authAPI.getMe();
      setUser(res.data);
      localStorage.setItem('accta_user', JSON.stringify(res.data));
    } catch {
      // ignore
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAuthenticated,
        isAdmin,
        isFinanceiro,
        isModerador,
        isAtivo,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
