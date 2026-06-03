import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

jest.mock('react-router-dom', () => ({
  Link: ({ children, to, ...props }) => <a href={to} {...props}>{children}</a>,
}), { virtual: true });
jest.mock('date-fns', () => ({ format: () => '01 Jan 2030' }));
jest.mock('date-fns/locale', () => ({ ptBR: {} }));

jest.mock('../../../components/ui/skeleton', () => ({ Skeleton: () => null }));
jest.mock('../../../components/ui/dialog', () => ({
  Dialog: ({ open, children }) => (open ? <div>{children}</div> : null),
  DialogContent: ({ children }) => <div>{children}</div>,
  DialogHeader: ({ children }) => <div>{children}</div>,
  DialogTitle: ({ children }) => <h2>{children}</h2>,
  DialogDescription: ({ children }) => <p>{children}</p>,
}));

jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

jest.mock('../../../utils/api', () => ({
  assembleiasAPI: {
    list: jest.fn(),
  },
  honorariosAPI: {
    list: jest.fn(),
    create: jest.fn(),
    abrirVotacao: jest.fn(),
    apurar: jest.fn(),
    ligar: jest.fn(),
  },
  peticoesAPI: {
    list: jest.fn(),
    create: jest.fn(),
    assinar: jest.fn(),
    retirar: jest.fn(),
    encaminhar: jest.fn(),
  },
}));

const { useAuth } = require('../../../contexts/AuthContext');
const { assembleiasAPI, honorariosAPI, peticoesAPI } = require('../../../utils/api');
const { HonorariosPage } = require('../HonorariosPage');
const { PeticoesPage } = require('../PeticoesPage');

const renderPage = (page) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{page}</QueryClientProvider>,
  );
};

describe('participation pages assembleias contract', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    assembleiasAPI.list.mockResolvedValue({
      data: { assembleias: [{ id: 'ag1', titulo: 'AG 2030' }] },
    });
  });

  test('PeticoesPage uses the assembleias list returned by the API wrapper', async () => {
    useAuth.mockReturnValue({ isMesaAG: true, isAdmin: false });
    peticoesAPI.list.mockResolvedValue({
      data: [{
        id: 'pet1',
        titulo: 'Pedido de assembleia',
        fundamentacao: 'Fundamento',
        status: 'atingida',
        signature_count: 3,
      }],
    });

    renderPage(<PeticoesPage />);

    expect(await screen.findByText('AG 2030')).toBeInTheDocument();
  });

  test('HonorariosPage uses the assembleias list returned by the API wrapper', async () => {
    useAuth.mockReturnValue({ isAdmin: true, isDirecao: false, isMesaAG: false });
    honorariosAPI.list.mockResolvedValue({
      data: [{
        id: 'hon1',
        nominee_name: 'Nomeado',
        justificacao: 'Servicos relevantes',
        status: 'eleito',
      }],
    });

    renderPage(<HonorariosPage />);

    expect(await screen.findByText('AG 2030')).toBeInTheDocument();
  });
});
