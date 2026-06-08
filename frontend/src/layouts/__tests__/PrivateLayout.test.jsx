import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

jest.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
  useNavigate: () => jest.fn(),
  useLocation: () => ({ pathname: '/dashboard' }),
}), { virtual: true });
jest.mock('../../contexts/AuthContext', () => ({ useAuth: jest.fn() }));
jest.mock('../components/Header', () => ({
  Header: () => <header data-testid="app-header" />,
}));
jest.mock('../../utils/api', () => ({
  registrationAPI: { listPending: jest.fn().mockResolvedValue({ data: [] }) },
}));

const { useAuth } = require('../../contexts/AuthContext');
const { PrivateLayout } = require('../PrivateLayout');

const renderLayout = () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <PrivateLayout><div data-testid="conteudo">Olá</div></PrivateLayout>
    </QueryClientProvider>,
  );
};

beforeEach(() => {
  jest.clearAllMocks();
  useAuth.mockReturnValue({
    user: { name: 'Sócio', email: 's@accta.cv', role: 'socio', account_type: 'member' },
    logout: jest.fn(),
    isAdmin: false, isFinanceiro: false, isModerador: false, isDirecao: false, isMesaAG: false,
  });
});

test('renderiza o cabeçalho e o conteúdo', () => {
  renderLayout();
  expect(screen.getByTestId('app-header')).toBeInTheDocument();
  expect(screen.getByTestId('conteudo')).toHaveTextContent('Olá');
});

test('sidebar: Mural saiu p/ o cabeçalho; Administração + Configurações (Aparência) presentes', () => {
  // admin para ver as secções Administração/Configurações (itens admin-gated)
  useAuth.mockReturnValue({
    user: { name: 'Admin', email: 'a@accta.cv', role: 'admin', account_type: 'technical' },
    logout: jest.fn(),
    isAdmin: true, isFinanceiro: false, isModerador: false, isDirecao: false, isMesaAG: false,
  });
  renderLayout();
  const sidebar = screen.getByTestId('desktop-sidebar');
  // Comunidade mantém-se mas SEM Mural (foi p/ o cabeçalho) e SEM Aparência (foi p/ Configurações)
  expect(within(sidebar).getByText('Galeria')).toBeInTheDocument();
  expect(within(sidebar).queryByText('Mural')).toBeNull();
  // Novas secções
  expect(within(sidebar).getByText('Administração')).toBeInTheDocument();
  expect(within(sidebar).getByText('Configurações do sistema')).toBeInTheDocument();
  expect(within(sidebar).getByText('Aparência')).toBeInTheDocument();
  // Itens que vivem no cabeçalho/dropdown não estão no sidebar
  expect(within(sidebar).queryByText('Meu Perfil')).toBeNull();
  expect(within(sidebar).queryByText('Notificações')).toBeNull();
  expect(within(sidebar).queryByText('Ranking')).toBeNull();
  expect(within(sidebar).queryByText('Carteira Digital')).toBeNull();
  expect(within(sidebar).queryByText('Sair')).toBeNull();
});
