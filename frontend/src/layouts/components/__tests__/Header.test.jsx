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
  UserMenu: ({ isMember }) => <div data-testid="user-menu" data-member={String(isMember)} />,
}));

const { useAuth } = require('../../../contexts/AuthContext');
const { Header } = require('../Header');

beforeEach(() => jest.clearAllMocks());

test('mostra logo, título, sino e o menu de utilizador', () => {
  useAuth.mockReturnValue({ user: { name: 'X', role: 'socio', account_type: 'member' } });
  render(<Header title="Dashboard" onOpenMobileMenu={() => {}} onLogout={() => {}} />);
  expect(screen.getByTestId('brand-logo')).toBeInTheDocument();
  expect(screen.getByText('Dashboard')).toBeInTheDocument();
  expect(screen.getByTestId('notif-bell')).toBeInTheDocument();
  expect(screen.getByTestId('user-menu')).toBeInTheDocument();
});

test('ícone de Ranking (desktop) aparece para sócio e some para conta técnica', () => {
  useAuth.mockReturnValue({ user: { name: 'X', role: 'socio', account_type: 'member' } });
  const { rerender } = render(<Header title="T" onOpenMobileMenu={() => {}} onLogout={() => {}} />);
  expect(screen.getByTestId('header-ranking')).toHaveAttribute('href', '/ranking');

  useAuth.mockReturnValue({ user: { name: 'Sys', role: 'admin', account_type: 'technical' } });
  rerender(<Header title="T" onOpenMobileMenu={() => {}} onLogout={() => {}} />);
  expect(screen.queryByTestId('header-ranking')).toBeNull();
});

test('hambúrguer chama onOpenMobileMenu', () => {
  useAuth.mockReturnValue({ user: { name: 'X', role: 'socio' } });
  const onOpen = jest.fn();
  render(<Header title="T" onOpenMobileMenu={onOpen} onLogout={() => {}} />);
  fireEvent.click(screen.getByTestId('mobile-sidebar-button'));
  expect(onOpen).toHaveBeenCalledTimes(1);
});
