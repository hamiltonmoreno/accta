import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

jest.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}), { virtual: true });
jest.mock('../../../contexts/AuthContext', () => ({ useAuth: jest.fn() }));
jest.mock('../../../components/NotificationBell', () => ({
  NotificationBell: () => <div data-testid="notif-bell" />,
}));
jest.mock('../../../components/BrandLogo', () => ({
  BrandLogo: () => <div data-testid="brand-logo" />,
}));
jest.mock('../UserMenu', () => ({
  UserMenu: ({ isMember, isAdmin }) => (
    <div data-testid="user-menu" data-member={String(isMember)} data-admin={String(isAdmin)} />
  ),
}));

const { useAuth } = require('../../../contexts/AuthContext');
const { Header } = require('../Header');

beforeEach(() => jest.clearAllMocks());

test('mostra logo, sino, atalhos e o menu de utilizador (sem título de página)', () => {
  useAuth.mockReturnValue({ user: { name: 'X', role: 'socio', account_type: 'member' }, isAdmin: false });
  render(<Header onOpenMobileMenu={() => {}} onLogout={() => {}} />);
  expect(screen.getByTestId('brand-logo')).toBeInTheDocument();
  expect(screen.getByTestId('notif-bell')).toBeInTheDocument();
  expect(screen.getByTestId('user-menu')).toBeInTheDocument();
  // Meu Perfil e Ranking vivem dentro do dropdown do avatar (sem ícones soltos).
  expect(screen.queryByTestId('header-perfil')).toBeNull();
  expect(screen.queryByTestId('header-ranking')).toBeNull();
  // Mural continua como atalho de ícone para membros.
  expect(screen.getByTestId('header-mural')).toHaveAttribute('href', '/mural');
});

test('Mural (atalho do cabeçalho) aparece para membro e para admin (mesmo técnico), e some para técnico não-admin', () => {
  // membro sócio
  useAuth.mockReturnValue({ user: { name: 'X', role: 'socio', account_type: 'member' }, isAdmin: false });
  const { rerender } = render(<Header onOpenMobileMenu={() => {}} onLogout={() => {}} />);
  expect(screen.getByTestId('header-mural')).toBeInTheDocument();
  // Ranking nunca é ícone solto no cabeçalho (vive no dropdown do avatar).
  expect(screen.queryByTestId('header-ranking')).toBeNull();

  // conta técnica MAS admin → aparece (resolve o caso da conta de teste)
  useAuth.mockReturnValue({ user: { name: 'Sys', role: 'admin', account_type: 'technical' }, isAdmin: true });
  rerender(<Header onOpenMobileMenu={() => {}} onLogout={() => {}} />);
  expect(screen.getByTestId('header-mural')).toBeInTheDocument();

  // conta técnica não-admin → some
  useAuth.mockReturnValue({ user: { name: 'Bot', role: 'moderador', account_type: 'technical' }, isAdmin: false });
  rerender(<Header onOpenMobileMenu={() => {}} onLogout={() => {}} />);
  expect(screen.queryByTestId('header-mural')).toBeNull();
  // O acesso ao perfil é sempre via dropdown do avatar (user-menu).
  expect(screen.getByTestId('user-menu')).toBeInTheDocument();
});

test('hambúrguer chama onOpenMobileMenu', () => {
  useAuth.mockReturnValue({ user: { name: 'X', role: 'socio' }, isAdmin: false });
  const onOpen = jest.fn();
  render(<Header onOpenMobileMenu={onOpen} onLogout={() => {}} />);
  fireEvent.click(screen.getByTestId('mobile-sidebar-button'));
  expect(onOpen).toHaveBeenCalledTimes(1);
});
