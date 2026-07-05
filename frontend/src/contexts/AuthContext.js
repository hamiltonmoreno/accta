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

  const value = useMemo(() => {
    // RBAC granular aditivo (spec-identidade-cargos): privilégios concedem
    // acesso EXTRA além do role. Espelha auth.can_view/manage_finances do backend.
    const privileges = user?.privileges || [];
    const isAdmin = user?.role === 'admin';
    // spec 018: os privilégios são a única fonte granular — o nível
    // financeiro/moderador deixou de existir (viraram funções personalizadas).
    const canManageFinances = isAdmin || privileges.includes('manage_finances');
    const canViewFinances = canManageFinances || privileges.includes('view_finances_readonly');

    // Governança (spec-governanca §15): órgão derivado da KEY canónica do cargo.
    const cargo = user?.cargo || '';
    const isMesaAG = cargo.startsWith('ag_');
    const isDirecao = cargo.startsWith('dir_');
    const isConselhoFiscal = cargo.startsWith('cf_');
    const isTesoureiro = cargo === 'dir_tesoureiro';
    const isPresidente = cargo === 'dir_presidente';

    // Eleitor: sócio real, activo, categoria votante, sem direitos suspensos.
    const suspendedUntil = user?.rights_suspended_until;
    const suspended = !!suspendedUntil && new Date(suspendedUntil) > new Date();
    const accountType = user?.account_type || 'member';
    const category = user?.member_category || 'ordinario';
    const isVotingMember =
      accountType === 'member' &&
      user?.status === 'ativo' &&
      (category === 'fundador' || category === 'ordinario') &&
      !suspended;

    // can(privilege): RBAC aditivo — admin OU detentor do privilégio.
    const can = (p) => isAdmin || privileges.includes(p);

    return {
      user,
      loading,
      login,
      logout,
      isAuthenticated: !!user,
      isAdmin,
      // Compat spec 018: flags derivadas de PRIVILÉGIOS (o role legado já não
      // existe) — consumidores antigos (isAdmin || isFinanceiro) continuam certos.
      isFinanceiro: privileges.includes('manage_finances'),
      isModerador: privileges.includes('moderate_content'),
      isAtivo: user?.status === 'ativo',
      hasPrivilege: (p) => privileges.includes(p),
      can,
      canViewFinances,
      canManageFinances,
      isMesaAG,
      isDirecao,
      isConselhoFiscal,
      isTesoureiro,
      isPresidente,
      isVotingMember,
      refreshUser,
    };
  }, [user, loading, login, logout, refreshUser]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
