// Testes para o hook das categorias financeiras (Cat 4 §5.4).
//
// Padrao do projecto: mock axios (utils/api importa-o), QueryClient proprio.
// Cobre 4 cenarios: (1) fetch ok devolve do endpoint; (2) durante o load
// devolve fallback offline; (3) erro do endpoint cai no fallback; (4) labels
// sao mapeados nos arrays {value, label}.
import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';

process.env.REACT_APP_BACKEND_URL = 'https://test-backend.example.com';

const mockAxiosGet = jest.fn();
jest.mock('axios', () => {
  const instance = {
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
    get: (...args) => mockAxiosGet(...args),
    post: jest.fn(), put: jest.fn(), patch: jest.fn(), delete: jest.fn(),
  };
  return { __esModule: true, default: { create: () => instance } };
});

const { QueryClient, QueryClientProvider } = require('@tanstack/react-query');
const { useFinanceCategories } = require('../useFinanceCategories');

const wrapper = (client) => ({ children }) => (
  <QueryClientProvider client={client}>{children}</QueryClientProvider>
);

const newClient = () =>
  new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });

beforeEach(() => {
  mockAxiosGet.mockReset();
});

describe('useFinanceCategories', () => {
  test('durante o load devolve fallback offline (nao bloqueia o dropdown)', () => {
    mockAxiosGet.mockReturnValue(new Promise(() => {})); // nunca resolve
    const client = newClient();
    const { result } = renderHook(() => useFinanceCategories(), { wrapper: wrapper(client) });

    expect(result.current.isLoading).toBe(true);
    // fallback tem todas as estatutarias
    const incomeValues = result.current.income.map((c) => c.value);
    expect(incomeValues).toContain('quotas');
    expect(incomeValues).toContain('venda_publicacoes');
    expect(incomeValues).not.toContain('patrocinios'); // legada
    expect(result.current.expense.map((c) => c.value)).toContain('operacional');
  });

  test('apos resposta OK usa as listas do endpoint e mapeia labels', async () => {
    mockAxiosGet.mockResolvedValue({
      data: {
        income: ['quotas', 'donativos'],
        expense: ['operacional'],
        types: ['receita', 'despesa'],
        labels: { quotas: 'Quotas', donativos: 'Donativos', operacional: 'Operacional' },
      },
    });
    const client = newClient();
    const { result } = renderHook(() => useFinanceCategories(), { wrapper: wrapper(client) });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.income).toEqual([
      { value: 'quotas', label: 'Quotas' },
      { value: 'donativos', label: 'Donativos' },
    ]);
    expect(result.current.expense).toEqual([{ value: 'operacional', label: 'Operacional' }]);
    // chamou o endpoint canonico
    expect(mockAxiosGet).toHaveBeenCalledWith('/finances/meta/categories');
  });

  test('label em falta no endpoint cai no value (defensivo)', async () => {
    mockAxiosGet.mockResolvedValue({
      data: { income: ['novacat'], expense: [], types: ['receita', 'despesa'], labels: {} },
    });
    const client = newClient();
    const { result } = renderHook(() => useFinanceCategories(), { wrapper: wrapper(client) });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.income).toEqual([{ value: 'novacat', label: 'novacat' }]);
  });

  test('erro de rede cai no fallback (nao explode o dropdown)', async () => {
    mockAxiosGet.mockRejectedValue(new Error('boom'));
    const client = newClient();
    const { result } = renderHook(() => useFinanceCategories(), { wrapper: wrapper(client) });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    // mesmo com erro o hook devolve as listas do fallback
    const incomeValues = result.current.income.map((c) => c.value);
    expect(incomeValues).toContain('quotas');
    expect(incomeValues.length).toBeGreaterThan(0);
  });
});
