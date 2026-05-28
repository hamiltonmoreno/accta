// Testes de componente para a sala de sessão "ao vivo" (F7).
//
// Estratégia (mesmo padrão do AdminEleicoesPage.test.js):
//  - mock axios ao nível do módulo p/ a utils/api.js carregar sem rede,
//  - wrapper TanStack QueryClient próprio por teste (estado isolado),
//  - sonner (toast) mockado para evitar Portal/jsdom friction,
//  - lucide-react NÃO mockado: SVG inline é benigno em jsdom.
import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

process.env.REACT_APP_BACKEND_URL = 'https://test-backend.example.com';

// react-router-dom v7 é ESM-only por exports — o transform default do CRA/jest
// não o resolve a partir do AssembleiaSalaPage.js. Como estes testes não
// exercitam Link/useParams, basta um stub.
// `{ virtual: true }` (mesmo pattern de ParticipationAssembleiasContract.test.js)
// — Jest não tenta resolver o módulo; o stub é totalmente virtual. Necessário
// porque react-router-dom v7 é ESM-only via `exports` e o resolver default
// do CRA não consegue resolvê-lo a partir de require/import em jest.
jest.mock('react-router-dom', () => ({
  useParams: () => ({ id: 'a1' }),
  Link: ({ children, ...rest }) => <a {...rest}>{children}</a>,
}), { virtual: true });

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

const mockToast = { success: jest.fn(), error: jest.fn(), warning: jest.fn() };
jest.mock('sonner', () => ({ toast: mockToast }));

const { QueryClient, QueryClientProvider } = require('@tanstack/react-query');
const { assembleiasAPI } = require('../../../utils/api');
const {
  QuorumBar,
  Countdown,
  CheckinParticipantePanel,
  PalavraPanel,
  VotacaoPanel,
  MocoesPanel,
} = require('../AssembleiaSalaPage');

const makeClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });

const wrap = (ui, client = makeClient()) => (
  <QueryClientProvider client={client}>{ui}</QueryClientProvider>
);

afterEach(() => {
  jest.clearAllMocks();
});

// --------------------------------------------------------------------------- //
// QuorumBar — render puro a partir do snapshot SSE ou fallback GET
// --------------------------------------------------------------------------- //

describe('QuorumBar', () => {
  it('mostra o esqueleto enquanto não há dados', () => {
    const { container } = render(<QuorumBar snapshot={null} fallback={null} />);
    // o `animate-pulse` é o esqueleto.
    expect(container.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('usa o snapshot SSE quando disponível (met=false em curso)', () => {
    const snap = {
      version: 5,
      chamada: 1,
      quorum: { required: 10, present_power: 4, met: false },
    };
    render(<QuorumBar snapshot={snap} fallback={null} />);
    expect(screen.getByText(/4\s*\/\s*10/)).toBeInTheDocument();
    expect(screen.getByText(/Chamada 1/)).toBeInTheDocument();
    expect(screen.getByText(/em curso/)).toBeInTheDocument();
  });

  it('quórum atingido pinta o estado de sucesso', () => {
    const snap = { version: 1, chamada: 2, quorum: { required: 4, present_power: 6, met: true } };
    render(<QuorumBar snapshot={snap} fallback={null} />);
    expect(screen.getByText(/atingido/)).toBeInTheDocument();
  });

  it('cai para o fallback quando o snapshot SSE ainda não chegou', () => {
    const fallback = { quorum_required: 6, present_voting_power: 5, quorum_met: false };
    render(<QuorumBar snapshot={null} fallback={fallback} />);
    expect(screen.getByText(/5\s*\/\s*6/)).toBeInTheDocument();
  });
});

// --------------------------------------------------------------------------- //
// Countdown — descida do tempo restante
// --------------------------------------------------------------------------- //

describe('Countdown', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2030-01-01T10:00:00Z'));
  });
  afterEach(() => {
    jest.useRealTimers();
  });

  it('mostra m:ss e desce a cada segundo', () => {
    const endsAt = new Date('2030-01-01T10:00:30Z').toISOString(); // 30s à frente
    const { rerender } = render(<Countdown endsAt={endsAt} />);
    expect(screen.getByText('0:30')).toBeInTheDocument();

    jest.advanceTimersByTime(5000);
    rerender(<Countdown endsAt={endsAt} />);
    expect(screen.getByText('0:25')).toBeInTheDocument();
  });

  it('não renderiza nada sem endsAt', () => {
    const { container } = render(<Countdown endsAt={null} />);
    expect(container.firstChild).toBeNull();
  });
});

// --------------------------------------------------------------------------- //
// CheckinParticipantePanel
// --------------------------------------------------------------------------- //

describe('CheckinParticipantePanel', () => {
  const assembleia = { id: 'a1', meeting_link: 'https://meet.example.com/abc' };

  it('quando presente apenas mostra a confirmação (sem botão de check-in)', () => {
    render(wrap(<CheckinParticipantePanel assembleia={assembleia} presente />));
    expect(screen.getByText(/Presente nesta sessão/)).toBeInTheDocument();
    expect(screen.queryByText(/Entrar na reunião/)).toBeNull();
  });

  it('"Entrar na reunião" abre o meeting_link em nova aba após registar', async () => {
    assembleiasAPI.checkin = jest.fn().mockResolvedValue({ data: {} });
    const winOpen = jest.spyOn(window, 'open').mockImplementation(() => null);

    render(wrap(<CheckinParticipantePanel assembleia={assembleia} presente={false} />));
    await userEvent.click(screen.getByRole('button', { name: /Entrar na reunião/ }));

    await waitFor(() => expect(assembleiasAPI.checkin).toHaveBeenCalled());
    expect(assembleiasAPI.checkin.mock.calls[0][1]).toEqual({ method: 'join_click' });
    expect(winOpen).toHaveBeenCalledWith(assembleia.meeting_link, '_blank', 'noopener');
    winOpen.mockRestore();
  });

  it('confirma com self_code quando o código está preenchido', async () => {
    assembleiasAPI.checkin = jest.fn().mockResolvedValue({ data: {} });
    render(wrap(<CheckinParticipantePanel assembleia={{ id: 'a1' }} presente={false} />));

    await userEvent.type(screen.getByLabelText(/Código de sessão/), 'abc123');
    await userEvent.click(screen.getByRole('button', { name: /Confirmar com código/ }));

    await waitFor(() => expect(assembleiasAPI.checkin).toHaveBeenCalled());
    expect(assembleiasAPI.checkin.mock.calls[0][1]).toEqual({ method: 'self_code', code: 'ABC123' });
  });
});

// --------------------------------------------------------------------------- //
// PalavraPanel — gating Mesa vs Participante
// --------------------------------------------------------------------------- //

describe('PalavraPanel', () => {
  const assembleia = { id: 'a1' };

  it('participante presente vê o botão "Pedir a palavra"', async () => {
    assembleiasAPI.palavra = jest.fn().mockResolvedValue({ data: { palavra: [] } });
    render(wrap(<PalavraPanel assembleia={assembleia} snapshot={null} isMesa={false} presente />));
    await waitFor(() => expect(assembleiasAPI.palavra).toHaveBeenCalled());
    expect(screen.getByRole('button', { name: /Pedir a palavra/ })).toBeInTheDocument();
  });

  it('participante não-presente não vê o botão de pedir', async () => {
    assembleiasAPI.palavra = jest.fn().mockResolvedValue({ data: { palavra: [] } });
    render(wrap(<PalavraPanel assembleia={assembleia} snapshot={null} isMesa={false} presente={false} />));
    await waitFor(() => expect(assembleiasAPI.palavra).toHaveBeenCalled());
    expect(screen.queryByRole('button', { name: /Pedir a palavra/ })).toBeNull();
  });

  it('Mesa vê "Conceder" em pedidos inscritos e "Terminar" no orador actual', async () => {
    assembleiasAPI.palavra = jest.fn().mockResolvedValue({
      data: {
        palavra: [
          { id: 'q-falar', user_id: 'u1', tipo: 'intervencao', status: 'a_falar', ends_at: null, requested_at: 't1', duration_limit_s: 180 },
          { id: 'q-insc', user_id: 'u2', tipo: 'protesto', status: 'inscrito', ordem: 1, requested_at: 't2', duration_limit_s: 60 },
        ],
      },
    });
    render(wrap(<PalavraPanel assembleia={assembleia} snapshot={null} isMesa presente={false} />));
    // findBy* espera o estado async (TanStack) materializar antes de assertar.
    expect(await screen.findByRole('button', { name: /Terminar/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Conceder/ })).toBeInTheDocument();
  });

  it('pedir a palavra chama o endpoint com o tipo escolhido', async () => {
    assembleiasAPI.palavra = jest.fn().mockResolvedValue({ data: { palavra: [] } });
    assembleiasAPI.pedirPalavra = jest.fn().mockResolvedValue({ data: {} });
    render(wrap(<PalavraPanel assembleia={assembleia} snapshot={null} isMesa={false} presente />));
    await waitFor(() => expect(assembleiasAPI.palavra).toHaveBeenCalled());

    await userEvent.selectOptions(screen.getByLabelText(/Tipo/), 'protesto');
    await userEvent.click(screen.getByRole('button', { name: /Pedir a palavra/ }));

    await waitFor(() => expect(assembleiasAPI.pedirPalavra).toHaveBeenCalled());
    expect(assembleiasAPI.pedirPalavra.mock.calls[0][1]).toEqual({ tipo: 'protesto' });
  });
});

// --------------------------------------------------------------------------- //
// VotacaoPanel — modos + exclusão por conflito
// --------------------------------------------------------------------------- //

describe('VotacaoPanel', () => {
  const assembleia = { id: 'a1' };

  it('sem voto aberto: Mesa vê o form "Abrir deliberação"', () => {
    render(wrap(
      <VotacaoPanel assembleia={assembleia} snapshot={{ open_vote: null }} isMesa currentUserId="u1" />,
    ));
    expect(screen.getByRole('button', { name: /Abrir deliberação/ })).toBeInTheDocument();
  });

  it('sem voto aberto: Participante vê só a mensagem informativa', () => {
    render(wrap(
      <VotacaoPanel assembleia={assembleia} snapshot={{ open_vote: null }} isMesa={false} currentUserId="u1" />,
    ));
    expect(screen.getByText(/Sem deliberação aberta/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Abrir deliberação/ })).toBeNull();
  });

  it('voto nominal aberto: Participante vê os botões favor/contra/abstenção', async () => {
    assembleiasAPI.getDeliberacao = jest.fn().mockResolvedValue({
      data: { id: 'd1', ponto: 'P1', descricao: 'd', voting_mode: 'nominal', conflitos_excluidos: [] },
    });
    const snapshot = { open_vote: { deliberacao_id: 'd1', voting_mode: 'nominal', ponto: 'P1' } };
    render(wrap(<VotacaoPanel assembleia={assembleia} snapshot={snapshot} isMesa={false} currentUserId="u1" />));
    await waitFor(() => expect(assembleiasAPI.getDeliberacao).toHaveBeenCalled());
    expect(screen.getByRole('button', { name: /A favor/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Contra/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Abstenção/ })).toBeInTheDocument();
  });

  it('excluído por conflito não vê botões de voto e tem aviso', async () => {
    assembleiasAPI.getDeliberacao = jest.fn().mockResolvedValue({
      data: { id: 'd1', ponto: 'P1', descricao: 'd', voting_mode: 'nominal', conflitos_excluidos: ['u1'] },
    });
    const snapshot = { open_vote: { deliberacao_id: 'd1', voting_mode: 'nominal', ponto: 'P1' } };
    render(wrap(<VotacaoPanel assembleia={assembleia} snapshot={snapshot} isMesa={false} currentUserId="u1" />));
    expect(await screen.findByText(/Está excluído desta votação/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /A favor/ })).toBeNull();
  });

  it('voto braço-no-ar: Participante NÃO vê botões individuais; Mesa vê form de contagem', async () => {
    assembleiasAPI.getDeliberacao = jest.fn().mockResolvedValue({
      data: { id: 'd1', ponto: 'P1', descricao: 'd', voting_mode: 'braco_no_ar', conflitos_excluidos: [] },
    });
    const snapshot = { open_vote: { deliberacao_id: 'd1', voting_mode: 'braco_no_ar', ponto: 'P1' } };

    const { rerender } = render(wrap(
      <VotacaoPanel assembleia={assembleia} snapshot={snapshot} isMesa={false} currentUserId="u1" />,
    ));
    await waitFor(() => expect(assembleiasAPI.getDeliberacao).toHaveBeenCalled());
    expect(screen.queryByRole('button', { name: /A favor/ })).toBeNull();

    rerender(wrap(
      <VotacaoPanel assembleia={assembleia} snapshot={snapshot} isMesa currentUserId="u1" />,
    ));
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Registar contagem/ })).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: /Apurar deliberação/ })).toBeInTheDocument();
  });

  it('voto nominal: clicar "A favor" chama votar com escolha=favor', async () => {
    assembleiasAPI.getDeliberacao = jest.fn().mockResolvedValue({
      data: { id: 'd1', ponto: 'P1', descricao: 'd', voting_mode: 'nominal', conflitos_excluidos: [] },
    });
    assembleiasAPI.votarDeliberacao = jest.fn().mockResolvedValue({ data: {} });
    const snapshot = { open_vote: { deliberacao_id: 'd1', voting_mode: 'nominal', ponto: 'P1' } };
    render(wrap(<VotacaoPanel assembleia={assembleia} snapshot={snapshot} isMesa={false} currentUserId="u1" />));
    await waitFor(() => expect(assembleiasAPI.getDeliberacao).toHaveBeenCalled());

    await userEvent.click(screen.getByRole('button', { name: /A favor/ }));
    await waitFor(() => expect(assembleiasAPI.votarDeliberacao).toHaveBeenCalled());
    const [aid, did, payload] = assembleiasAPI.votarDeliberacao.mock.calls[0];
    expect(aid).toBe('a1');
    expect(did).toBe('d1');
    expect(payload).toEqual({ escolha: 'favor' });
  });
});

// --------------------------------------------------------------------------- //
// MocoesPanel
// --------------------------------------------------------------------------- //

describe('MocoesPanel', () => {
  const assembleia = { id: 'a1' };

  it('lista mostra o badge "voto imediato" para requerimento', async () => {
    assembleiasAPI.mocoes = jest.fn().mockResolvedValue({
      data: {
        mocoes: [
          { id: 'm1', tipo: 'requerimento', titulo: 'Encerrar debate', texto: 'já', status: 'submetida', votacao_imediata: true, proposta_por: 'u-other' },
          { id: 'm2', tipo: 'mocao', titulo: 'Aprovar X', texto: 'porque', status: 'submetida', votacao_imediata: false, proposta_por: 'u-other' },
        ],
      },
    });
    render(wrap(<MocoesPanel assembleia={assembleia} snapshot={null} isMesa presente={false} currentUserId="u1" />));
    // Exact match: a label do dropdown ("Requerimento (voto imediato)") também
    // contém "voto imediato" — só o badge tem essa string como textContent isolado.
    expect(await screen.findByText(/^voto imediato$/)).toBeInTheDocument();
  });

  it('Mesa vê "Colocar a voto" em moções submetidas', async () => {
    assembleiasAPI.mocoes = jest.fn().mockResolvedValue({
      data: { mocoes: [{ id: 'm1', tipo: 'mocao', titulo: 'X', texto: 'y', status: 'submetida', votacao_imediata: false, proposta_por: 'u-other' }] },
    });
    render(wrap(<MocoesPanel assembleia={assembleia} snapshot={null} isMesa presente={false} currentUserId="u1" />));
    expect(await screen.findByRole('button', { name: /Colocar a voto/ })).toBeInTheDocument();
  });

  it('o proponente vê "Retirar" mas não "Colocar a voto"', async () => {
    assembleiasAPI.mocoes = jest.fn().mockResolvedValue({
      data: { mocoes: [{ id: 'm1', tipo: 'mocao', titulo: 'X', texto: 'y', status: 'submetida', votacao_imediata: false, proposta_por: 'u1' }] },
    });
    render(wrap(<MocoesPanel assembleia={assembleia} snapshot={null} isMesa={false} presente={false} currentUserId="u1" />));
    expect(await screen.findByRole('button', { name: /Retirar/ })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Colocar a voto/ })).toBeNull();
  });

  it('submeter com tipo=requerimento envia o payload completo', async () => {
    assembleiasAPI.mocoes = jest.fn().mockResolvedValue({ data: { mocoes: [] } });
    assembleiasAPI.submeterMocao = jest.fn().mockResolvedValue({ data: {} });
    render(wrap(<MocoesPanel assembleia={assembleia} snapshot={null} isMesa={false} presente currentUserId="u1" />));
    // O form só aparece quando o presente=true; aguardar a renderização inicial.
    const tituloInput = await screen.findByLabelText('Título');

    await userEvent.selectOptions(screen.getByLabelText('Tipo'), 'requerimento');
    await userEvent.type(tituloInput, 'Encerrar a sessão');
    await userEvent.type(screen.getByLabelText('Texto'), 'já chega');
    // O botão "Submeter" é o type=submit do form; selecciono pelo papel/nome
    // ambíguo: há um "Submeter" header e o botão — uso `name` exacto.
    const submitButtons = screen.getAllByRole('button', { name: 'Submeter' });
    await userEvent.click(submitButtons[submitButtons.length - 1]);

    await waitFor(() => expect(assembleiasAPI.submeterMocao).toHaveBeenCalled());
    expect(assembleiasAPI.submeterMocao.mock.calls[0][1]).toEqual({
      tipo: 'requerimento',
      titulo: 'Encerrar a sessão',
      texto: 'já chega',
    });
  });
});
