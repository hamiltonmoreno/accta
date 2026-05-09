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

// Sprint 10 — JWT em httpOnly cookie. JS no browser nao consegue ler/escrever
// o cookie (XSS-safe). Bootstrap: chamar /auth/me ao montar; se 200, ha
// sessao valida e devolve o user. Se 401, sem sessao.
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const clearAuth = useCallback(() => {
    setUser(null);
  }, []);

  useEffect(() => {
    const validateSession = async () => {
      try {
        const res = await authAPI.getMe();
        setUser(res.data);
      } catch {
        // 401 / network — sem sessao valida, fica anonymous.
      } finally {
        setLoading(false);
      }
    };
    validateSession();
  }, []);

  // Listen for forced logout events (from 401 interceptor)
  useEffect(() => {
    const handleForceLogout = () => clearAuth();
    window.addEventListener('accta:force-logout', handleForceLogout);
    return () => window.removeEventListener('accta:force-logout', handleForceLogout);
  }, [clearAuth]);

  const login = useCallback(async (credentials) => {
    // Backend define o cookie httpOnly via Set-Cookie no response. JS nao
    // ve o cookie — apenas o user object devolvido no body.
    const response = await authAPI.login(credentials);
    const { user: userData } = response.data;
    setUser(userData);
    return userData;
  }, []);

  const logout = useCallback(async () => {
    // /auth/logout adiciona JTI ao blocklist + limpa cookie via Set-Cookie.
    // Se falhar (network/401), fazemos clear local na mesma — UI nao deve
    // ficar presa.
    try {
      await authAPI.logout();
    } catch {
      // ignore
    }
    clearAuth();
  }, [clearAuth]);

  const refreshUser = useCallback(async () => {
    try {
      const res = await authAPI.getMe();
      setUser(res.data);
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
