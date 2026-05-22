import React, { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { eleicoesAPI, cargosAPI, governanceAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { ELEICAO_STATUS_LABELS, cargoLabelFrom, orgaoLabel } from '../../lib/governanceLabels';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import {
  Vote, ListChecks, Search, Plus, Trophy, AlertTriangle, CheckCircle2, XCircle,
  Clock, FileSignature, Layers, CalendarRange, Hash,
} from 'lucide-react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../components/ui/dialog';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

const MODO_LABELS = {
  presencial: 'Presencial',
  correspondencia: 'Correspondência',
  digital: 'Digital',
  hibrido: 'Híbrido',
};

// Mapeia cada status ao seu par semântico (icone + cor). Status = icone + texto + cor.
const STATUS_STYLE = {
  preparacao: { icon: Clock, fg: 'text-[#6B7280]', bg: 'bg-[#F5F5F5]', ring: 'ring-[#E5E7EB]' },
  candidaturas: { icon: FileSignature, fg: 'text-[#1D4ED8]', bg: 'bg-[#EFF6FF]', ring: 'ring-[#BFDBFE]' },
  campanha: { icon: FileSignature, fg: 'text-[#1D4ED8]', bg: 'bg-[#EFF6FF]', ring: 'ring-[#BFDBFE]' },
  votacao: { icon: Vote, fg: 'text-[#B45309]', bg: 'bg-[#FFFBEB]', ring: 'ring-[#FDE68A]' },
  apurada: { icon: ListChecks, fg: 'text-[#15803D]', bg: 'bg-[#F0FDF4]', ring: 'ring-[#BBF7D0]' },
  recurso: { icon: AlertTriangle, fg: 'text-[#B45309]', bg: 'bg-[#FFFBEB]', ring: 'ring-[#FDE68A]' },
  proclamada: { icon: Trophy, fg: 'text-[#15803D]', bg: 'bg-[#F0FDF4]', ring: 'ring-[#BBF7D0]' },
  anulada: { icon: XCircle, fg: 'text-[#B91C1C]', bg: 'bg-[#FEF2F2]', ring: 'ring-[#FECACA]' },
};

const ESTADO_LISTA_STYLE = {
  submetida: { fg: 'text-[#6B7280]', bg: 'bg-[#F5F5F5]', label: 'Submetida' },
  aceite: { fg: 'text-[#15803D]', bg: 'bg-[#F0FDF4]', label: 'Aceite' },
  rejeitada: { fg: 'text-[#B91C1C]', bg: 'bg-[#FEF2F2]', label: 'Rejeitada' },
};

const formatDate = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return '—';
  }
};

const StatusBadge = ({ status }) => {
  const s = STATUS_STYLE[status] || STATUS_STYLE.preparacao;
  const Icon = s.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ${s.bg} ${s.fg} ${s.ring}`}
      data-testid={`status-${status}`}
    >
      <Icon className="w-3.5 h-3.5" aria-hidden="true" />
      {ELEICAO_STATUS_LABELS[status] || status}
    </span>
  );
};

// Procura de sócios elegíveis (debounced) para preencher um slot de candidatura.
const CandidatePicker = ({ value, onSelect, testId }) => {
  const [search, setSearch] = useState('');
  const [debounced, setDebounced] = useState('');

  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  const { data: candidates = [], isFetching } = useQuery({
    queryKey: queryKeys.cargos.candidates({ q: debounced }),
    queryFn: async () => (await cargosAPI.candidates({ q: debounced || undefined })).data.candidates,
    staleTime: 30 * 1000,
  });

  if (value) {
    return (
      <div className="flex items-center justify-between px-3 py-2 rounded-md border border-[#D1D5DB] bg-[#F5F5F5]">
        <span className="text-sm text-grafite truncate">
          {value.name} <span className="font-mono text-xs text-[#6B7280]">{value.member_id || ''}</span>
        </span>
        <button
          type="button"
          onClick={() => onSelect(null)}
          className="text-xs text-carmesim font-semibold hover:underline cursor-pointer ml-2 shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 rounded"
        >
          Alterar
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Procurar sócio por nome, email ou nº..."
          className="w-full pl-9 pr-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 outline-none"
          data-testid={testId}
        />
      </div>
      {debounced && (
        <div className="mt-1.5 max-h-40 overflow-y-auto rounded-md border border-gray-100 divide-y divide-gray-50">
          {isFetching && candidates.length === 0 ? (
            <div className="px-3 py-2.5"><Skeleton className="h-4 w-40" /></div>
          ) : candidates.length === 0 ? (
            <p className="px-3 py-2.5 text-xs text-[#6B7280]">Nenhum sócio encontrado.</p>
          ) : (
            candidates.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => onSelect(c)}
                className="w-full text-left px-3 py-2 hover:bg-[#F5F5F5] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
                data-testid={`candidate-${c.id}`}
              >
                <span className="text-sm text-grafite">{c.name}</span>
                <span className="ml-2 font-mono text-xs text-[#6B7280]">{c.member_id || ''}</span>
                <span className="block text-xs text-[#6B7280]">{c.email}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};

const fieldClass = 'w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 outline-none';
const labelClass = 'block text-xs font-medium text-[#6B7280] mb-1.5';
const secondaryBtn = 'px-4 py-2 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 disabled:opacity-50';
const primaryBtn = 'px-4 py-2 rounded-md bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 ring-offset-2 disabled:opacity-50';

// ── Modal: criar eleição ────────────────────────────────────────────────────
const CriarEleicaoModal = ({ open, onClose, onSubmit, pending }) => {
  const [form, setForm] = useState({ ano: new Date().getFullYear(), mandato_inicio: '', mandato_fim: '', modo_votacao: 'presencial', direcao_titulares: 5 });

  useEffect(() => {
    if (open) setForm({ ano: new Date().getFullYear(), mandato_inicio: '', mandato_fim: '', modo_votacao: 'presencial', direcao_titulares: 5 });
  }, [open]);

  const valid = form.ano && form.mandato_inicio && form.mandato_fim;

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Criar eleição</DialogTitle>
          <DialogDescription>Defina o ano, o mandato e o modo de votação dos órgãos sociais.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass} htmlFor="ele-ano">Ano</label>
              <input
                id="ele-ano"
                type="number"
                value={form.ano}
                onChange={(e) => setForm({ ...form, ano: Number(e.target.value) })}
                className={fieldClass}
                data-testid="eleicao-ano"
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="ele-direcao">Titulares da Direcção</label>
              <select
                id="ele-direcao"
                value={form.direcao_titulares}
                onChange={(e) => setForm({ ...form, direcao_titulares: Number(e.target.value) })}
                className={`${fieldClass} bg-white`}
              >
                <option value={5}>5</option>
                <option value={7}>7</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass} htmlFor="ele-inicio">Início do mandato</label>
              <input
                id="ele-inicio"
                type="date"
                value={form.mandato_inicio}
                onChange={(e) => setForm({ ...form, mandato_inicio: e.target.value })}
                className={fieldClass}
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="ele-fim">Fim do mandato</label>
              <input
                id="ele-fim"
                type="date"
                value={form.mandato_fim}
                onChange={(e) => setForm({ ...form, mandato_fim: e.target.value })}
                className={fieldClass}
              />
            </div>
          </div>
          <div>
            <label className={labelClass} htmlFor="ele-modo">Modo de votação</label>
            <select
              id="ele-modo"
              value={form.modo_votacao}
              onChange={(e) => setForm({ ...form, modo_votacao: e.target.value })}
              className={`${fieldClass} bg-white`}
            >
              {Object.entries(MODO_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className={secondaryBtn}>Cancelar</button>
            <button
              type="button"
              onClick={() => onSubmit({
                ano: Number(form.ano),
                mandato_inicio: form.mandato_inicio,
                mandato_fim: form.mandato_fim,
                modo_votacao: form.modo_votacao,
                direcao_titulares: Number(form.direcao_titulares),
              })}
              disabled={!valid || pending}
              className={primaryBtn}
              data-testid="criar-eleicao-confirm"
            >
              {pending ? 'A criar...' : 'Criar eleição'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ── Modal: submeter lista (um candidato por slot) ─────────────────────────────
const SubmeterListaModal = ({ open, onClose, onSubmit, pending, slots, structure }) => {
  const [letra, setLetra] = useState('');
  const [nome, setNome] = useState('');
  const [picks, setPicks] = useState({}); // slot_key -> user

  useEffect(() => {
    if (open) { setLetra(''); setNome(''); setPicks({}); }
  }, [open]);

  const allFilled = slots.length > 0 && slots.every((s) => picks[s.slot_key]);
  const valid = letra.trim() && allFilled;

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Submeter lista</DialogTitle>
          <DialogDescription>
            Indique a letra da lista e atribua um sócio a cada um dos {slots.length} lugares.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className={labelClass} htmlFor="lista-letra">Letra</label>
              <input
                id="lista-letra"
                type="text"
                maxLength={2}
                value={letra}
                onChange={(e) => setLetra(e.target.value.toUpperCase())}
                placeholder="A"
                className={`${fieldClass} text-center font-semibold`}
                data-testid="lista-letra"
              />
            </div>
            <div className="col-span-2">
              <label className={labelClass} htmlFor="lista-nome">Nome (opcional)</label>
              <input
                id="lista-nome"
                type="text"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                placeholder="Lista de candidatura"
                className={fieldClass}
              />
            </div>
          </div>

          <div>
            <p className={labelClass}>Candidatos por lugar</p>
            <div className="max-h-72 overflow-y-auto space-y-3 pr-1 rounded-md border border-[#E5E7EB] p-3 bg-[#F5F5F5]/40">
              {slots.map((s) => (
                <div key={s.slot_key} className="rounded-md border border-[#E5E7EB] bg-white p-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-medium text-grafite">
                      {cargoLabelFrom(structure, s.cargo)}
                      {s.suplente && <span className="text-xs text-[#6B7280] font-normal"> (suplente)</span>}
                    </span>
                    <span className="text-xs text-[#6B7280]">{orgaoLabel(s.orgao)}</span>
                  </div>
                  <CandidatePicker
                    value={picks[s.slot_key] || null}
                    onSelect={(u) => setPicks((prev) => ({ ...prev, [s.slot_key]: u }))}
                    testId={`slot-picker-${s.slot_key}`}
                  />
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className={secondaryBtn}>Cancelar</button>
            <button
              type="button"
              onClick={() => onSubmit({
                letra: letra.trim(),
                nome: nome.trim() || undefined,
                candidatos: slots.map((s) => ({ slot_key: s.slot_key, user_id: picks[s.slot_key].id })),
              })}
              disabled={!valid || pending}
              className={primaryBtn}
              data-testid="submeter-lista-confirm"
            >
              {pending ? 'A submeter...' : 'Submeter lista'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ── Modal: votar (sócio votante) — SEGREDO: nunca regista quem votou na UI ────
const VotarModal = ({ open, onClose, onSubmit, pending, listas }) => {
  const [voto, setVoto] = useState(null);

  useEffect(() => { if (open) setVoto(null); }, [open]);

  const aceites = listas.filter((l) => l.estado === 'aceite');

  const Option = ({ id, children }) => (
    <label
      className={`flex items-center gap-3 px-3 py-2.5 rounded-md border cursor-pointer transition-colors ${voto === id ? 'border-carmesim bg-carmesim/5' : 'border-[#E5E7EB] hover:bg-[#F5F5F5]'}`}
    >
      <input
        type="radio"
        name="voto"
        checked={voto === id}
        onChange={() => setVoto(id)}
        className="text-carmesim focus:ring-carmesim/40"
      />
      <span className="text-sm text-grafite">{children}</span>
    </label>
  );

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Votar</DialogTitle>
          <DialogDescription>O voto é secreto. Selecione uma lista, voto em branco ou nulo.</DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          {aceites.map((l) => (
            <Option key={l.id} id={l.id}>
              <span className="font-semibold mr-1">Lista {l.letra}</span>{l.nome || ''}
            </Option>
          ))}
          <Option id="branco">Voto em branco</Option>
          <Option id="nulo">Voto nulo</Option>
        </div>
        <div className="flex justify-end gap-2 pt-3">
          <button type="button" onClick={onClose} className={secondaryBtn}>Cancelar</button>
          <button
            type="button"
            onClick={() => onSubmit({ voto })}
            disabled={!voto || pending}
            className={primaryBtn}
            data-testid="votar-confirm"
          >
            {pending ? 'A registar...' : 'Registar voto'}
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ── Modal: validar / rejeitar lista ───────────────────────────────────────────
const ValidarListaModal = ({ lista, structure, onClose, onSubmit, pending }) => {
  const [motivo, setMotivo] = useState('');

  useEffect(() => { setMotivo(''); }, [lista]);

  const candidatos = lista?.candidatos || [];

  return (
    <Dialog open={!!lista} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Validar lista {lista?.letra}</DialogTitle>
          <DialogDescription>Confira os cargos cobertos e aceite a lista, ou rejeite-a indicando o motivo.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          {candidatos.length > 0 && (
            <div>
              <p className={labelClass}>Cargos na lista ({candidatos.length})</p>
              <ul className="max-h-44 overflow-y-auto rounded-md border border-[#E5E7EB] divide-y divide-[#F5F5F5] text-sm" data-testid="validar-candidatos">
                {candidatos.map((c, i) => (
                  <li key={c.user_id || c.slot_key || i} className="px-3 py-1.5 flex items-center justify-between gap-2">
                    <span className="text-grafite truncate">{cargoLabelFrom(structure, c.cargo)}</span>
                    {c.suplente && <span className="text-xs text-[#6B7280] shrink-0">suplente</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div>
            <label className={labelClass} htmlFor="rejeicao-motivo">Motivo (em caso de rejeição)</label>
            <textarea
              id="rejeicao-motivo"
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              rows={2}
              maxLength={500}
              placeholder="Ex.: candidato inelegível"
              className={`${fieldClass} resize-none`}
              data-testid="rejeicao-motivo"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => onSubmit({ aceite: false, motivo: motivo.trim() || undefined })}
              disabled={pending}
              className={`${secondaryBtn} text-[#B91C1C] border-[#FECACA] hover:bg-[#FEF2F2]`}
              data-testid="rejeitar-lista-confirm"
            >
              Rejeitar
            </button>
            <button
              type="button"
              onClick={() => onSubmit({ aceite: true })}
              disabled={pending}
              className={primaryBtn}
              data-testid="aceitar-lista-confirm"
            >
              {pending ? 'A validar...' : 'Aceitar lista'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ── Modal: voto por correspondência (Comissão/Mesa/admin) ─────────────────────
// Registo administrativo de um boletim recebido por correspondência. SEGREDO: o
// sentido do voto nunca é confirmado associado ao eleitor após submissão.
const VotoCorrespondenciaModal = ({ open, onClose, onSubmit, pending, listas }) => {
  const [voter, setVoter] = useState(null);
  const [voto, setVoto] = useState(null);
  const [justificacao, setJustificacao] = useState('');

  useEffect(() => { if (open) { setVoter(null); setVoto(null); setJustificacao(''); } }, [open]);

  const aceites = listas.filter((l) => l.estado === 'aceite');
  const Option = ({ id, children }) => (
    <label className={`flex items-center gap-3 px-3 py-2.5 rounded-md border cursor-pointer transition-colors ${voto === id ? 'border-carmesim bg-carmesim/5' : 'border-[#E5E7EB] hover:bg-[#F5F5F5]'}`}>
      <input type="radio" name="voto-corr" checked={voto === id} onChange={() => setVoto(id)} className="text-carmesim focus:ring-carmesim/40" />
      <span className="text-sm text-grafite">{children}</span>
    </label>
  );

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Voto por correspondência</DialogTitle>
          <DialogDescription>Registo administrativo de um boletim recebido por correspondência. O sentido do voto não fica associado ao eleitor.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Eleitor</label>
            <CandidatePicker value={voter} onSelect={setVoter} testId="corr-voter" />
          </div>
          <div className="space-y-2">
            {aceites.map((l) => (
              <Option key={l.id} id={l.id}><span className="font-semibold mr-1">Lista {l.letra}</span>{l.nome || ''}</Option>
            ))}
            <Option id="branco">Voto em branco</Option>
            <Option id="nulo">Voto nulo</Option>
          </div>
          <div>
            <label className={labelClass} htmlFor="corr-just">Justificação</label>
            <textarea
              id="corr-just"
              value={justificacao}
              onChange={(e) => setJustificacao(e.target.value)}
              rows={2}
              maxLength={500}
              placeholder="Ex.: boletim recebido por correio em DD/MM/AAAA"
              className={`${fieldClass} resize-none`}
              data-testid="corr-justificacao"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className={secondaryBtn}>Cancelar</button>
            <button
              type="button"
              onClick={() => onSubmit({ user_id: voter.id, voto, justificacao: justificacao.trim() })}
              disabled={!voter || !voto || justificacao.trim().length < 3 || pending}
              className={primaryBtn}
              data-testid="corr-confirm"
            >
              {pending ? 'A registar...' : 'Registar voto'}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ── Painel de resultado (AGREGADO apenas — spec §18) ──────────────────────────
const ResultadoPanel = ({ resultado, listas }) => {
  const porLista = resultado.por_lista || {};
  const letraById = useMemo(() => {
    const m = {};
    listas.forEach((l) => { m[l.id] = l; });
    return m;
  }, [listas]);

  const rows = Object.entries(porLista)
    .map(([listaId, count]) => ({ listaId, count, lista: letraById[listaId] }))
    .sort((a, b) => b.count - a.count);

  return (
    <div className="space-y-4">
      {resultado.empate && (
        <div className="flex items-start gap-2 px-4 py-3 rounded-md bg-[#FFFBEB] ring-1 ring-[#FDE68A]" data-testid="empate-warning">
          <AlertTriangle className="w-4 h-4 text-[#B45309] mt-0.5 shrink-0" aria-hidden="true" />
          <div className="text-sm text-[#B45309]">
            <span className="font-semibold">Empate.</span> É necessária nova eleição.
            {resultado.nova_eleicao_ate && <> Prazo até {formatDate(resultado.nova_eleicao_ate)}.</>}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-md border border-[#E5E7EB] bg-[#F5F5F5] p-3">
          <p className="text-xs text-[#6B7280]">Brancos</p>
          <p className="text-xl font-bold text-grafite">{resultado.brancos ?? 0}</p>
        </div>
        <div className="rounded-md border border-[#E5E7EB] bg-[#F5F5F5] p-3">
          <p className="text-xs text-[#6B7280]">Nulos</p>
          <p className="text-xl font-bold text-grafite">{resultado.nulos ?? 0}</p>
        </div>
        <div className="rounded-md border border-[#E5E7EB] bg-[#F5F5F5] p-3">
          <p className="text-xs text-[#6B7280]">Votos válidos</p>
          <p className="text-xl font-bold text-grafite">{resultado.total_validos ?? 0}</p>
        </div>
        <div className="rounded-md border border-[#E5E7EB] bg-[#F5F5F5] p-3">
          <p className="text-xs text-[#6B7280]">Total boletins</p>
          <p className="text-xl font-bold text-grafite">{resultado.total_boletins ?? 0}</p>
        </div>
      </div>

      <div className="space-y-2">
        {rows.length === 0 ? (
          <p className="text-sm text-[#6B7280]">Sem votos por lista.</p>
        ) : rows.map(({ listaId, count, lista }) => {
          const winner = resultado.vencedora === listaId && !resultado.empate;
          return (
            <div
              key={listaId}
              className={`flex items-center justify-between px-4 py-3 rounded-md border ${winner ? 'border-[#BBF7D0] bg-[#F0FDF4]' : 'border-[#E5E7EB] bg-white'}`}
              data-testid={`resultado-lista-${listaId}`}
            >
              <span className="flex items-center gap-2 text-sm text-grafite">
                {winner && <Trophy className="w-4 h-4 text-[#15803D]" aria-hidden="true" />}
                <span className="font-semibold">Lista {lista?.letra || '?'}</span>
                {lista?.nome && <span className="text-[#6B7280]">{lista.nome}</span>}
                {winner && <span className="text-xs font-semibold text-[#15803D]">Vencedora</span>}
              </span>
              <span className={`text-lg font-bold ${winner ? 'text-[#15803D]' : 'text-grafite'}`}>{count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ── Painel de detalhe ─────────────────────────────────────────────────────────
const EleicaoDetail = ({ eleicaoId, structure, canManage, isVotingMember, qc }) => {
  const [submeterOpen, setSubmeterOpen] = useState(false);
  const [votarOpen, setVotarOpen] = useState(false);
  const [corrOpen, setCorrOpen] = useState(false);
  const [validarLista, setValidarLista] = useState(null);

  const { data: detail, isLoading } = useQuery({
    queryKey: queryKeys.eleicoes.byId(eleicaoId),
    queryFn: async () => (await eleicoesAPI.get(eleicaoId)).data,
    enabled: !!eleicaoId,
  });

  const { data: listasResp } = useQuery({
    queryKey: queryKeys.eleicoes.listas(eleicaoId),
    queryFn: async () => (await eleicoesAPI.listas(eleicaoId)).data,
    enabled: !!eleicaoId,
  });

  const listas = listasResp?.listas || [];
  const slots = detail?.slots || [];
  const status = detail?.status;
  const resultado = detail?.resultado || {};

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['eleicoes'] });
  };

  const submitListaMutation = useMutation({
    mutationFn: (data) => eleicoesAPI.submitLista(eleicaoId, data),
    onSuccess: () => { toast.success('Lista submetida.'); setSubmeterOpen(false); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao submeter a lista'),
  });

  const validarMutation = useMutation({
    mutationFn: ({ listaId, data }) => eleicoesAPI.validarLista(eleicaoId, listaId, data),
    onSuccess: () => { toast.success('Lista validada.'); setValidarLista(null); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao validar a lista'),
  });

  const abrirMutation = useMutation({
    mutationFn: () => eleicoesAPI.abrirVotacao(eleicaoId),
    onSuccess: () => { toast.success('Votação aberta.'); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao abrir a votação'),
  });

  const votarMutation = useMutation({
    mutationFn: (data) => eleicoesAPI.votar(eleicaoId, data),
    onSuccess: () => { toast.success('Voto registado.'); setVotarOpen(false); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao registar o voto'),
  });

  const corrMutation = useMutation({
    mutationFn: (data) => eleicoesAPI.votoCorrespondencia(eleicaoId, data),
    onSuccess: () => { toast.success('Voto por correspondência registado.'); setCorrOpen(false); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao registar o voto'),
  });

  const apurarMutation = useMutation({
    mutationFn: () => eleicoesAPI.apurar(eleicaoId),
    onSuccess: () => { toast.success('Eleição apurada.'); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao apurar a eleição'),
  });

  const proclamarMutation = useMutation({
    mutationFn: () => eleicoesAPI.proclamar(eleicaoId),
    onSuccess: (res) => { toast.success(res.data?.message || 'Eleição proclamada.'); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao proclamar a eleição'),
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-24 w-full rounded-lg" />
        <Skeleton className="h-40 w-full rounded-lg" />
      </div>
    );
  }
  if (!detail) return null;

  const showResultado = status === 'apurada' || status === 'proclamada';
  const canProclamar = status === 'apurada' && resultado.vencedora && !resultado.empate;
  const canVotar = isVotingMember && status === 'votacao';

  return (
    <div className="space-y-5">
      {/* Resumo */}
      <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-bold text-grafite">Eleição {detail.ano}</h2>
            <StatusBadge status={status} />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {canVotar && (
              <button type="button" onClick={() => setVotarOpen(true)} className={primaryBtn} data-testid="votar-btn">
                <Vote className="w-4 h-4 inline -mt-0.5 mr-1.5" aria-hidden="true" />Votar
              </button>
            )}
            {canManage && status === 'candidaturas' && (
              <>
                <button type="button" onClick={() => setSubmeterOpen(true)} className={secondaryBtn} data-testid="submeter-lista-btn">
                  Submeter lista
                </button>
                <button
                  type="button"
                  onClick={() => abrirMutation.mutate()}
                  disabled={abrirMutation.isPending}
                  className={primaryBtn}
                  data-testid="abrir-votacao-btn"
                >
                  {abrirMutation.isPending ? 'A abrir...' : 'Abrir votação'}
                </button>
              </>
            )}
            {canManage && status === 'votacao' && (detail.modo_votacao === 'correspondencia' || detail.modo_votacao === 'hibrido') && (
              <button type="button" onClick={() => setCorrOpen(true)} className={secondaryBtn} data-testid="voto-corr-btn">
                Voto por correspondência
              </button>
            )}
            {canManage && status === 'votacao' && (
              <button
                type="button"
                onClick={() => apurarMutation.mutate()}
                disabled={apurarMutation.isPending}
                className={secondaryBtn}
                data-testid="apurar-btn"
              >
                {apurarMutation.isPending ? 'A apurar...' : 'Apurar'}
              </button>
            )}
            {canManage && canProclamar && (
              <button
                type="button"
                onClick={() => proclamarMutation.mutate()}
                disabled={proclamarMutation.isPending}
                className={primaryBtn}
                data-testid="proclamar-btn"
              >
                {proclamarMutation.isPending ? 'A proclamar...' : 'Proclamar'}
              </button>
            )}
          </div>
        </div>

        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          <div>
            <dt className="text-xs text-[#6B7280] flex items-center gap-1"><Vote className="w-3.5 h-3.5" aria-hidden="true" />Modo</dt>
            <dd className="text-grafite font-medium">{MODO_LABELS[detail.modo_votacao] || detail.modo_votacao || '—'}</dd>
          </div>
          <div>
            <dt className="text-xs text-[#6B7280] flex items-center gap-1"><CalendarRange className="w-3.5 h-3.5" aria-hidden="true" />Mandato</dt>
            <dd className="text-grafite font-medium">{formatDate(detail.mandato_inicio)} – {formatDate(detail.mandato_fim)}</dd>
          </div>
          <div>
            <dt className="text-xs text-[#6B7280] flex items-center gap-1"><Layers className="w-3.5 h-3.5" aria-hidden="true" />Lugares</dt>
            <dd className="text-grafite font-medium">{slots.length}</dd>
          </div>
          <div>
            <dt className="text-xs text-[#6B7280] flex items-center gap-1"><ListChecks className="w-3.5 h-3.5" aria-hidden="true" />Listas</dt>
            <dd className="text-grafite font-medium">{listas.length}</dd>
          </div>
        </dl>
      </div>

      {/* Listas */}
      <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6">
        <h3 className="text-sm font-semibold text-grafite mb-3">Listas candidatas</h3>
        {listas.length === 0 ? (
          <p className="text-sm text-[#6B7280]">Ainda não há listas submetidas.</p>
        ) : (
          <div className="space-y-2">
            {listas.map((l) => {
              const es = ESTADO_LISTA_STYLE[l.estado] || ESTADO_LISTA_STYLE.submetida;
              return (
                <div key={l.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 rounded-md border border-[#E5E7EB]" data-testid={`lista-${l.id}`}>
                  <div className="min-w-0">
                    <span className="text-sm text-grafite">
                      <span className="font-semibold">Lista {l.letra}</span>
                      {l.nome && <span className="text-[#6B7280] ml-2">{l.nome}</span>}
                    </span>
                    <span className="block text-xs text-[#6B7280]">{(l.candidatos || []).length} candidatos</span>
                    {l.estado === 'rejeitada' && l.rejeicao_motivo && (
                      <span className="block text-xs text-[#B91C1C] mt-0.5">{l.rejeicao_motivo}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${es.bg} ${es.fg}`}>
                      {l.estado === 'aceite' && <CheckCircle2 className="w-3 h-3" aria-hidden="true" />}
                      {l.estado === 'rejeitada' && <XCircle className="w-3 h-3" aria-hidden="true" />}
                      {es.label}
                    </span>
                    {canManage && status === 'candidaturas' && l.estado === 'submetida' && (
                      <button
                        type="button"
                        onClick={() => setValidarLista(l)}
                        className={secondaryBtn + ' !px-3 !py-1 text-xs'}
                        data-testid={`validar-lista-${l.id}`}
                      >
                        Validar
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Resultado (agregado apenas) */}
      {showResultado && (
        <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-6">
          <h3 className="text-sm font-semibold text-grafite mb-3 flex items-center gap-2">
            <Trophy className="w-4 h-4 text-[#15803D]" aria-hidden="true" />Resultado
          </h3>
          <ResultadoPanel resultado={resultado} listas={listas} />
        </div>
      )}

      {/* Modais */}
      <SubmeterListaModal
        open={submeterOpen}
        onClose={() => setSubmeterOpen(false)}
        onSubmit={(data) => submitListaMutation.mutate(data)}
        pending={submitListaMutation.isPending}
        slots={slots}
        structure={structure}
      />
      <VotarModal
        open={votarOpen}
        onClose={() => setVotarOpen(false)}
        onSubmit={(data) => votarMutation.mutate(data)}
        pending={votarMutation.isPending}
        listas={listas}
      />
      <VotoCorrespondenciaModal
        open={corrOpen}
        onClose={() => setCorrOpen(false)}
        onSubmit={(data) => corrMutation.mutate(data)}
        pending={corrMutation.isPending}
        listas={listas}
      />
      <ValidarListaModal
        lista={validarLista}
        structure={structure}
        onClose={() => setValidarLista(null)}
        onSubmit={(data) => validarMutation.mutate({ listaId: validarLista.id, data })}
        pending={validarMutation.isPending}
      />
    </div>
  );
};

export const AdminEleicoesPage = () => {
  const qc = useQueryClient();
  const { isAdmin, isMesaAG, isVotingMember } = useAuth();
  const canManage = isAdmin || isMesaAG;

  const [selectedId, setSelectedId] = useState(null);
  const [criarOpen, setCriarOpen] = useState(false);

  const { data: structure } = useQuery({
    queryKey: queryKeys.governance.structure(),
    queryFn: async () => (await governanceAPI.structure()).data,
    staleTime: 60 * 60 * 1000,
  });

  const { data: listResp, isLoading } = useQuery({
    queryKey: queryKeys.eleicoes.list(),
    queryFn: async () => (await eleicoesAPI.list()).data,
  });

  const eleicoes = useMemo(() => listResp?.eleicoes || [], [listResp]);

  // Selecciona a primeira eleição por defeito.
  useEffect(() => {
    if (!selectedId && eleicoes.length > 0) setSelectedId(eleicoes[0].id);
  }, [eleicoes, selectedId]);

  const criarMutation = useMutation({
    mutationFn: (data) => eleicoesAPI.create(data),
    onSuccess: (res) => {
      toast.success('Eleição criada.');
      setCriarOpen(false);
      qc.invalidateQueries({ queryKey: ['eleicoes'] });
      const newId = res.data?.id;
      if (newId) setSelectedId(newId);
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao criar a eleição'),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-carmesim/10 flex items-center justify-center">
            <Vote className="w-5 h-5 text-carmesim" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-grafite">Eleições</h1>
            <p className="text-sm text-[#6B7280]">Listas, votação e apuramento dos órgãos sociais. O voto é secreto.</p>
          </div>
        </div>
        {canManage && (
          <button type="button" onClick={() => setCriarOpen(true)} className={primaryBtn} data-testid="criar-eleicao-btn">
            <Plus className="w-4 h-4 inline -mt-0.5 mr-1.5" aria-hidden="true" />Criar eleição
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
          <div className="space-y-2">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}</div>
          <Skeleton className="h-64 w-full rounded-lg" />
        </div>
      ) : eleicoes.length === 0 ? (
        <EmptyState icon={ListChecks} title="Sem eleições" description="Ainda não foi criada nenhuma eleição." testId="no-eleicoes" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6 items-start">
          {/* Master: lista de eleições */}
          <nav className="space-y-2" aria-label="Eleições">
            {eleicoes.map((e) => {
              const active = e.id === selectedId;
              return (
                <button
                  key={e.id}
                  type="button"
                  onClick={() => setSelectedId(e.id)}
                  className={`w-full text-left rounded-lg border p-4 transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 ${active ? 'border-carmesim bg-carmesim/5' : 'border-[#E5E7EB] bg-white hover:bg-[#F5F5F5]'}`}
                  data-testid={`eleicao-item-${e.id}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-1.5 text-sm font-semibold text-grafite">
                      <Hash className="w-3.5 h-3.5 text-[#6B7280]" aria-hidden="true" />Eleição {e.ano}
                    </span>
                  </div>
                  <div className="mt-2"><StatusBadge status={e.status} /></div>
                </button>
              );
            })}
          </nav>

          {/* Detail */}
          <div>
            {selectedId ? (
              <EleicaoDetail
                eleicaoId={selectedId}
                structure={structure}
                canManage={canManage}
                isVotingMember={isVotingMember}
                qc={qc}
              />
            ) : (
              <EmptyState icon={Vote} title="Selecione uma eleição" testId="no-selection" />
            )}
          </div>
        </div>
      )}

      <CriarEleicaoModal
        open={criarOpen}
        onClose={() => setCriarOpen(false)}
        onSubmit={(data) => criarMutation.mutate(data)}
        pending={criarMutation.isPending}
      />
    </div>
  );
};

export default AdminEleicoesPage;
