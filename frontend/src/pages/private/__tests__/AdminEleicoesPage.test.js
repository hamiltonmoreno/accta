// Testes de componente para a UI nova da F7 (revisão da governança):
// - VotoCorrespondenciaModal (voto por correspondência)
// - ValidarListaModal (cargos cobertos pela lista)
//
// O `Dialog` (Radix) e o `MemberPicker` são mockados: evita fricção Radix/jsdom
// (ResizeObserver/pointer-capture) e o debounce+query do picker, isolando a
// lógica dos modais. Sem backend/DB — verificação reproduzível.
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

jest.mock('../../../components/ui/dialog', () => ({
  Dialog: ({ open, children }) => (open ? <div data-testid="dialog">{children}</div> : null),
  DialogContent: ({ children }) => <div>{children}</div>,
  DialogHeader: ({ children }) => <div>{children}</div>,
  DialogTitle: ({ children }) => <h2>{children}</h2>,
  DialogDescription: ({ children }) => <p>{children}</p>,
}));

// skeleton.jsx usa o alias `@/lib/utils` (não resolvido pelo jest); os modais não
// usam Skeleton — stub para não carregar o módulo.
jest.mock('../../../components/ui/skeleton', () => ({ Skeleton: () => null }));

// Stub do picker partilhado: um clique selecciona um eleitor fixo.
jest.mock('../../../components/MemberPicker', () => ({
  MemberPicker: ({ value, onSelect, testId }) =>
    value ? (
      <span data-testid={`${testId}-selected`}>{value.name}</span>
    ) : (
      <button
        type="button"
        data-testid={testId}
        onClick={() => onSelect({ id: 'u-123', name: 'Fulano de Tal', member_id: 'ACCTA-0001' })}
      >
        escolher
      </button>
    ),
}));

// A página importa utils/api → axios (ESM). Mock do axios (mesma convenção de
// utils/__tests__/api.test.js) para a página carregar; os modais não usam a API.
process.env.REACT_APP_BACKEND_URL = 'https://test-backend.example.com';
jest.mock('axios', () => {
  const instance = {
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  };
  return { __esModule: true, default: { create: () => instance } };
});

const { ValidarListaModal, VotoCorrespondenciaModal } = require('../AdminEleicoesPage');

const structure = {
  cargos: [
    { key: 'dir_presidente', label: 'Presidente da Direcção' },
    { key: 'dir_tesoureiro', label: 'Tesoureiro' },
  ],
};

describe('ValidarListaModal', () => {
  const lista = {
    id: 'l1',
    letra: 'A',
    candidatos: [
      { user_id: 'u1', cargo: 'dir_presidente', suplente: false },
      { user_id: 'u2', cargo: 'dir_tesoureiro', suplente: true },
    ],
  };

  it('mostra os cargos cobertos pela lista (com label) e marca o suplente', () => {
    render(<ValidarListaModal lista={lista} structure={structure} onClose={() => {}} onSubmit={() => {}} pending={false} />);
    expect(screen.getByText('Presidente da Direcção')).toBeInTheDocument();
    expect(screen.getByText('Tesoureiro')).toBeInTheDocument();
    // só o tesoureiro é suplente
    expect(screen.getAllByText('suplente')).toHaveLength(1);
  });

  it('aceitar chama onSubmit com { aceite: true }', async () => {
    const onSubmit = jest.fn();
    render(<ValidarListaModal lista={lista} structure={structure} onClose={() => {}} onSubmit={onSubmit} pending={false} />);
    await userEvent.click(screen.getByTestId('aceitar-lista-confirm'));
    expect(onSubmit).toHaveBeenCalledWith({ aceite: true });
  });

  it('rejeitar com motivo chama onSubmit com { aceite: false, motivo }', async () => {
    const onSubmit = jest.fn();
    render(<ValidarListaModal lista={lista} structure={structure} onClose={() => {}} onSubmit={onSubmit} pending={false} />);
    await userEvent.type(screen.getByTestId('rejeicao-motivo'), 'candidato inelegível');
    await userEvent.click(screen.getByTestId('rejeitar-lista-confirm'));
    expect(onSubmit).toHaveBeenCalledWith({ aceite: false, motivo: 'candidato inelegível' });
  });
});

describe('VotoCorrespondenciaModal', () => {
  const listas = [
    { id: 'lA', letra: 'A', nome: 'Lista Alfa', estado: 'aceite' },
    { id: 'lB', letra: 'B', nome: 'Lista Beta', estado: 'rejeitada' }, // não aceite → não aparece
  ];

  it('só lista as candidaturas aceites e mantém o submit desativado sem dados', () => {
    render(<VotoCorrespondenciaModal open onClose={() => {}} onSubmit={() => {}} pending={false} listas={listas} />);
    expect(screen.getByText('Lista A')).toBeInTheDocument(); // letra da lista aceite
    expect(screen.getByText('Lista Alfa')).toBeInTheDocument(); // nome da lista aceite
    expect(screen.queryByText('Lista Beta')).not.toBeInTheDocument(); // rejeitada → não aparece
    expect(screen.getByText('Voto em branco')).toBeInTheDocument();
    expect(screen.getByTestId('corr-confirm')).toBeDisabled();
  });

  it('happy path: eleitor + voto + justificação → onSubmit com { user_id, voto, justificacao }', async () => {
    const onSubmit = jest.fn();
    render(<VotoCorrespondenciaModal open onClose={() => {}} onSubmit={onSubmit} pending={false} listas={listas} />);

    await userEvent.click(screen.getByTestId('corr-voter')); // stub selecciona u-123
    await userEvent.click(screen.getByText('Voto em branco'));
    await userEvent.type(screen.getByTestId('corr-justificacao'), 'boletim recebido por correio');

    const confirm = screen.getByTestId('corr-confirm');
    expect(confirm).toBeEnabled();
    await userEvent.click(confirm);

    expect(onSubmit).toHaveBeenCalledWith({
      user_id: 'u-123',
      voto: 'branco',
      justificacao: 'boletim recebido por correio',
    });
  });

  it('justificação demasiado curta mantém o submit desativado', async () => {
    render(<VotoCorrespondenciaModal open onClose={() => {}} onSubmit={() => {}} pending={false} listas={listas} />);
    await userEvent.click(screen.getByTestId('corr-voter'));
    await userEvent.click(screen.getByText('Voto nulo'));
    await userEvent.type(screen.getByTestId('corr-justificacao'), 'ab'); // < 3
    expect(screen.getByTestId('corr-confirm')).toBeDisabled();
  });
});
