/**
 * Unit tests for AuthContext.
 *
 * Sprint 10 — JWT em httpOnly cookie. AuthContext ja nao usa localStorage;
 * bootstrap via /auth/me que devolve user se cookie valido OR 401.
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
    jest.clearAllMocks();
  });

  test('starts unauthenticated when /auth/me rejects (no cookie)', async () => {
    authAPI.getMe.mockRejectedValueOnce(new Error('401'));
    render(
      <AuthProvider>
        <Probe onState={() => {}} />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));
    expect(screen.getByTestId('auth')).toHaveTextContent('no');
    expect(authAPI.getMe).toHaveBeenCalledTimes(1);
  });

  test('hydrates from /auth/me when cookie is valid', async () => {
    const user = { id: 'u1', name: 'Test', role: 'admin', status: 'ativo' };
    authAPI.getMe.mockResolvedValueOnce({ data: user });

    render(
      <AuthProvider>
        <Probe onState={() => {}} />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));
    expect(screen.getByTestId('auth')).toHaveTextContent('yes');
    expect(screen.getByTestId('role')).toHaveTextContent('admin');
    expect(authAPI.getMe).toHaveBeenCalledTimes(1);
  });

  test('login() updates state from response.data.user (cookie set server-side)', async () => {
    authAPI.getMe.mockRejectedValueOnce(new Error('401'));
    authAPI.login.mockResolvedValueOnce({
      data: {
        access_token: 'still-in-body',
        user: { id: 'u2', name: 'Socio', role: 'socio', status: 'ativo' },
      },
    });

    let captured;
    render(
      <AuthProvider>
        <Probe onState={(s) => { captured = s; }} />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('ready'));
    await act(async () => {
      await captured.login({ email: 's@x.com', password: 'pw' });
    });

    expect(screen.getByTestId('auth')).toHaveTextContent('yes');
    expect(screen.getByTestId('role')).toHaveTextContent('socio');
  });

  test('logout() chama authAPI.logout() (server-side cookie clear) + clears state', async () => {
    authAPI.getMe.mockResolvedValueOnce({ data: { id: 'u1', role: 'admin', status: 'ativo' } });
    authAPI.logout.mockResolvedValueOnce({ data: { message: 'Sessão encerrada' } });

    let captured;
    render(
      <AuthProvider>
        <Probe onState={(s) => { captured = s; }} />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('yes'));
    await act(async () => { await captured.logout(); });

    expect(authAPI.logout).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('auth')).toHaveTextContent('no');
  });

  test('logout() faz fallback gracioso se /auth/logout falhar', async () => {
    authAPI.getMe.mockResolvedValueOnce({ data: { id: 'u1', role: 'admin', status: 'ativo' } });
    authAPI.logout.mockRejectedValueOnce(new Error('Network error'));

    let captured;
    render(
      <AuthProvider>
        <Probe onState={(s) => { captured = s; }} />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('yes'));
    await act(async () => { await captured.logout(); });

    expect(authAPI.logout).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('auth')).toHaveTextContent('no');
  });

  test('responds to accta:force-logout event by clearing state', async () => {
    authAPI.getMe.mockResolvedValueOnce({ data: { id: 'u1', role: 'admin', status: 'ativo' } });

    render(
      <AuthProvider>
        <Probe onState={() => {}} />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('yes'));
    act(() => {
      window.dispatchEvent(new Event('accta:force-logout'));
    });
    await waitFor(() => expect(screen.getByTestId('auth')).toHaveTextContent('no'));
  });

  test('role flags reflect user role', async () => {
    authAPI.getMe.mockResolvedValueOnce({ data: { id: 'u1', role: 'financeiro', status: 'ativo' } });

    let captured;
    render(
      <AuthProvider>
        <Probe onState={(s) => { captured = s; }} />
      </AuthProvider>,
    );

    await waitFor(() => expect(captured?.isFinanceiro).toBe(true));
    expect(captured.isAdmin).toBe(false);
    expect(captured.isModerador).toBe(false);
    expect(captured.isAtivo).toBe(true);
  });

  test('useAuth throws when used outside AuthProvider', () => {
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<Probe onState={() => {}} />)).toThrow(
      'useAuth must be used within AuthProvider',
    );
    spy.mockRestore();
  });
});
