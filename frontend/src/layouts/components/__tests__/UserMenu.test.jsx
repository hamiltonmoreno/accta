// frontend/src/layouts/components/__tests__/UserMenu.test.jsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';

jest.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}), { virtual: true });

// Passthrough do dropdown — torna o conteúdo sempre visível no teste.
jest.mock('../../../components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }) => <div>{children}</div>,
  DropdownMenuItem: ({ children, onClick, asChild, ...props }) => (
    <div onClick={onClick} {...props}>{children}</div>
  ),
  DropdownMenuLabel: ({ children }) => <div>{children}</div>,
  DropdownMenuSeparator: () => <hr />,
}));
jest.mock('../../../components/UserAvatar', () => ({
  UserAvatar: () => <span data-testid="avatar" />,
}));

const { UserMenu } = require('../UserMenu');

const baseUser = { name: 'Hamilton V.', email: 'h@accta.cv', status: 'ativo' };

test('mostra nome, email e Meu Perfil sempre', () => {
  render(<UserMenu user={baseUser} isSocio={false} isMember={true} onLogout={() => {}} />);
  expect(screen.getByText('Hamilton V.')).toBeInTheDocument();
  expect(screen.getByText('h@accta.cv')).toBeInTheDocument();
  expect(screen.getByTestId('menu-perfil')).toHaveAttribute('href', '/perfil');
});

test('Carteira só aparece para sócios', () => {
  const { rerender } = render(<UserMenu user={baseUser} isSocio={false} isMember={true} onLogout={() => {}} />);
  expect(screen.queryByTestId('menu-carteira')).toBeNull();
  rerender(<UserMenu user={baseUser} isSocio={true} isMember={true} onLogout={() => {}} />);
  expect(screen.getByTestId('menu-carteira')).toHaveAttribute('href', '/carteira');
});

test('Ranking (sempre) e Mural (mobile) aparecem para membros OU admins', () => {
  // nem membro nem admin → não aparecem
  const { rerender } = render(<UserMenu user={baseUser} isSocio={true} isMember={false} isAdmin={false} onLogout={() => {}} />);
  expect(screen.queryByTestId('menu-ranking')).toBeNull();
  expect(screen.queryByTestId('menu-mural')).toBeNull();
  // membro
  rerender(<UserMenu user={baseUser} isSocio={true} isMember={true} isAdmin={false} onLogout={() => {}} />);
  expect(screen.getByTestId('menu-ranking')).toHaveAttribute('href', '/ranking');
  expect(screen.getByTestId('menu-mural')).toHaveAttribute('href', '/mural');
  // admin técnico (não-membro) → também aparecem
  rerender(<UserMenu user={baseUser} isSocio={false} isMember={false} isAdmin={true} onLogout={() => {}} />);
  expect(screen.getByTestId('menu-ranking')).toBeInTheDocument();
  expect(screen.getByTestId('menu-mural')).toBeInTheDocument();
});

test('Ajuda aparece para todos os roles e aponta para /ajuda', () => {
  const variantes = [
    { isAdmin: true, isMember: false, isSocio: false },
    { isAdmin: false, isMember: true, isSocio: true },
    { isAdmin: false, isMember: true, isSocio: false },
    { isAdmin: false, isMember: false, isSocio: false },
  ];
  variantes.forEach((v) => {
    const { unmount } = render(<UserMenu user={baseUser} onLogout={() => {}} {...v} />);
    expect(screen.getByTestId('menu-ajuda')).toHaveAttribute('href', '/ajuda');
    unmount();
  });
});

test('Sair chama onLogout', () => {
  const onLogout = jest.fn();
  render(<UserMenu user={baseUser} isSocio={true} isMember={true} onLogout={onLogout} />);
  fireEvent.click(screen.getByTestId('menu-sair'));
  expect(onLogout).toHaveBeenCalledTimes(1);
});

test('badge de estado aparece quando status != ativo', () => {
  render(<UserMenu user={{ ...baseUser, status: 'pendente_aprovacao' }} isSocio={true} isMember={true} onLogout={() => {}} />);
  expect(screen.getByTestId('menu-status')).toBeInTheDocument();
});
