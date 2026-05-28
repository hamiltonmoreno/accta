// Testes para o hook do SSE per-assembleia.
//
// Padrão do projeto: mock axios (utils/api importa-o), QueryClient próprio.
// EventSource é stub: jsdom não o implementa. Captamos o construtor para
// disparar onmessage/onerror conforme cada cenário.
import React from 'react';
import { render, act, waitFor } from '@testing-library/react';

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

// Stub mínimo de EventSource que regista as instâncias criadas para os testes
// poderem injectar mensagens/erros via `instances[0].onmessage(...)`.
const instances = [];
class FakeEventSource {
  constructor(url, opts) {
    this.url = url;
    this.opts = opts;
    this.onmessage = null;
    this.onerror = null;
    this.closed = false;
    instances.push(this);
  }
  close() { this.closed = true; }
}
beforeEach(() => {
  instances.length = 0;
  // jsdom não tem EventSource; instala stub no `globalThis` (resolve para
  // `window` no jsdom) para o hook o consumir.
  globalThis.EventSource = FakeEventSource;
});

const { QueryClient, QueryClientProvider, useQueryClient } = require('@tanstack/react-query');
const { useAssembleiaStream } = require('../useAssembleiaStream');

const Wrapper = ({ children, client }) => (
  <QueryClientProvider client={client}>{children}</QueryClientProvider>
);

const Probe = ({ id, onSnap, onClient }) => {
  const snap = useAssembleiaStream(id);
  const qc = useQueryClient();
  React.useEffect(() => { onClient?.(qc); }, [qc, onClient]);
  React.useEffect(() => { onSnap?.(snap); }, [snap, onSnap]);
  return null;
};

describe('useAssembleiaStream', () => {
  it('abre EventSource com withCredentials e o URL certo', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<Wrapper client={client}><Probe id="a1" /></Wrapper>);
    expect(instances).toHaveLength(1);
    expect(instances[0].url).toBe('https://test-backend.example.com/api/assembleias/a1/stream');
    expect(instances[0].opts).toEqual({ withCredentials: true });
  });

  it('actualiza o snapshot e a cache TanStack ao receber mensagem', async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const snaps = [];
    render(<Wrapper client={client}><Probe id="a1" onSnap={(s) => snaps.push(s)} /></Wrapper>);
    await waitFor(() => expect(instances).toHaveLength(1));

    const data = { version: 7, phase: 'checkin', quorum: { required: 5, present_power: 3, met: false } };
    act(() => {
      instances[0].onmessage({ data: JSON.stringify(data) });
    });

    await waitFor(() => expect(snaps.at(-1)).toEqual(data));
    expect(client.getQueryData(['assembleia', 'a1', 'snapshot'])).toEqual(data);
  });

  it('ignora mensagens com JSON inválido sem partir o hook', async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<Wrapper client={client}><Probe id="a1" /></Wrapper>);
    await waitFor(() => expect(instances).toHaveLength(1));

    expect(() => act(() => instances[0].onmessage({ data: '<<not-json>>' }))).not.toThrow();
  });

  it('em erro do EventSource, cai para polling de 30s (invalida queries da assembleia)', () => {
    jest.useFakeTimers();
    try {
      const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
      const invalidate = jest.spyOn(client, 'invalidateQueries');
      render(<Wrapper client={client}><Probe id="a1" /></Wrapper>);
      expect(instances).toHaveLength(1);

      act(() => instances[0].onerror({}));
      expect(instances[0].closed).toBe(true);

      act(() => jest.advanceTimersByTime(31_000));
      expect(invalidate).toHaveBeenCalledWith({ queryKey: ['assembleia', 'a1'] });
    } finally {
      jest.useRealTimers();
    }
  });

  it('fecha o stream ao desmontar', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const { unmount } = render(<Wrapper client={client}><Probe id="a1" /></Wrapper>);
    expect(instances[0].closed).toBe(false);
    unmount();
    expect(instances[0].closed).toBe(true);
  });

  it('não abre o stream quando o id é falsy', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(<Wrapper client={client}><Probe id={null} /></Wrapper>);
    expect(instances).toHaveLength(0);
  });
});
