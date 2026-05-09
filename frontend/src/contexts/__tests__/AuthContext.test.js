/**
 * Unit tests for AuthContext.
 *
 * Mocks utils/api so the provider's session-validation effect resolves
 * deterministically without a real backend.
 */
import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';

// Mock the api module BEFORE importing anything that loads it.
jest.mock('../../utils/api', () => ({
  __esModule: true,
  authAPI: {
    login: jest.fn(),
    logout: jest.fn(),
    getMe: jest.fn(),
  },
  default: {},
}));

const { AuthProvider, useAuth } = require('../AuthContext');
const { authAPI } = require('../../utils/api');

const Probe = ({ onState }) => {
  const auth = useAuth();
  React.useEffect(() => {
    onState(auth);
  }, [auth, onState]);
  return (
    <div>
      <span data-testid="auth">{auth.isAuthenticated ? 'yes' : 'no'}</span>
      <span data-testid="role">{auth.user?.role || 'none'}</span>
      <span data-testid="loading">{auth.loading ? 'loading' : 'ready'}</span>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  test('starts unauthenticated when no token stored', async () => {
    render(
      <AuthProvider>
        <Probe onState={() => {}} />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));
    expect(screen.getByTestId('auth')).toHaveTextContent('no');
    expect(authAPI.getMe).not.toHaveBeenCalled();
  });

  test('hydrates from localStorage and re-validates with server', async () => {
    const stored = { id: 'u1', name: 'Test', role: 'admin', status: 'ativo' };
    localStorage.setItem('accta_token', 'token-abc');
    localStorage.setItem('accta_user', JSON.stringify(stored));
    authAPI.getMe.mockResolvedValueOnce({ data: stored });

    render(
      <AuthProvider>
        <Probe onState={() => {}} />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));
    expect(screen.getByTestId('auth')).toHaveTextContent('yes');
    expect(screen.getByTestId('role')).toHaveTextContent('admin');
    expect(authAPI.getMe).toHaveBeenCalledTimes(1);
  });

  test('clears session when stored user JSON is corrupt', async () => {
    localStorage.setItem('accta_token', 'token-abc');
    localStorage.setItem('accta_user', 'not-json');

    render(
      <AuthProvider>
        <Probe onState={() => {}} />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));
    expect(localStorage.getItem('accta_token')).toBeNull();
    expect(localStorage.getItem('accta_user')).toBeNull();
    expect(screen.getByTestId('auth')).toHaveTextContent('no');
  });

  test('clears session when getMe rejects (token expired)', async () => {
    localStorage.setItem('accta_token', 'expired');
    localStorage.setItem('accta_user', JSON.stringify({ id: 'u1', role: 'socio' }));
    authAPI.getMe.mockRejectedValueOnce(new Error('401'));

    render(
      <AuthProvider>
        <Probe onState={() => {}} />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));
    expect(localStorage.getItem('accta_token')).toBeNull();
    expect(screen.getByTestId('auth')).toHaveTextContent('no');
  });

  test('login() persists token+user and updates state', async () => {
    authAPI.login.mockResolvedValueOnce({
      data: {
        access_token: 'new-token',
        user: { id: 'u2', name: 'Socio', role: 'socio', status: 'ativo' },
      },
    });

    let captured;
    render(
      <AuthProvider>
        <Probe onState={(s) => { captured = s; }} />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));
    await act(async () => {
      await captured.login({ email: 's@x.com', password: 'pw' });
    });

    expect(localStorage.getItem('accta_token')).toBe('new-token');
    expect(JSON.parse(localStorage.getItem('accta_user'))).toMatchObject({ role: 'socio' });
    expect(screen.getByTestId('auth')).toHaveTextContent('yes');
  });

  test('logout() chama authAPI.logout() (revoga server-side) e limpa storage', async () => {
    localStorage.setItem('accta_token', 'tok');
    localStorage.setItem('accta_user', JSON.stringify({ id: 'u1', role: 'admin', status: 'ativo' }));
    authAPI.getMe.mockResolvedValueOnce({ data: { id: 'u1', role: 'admin', status: 'ativo' } });
    authAPI.logout.mockResolvedValueOnce({ data: { message: 'Sessão encerrada' } });

    let captured;
    render(
      <AuthProvider>
        <Probe onState={(s) => { captured = s; }} />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('yes'));
    await act(async () => { await captured.logout(); });

    expect(authAPI.logout).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('accta_token')).toBeNull();
    expect(screen.getByTestId('auth')).toHaveTextContent('no');
  });

  test('logout() faz fallback gracioso se /auth/logout falhar (404, network, 401)', async () => {
    // Backend antigo sem endpoint /auth/logout, ou token ja invalido.
    // O frontend deve continuar a fazer logout local.
    localStorage.setItem('accta_token', 'tok');
    localStorage.setItem('accta_user', JSON.stringify({ id: 'u1', role: 'admin', status: 'ativo' }));
    authAPI.getMe.mockResolvedValueOnce({ data: { id: 'u1', role: 'admin', status: 'ativo' } });
    authAPI.logout.mockRejectedValueOnce(new Error('Network error'));

    let captured;
    render(
      <AuthProvider>
        <Probe onState={(s) => { captured = s; }} />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('yes'));
    await act(async () => { await captured.logout(); });

    expect(authAPI.logout).toHaveBeenCalledTimes(1);
    // Apesar do reject, localStorage tem que ser limpo.
    expect(localStorage.getItem('accta_token')).toBeNull();
    expect(screen.getByTestId('auth')).toHaveTextContent('no');
  });

  test('responds to accta:force-logout event by clearing state', async () => {
    localStorage.setItem('accta_token', 'tok');
    localStorage.setItem('accta_user', JSON.stringify({ id: 'u1', role: 'admin', status: 'ativo' }));
    authAPI.getMe.mockResolvedValueOnce({ data: { id: 'u1', role: 'admin', status: 'ativo' } });

    render(
      <AuthProvider>
        <Probe onState={() => {}} />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('yes'));
    act(() => {
      window.dispatchEvent(new Event('accta:force-logout'));
    });
    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('no'));
    expect(localStorage.getItem('accta_token')).toBeNull();
  });

  test('role flags reflect user role', async () => {
    localStorage.setItem('accta_token', 'tok');
    localStorage.setItem('accta_user', JSON.stringify({ id: 'u1', role: 'financeiro', status: 'ativo' }));
    authAPI.getMe.mockResolvedValueOnce({ data: { id: 'u1', role: 'financeiro', status: 'ativo' } });

    let captured;
    render(
      <AuthProvider>
        <Probe onState={(s) => { captured = s; }} />
      </AuthProvider>
    );

    await waitFor(() => expect(captured?.isFinanceiro).toBe(true));
    expect(captured.isAdmin).toBe(false);
    expect(captured.isModerador).toBe(false);
    expect(captured.isAtivo).toBe(true);
  });

  test('useAuth throws when used outside AuthProvider', () => {
    // Suppress expected console.error from React boundary.
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<Probe onState={() => {}} />)).toThrow(
      'useAuth must be used within AuthProvider'
    );
    spy.mockRestore();
  });
});
