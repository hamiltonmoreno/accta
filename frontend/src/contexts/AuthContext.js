import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
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

  const login = useCallback(async (credentials) => {
    const response = await authAPI.login(credentials);
    const { access_token, user: userData } = response.data;

    localStorage.setItem('accta_token', access_token);
    localStorage.setItem('accta_user', JSON.stringify(userData));
    setUser(userData);

    return userData;
  }, []);

  const logout = useCallback(() => {
    clearAuth();
  }, [clearAuth]);

  const refreshUser = useCallback(async () => {
    try {
      const res = await authAPI.getMe();
      setUser(res.data);
      localStorage.setItem('accta_user', JSON.stringify(res.data));
    } catch {
      // ignore
    }
  }, []);

  const value = useMemo(() => ({
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin',
    isFinanceiro: user?.role === 'financeiro',
    isModerador: user?.role === 'moderador',
    isAtivo: user?.status === 'ativo',
    refreshUser,
  }), [user, loading, login, logout, refreshUser]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
