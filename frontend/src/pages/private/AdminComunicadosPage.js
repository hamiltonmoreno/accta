import React, { useState, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { comunicadosAPI, usersAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { ROLE_LABELS } from '../../lib/cargoLabels';
import { MEMBER_CATEGORY_LABELS } from '../../lib/governanceLabels';
import { toast } from 'sonner';
import {
  Megaphone, Send, Users, Mail, Bell, Search, ExternalLink,
  ChevronLeft, ChevronRight, CheckCircle2, XCircle, Clock, Loader2,
} from 'lucide-react';
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Label } from '../../components/ui/label';
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem,
} from '../../components/ui/select';
import { Checkbox } from '../../components/ui/checkbox';
import { Badge } from '../../components/ui/badge';
import {
  Table, TableHeader, TableBody, TableHead, TableRow, TableCell,
} from '../../components/ui/table';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel,
  AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
  AlertDialogHeader, AlertDialogTitle,
} from '../../components/ui/alert-dialog';
import { Skeleton } from '../../components/ui/skeleton';
import { EmptyState } from '../../components/EmptyState';

const PAGE_SIZE = 20;

// Rótulos PT para as chaves de órgão devolvidas por /comunicados/segments
// (mesa_ag/direcao/conselho_fiscal — distintas das chaves de ORGAO_LABELS).
const ORGAO_SEGMENT_LABELS = {
  mesa_ag: 'Mesa da Assembleia Geral',
  direcao: 'Direcção',
  conselho_fiscal: 'Conselho Fiscal',
};

const TIPO_LABELS = { informativo: 'Informativo', oficial: 'Oficial' };

const SEGMENT_KIND_LABELS = {
  all_active: 'Todos os sócios ativos',
  role: 'Por função',
  member_category: 'Por categoria',
  orgao: 'Por órgão social',
  manual: 'Seleção manual',
};

const CHANNEL_LABELS = { in_app: 'Notificação na app', email: 'E-mail' };

// Estados do dispatch -> aparência neutra; Carmesim só no estado de falha.
const STATUS_CONFIG = {
  a_enviar: { label: 'A enviar', icon: Clock, className: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
  enviado: { label: 'Enviado', icon: CheckCircle2, className: 'bg-[#F0FDF4] text-[#15803D] border-[#15803D]/30' },
  parcial: { label: 'Parcial', icon: Clock, className: 'bg-[#FFFBEB] text-[#B45309] border-[#B45309]/30' },
  falhado: { label: 'Falhado', icon: XCircle, className: 'bg-[#FEF2F2] text-[#B91C1C] border-[#C7202F]/40' },
};

const formatDate = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('pt-PT', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return '—';
  }
};

// debounce simples para um valor (usado na contagem de destinatários).
function useDebounced(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

// ──────────────────────────────────────────────────────────────────────────
// Seletor de sócios (segmento manual)
// ──────────────────────────────────────────────────────────────────────────
function MemberSelector({ selectedIds, onToggle }) {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounced(search, 300);

  const { data: members = [], isLoading } = useQuery({
    queryKey: queryKeys.users.list({ search: debouncedSearch, scope: 'comunicados' }),
    queryFn: async () => {
      const params = { status: 'ativo', limit: 50 };
      if (debouncedSearch) params.search = debouncedSearch;
      return (await usersAPI.getAll(params)).data;
    },
  });

  return (
    <div className="space-y-2">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" aria-hidden="true" />
        <Input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Procurar sócio por nome ou e-mail…"
          className="pl-9"
          aria-label="Procurar sócio"
          data-testid="comunicado-member-search"
        />
      </div>

      <div className="border border-[#E5E7EB] rounded-md max-h-60 overflow-y-auto divide-y divide-[#E5E7EB]">
        {isLoading ? (
          <div className="p-3 space-y-2">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-9 w-full rounded-md" />)}
          </div>
        ) : members.length === 0 ? (
          <p className="p-4 text-sm text-[#6B7280] text-center">Nenhum sócio encontrado.</p>
        ) : (
          members.map((m) => {
            const checked = selectedIds.includes(m.id);
            return (
              <label
                key={m.id}
                className="flex items-center gap-3 px-3 py-2 hover:bg-[#F5F5F5] cursor-pointer transition-colors"
                data-testid={`comunicado-member-${m.id}`}
              >
                <Checkbox checked={checked} onCheckedChange={() => onToggle(m.id)} />
                <span className="min-w-0 flex-1">
                  <span className="block text-sm text-grafite truncate">{m.name || 'Sem nome'}</span>
                  <span className="block text-xs text-[#6B7280] truncate">{m.email}</span>
                </span>
              </label>
            );
          })
        )}
      </div>

      <p className="text-xs text-[#6B7280]">
        {selectedIds.length} sócio(s) selecionado(s).
      </p>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Histórico de comunicados
// ──────────────────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || {
    label: status || '—', icon: Clock, className: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]',
  };
  const Icon = cfg.icon;
  return (
    <Badge variant="outline" className={`gap-1 font-medium ${cfg.className}`}>
      <Icon className="w-3 h-3" aria-hidden="true" />
      {cfg.label}
    </Badge>
  );
}

function segmentDescription(seg) {
  if (!seg) return '—';
  const base = SEGMENT_KIND_LABELS[seg.kind] || seg.kind;
  if (seg.kind === 'role') return `${base}: ${ROLE_LABELS[seg.value] || seg.value}`;
  if (seg.kind === 'member_category') return `${base}: ${MEMBER_CATEGORY_LABELS[seg.value] || seg.value}`;
  if (seg.kind === 'orgao') return `${base}: ${ORGAO_SEGMENT_LABELS[seg.value] || seg.value}`;
  if (seg.kind === 'manual') return `${base} (${(seg.user_ids || []).length})`;
  return base;
}

function HistoryTable() {
  const [page, setPage] = useState(0);
  const skip = page * PAGE_SIZE;

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.comunicados.list({ skip, limit: PAGE_SIZE }),
    queryFn: async () => (await comunicadosAPI.list({ skip, limit: PAGE_SIZE })).data,
    staleTime: 15 * 1000,
  });

  const items = data?.items || [];
  const total = data?.total ?? 0;
  const hasNext = skip + items.length < total;

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12 w-full rounded-md" />)}
      </div>
    );
  }

  if (isError) {
    return (
      <EmptyState
        icon={XCircle}
        title="Não foi possível carregar o histórico"
        description="Tente novamente dentro de momentos."
        testId="comunicados-history-error"
      />
    );
  }

  if (items.length === 0 && page === 0) {
    return (
      <EmptyState
        icon={Megaphone}
        title="Ainda não há comunicados"
        description="Os comunicados que enviar aparecerão aqui."
        testId="comunicados-history-empty"
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Assunto</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Canais</TableHead>
            <TableHead>Segmento</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead className="text-right">E-mail (env./falh.)</TableHead>
            <TableHead className="text-right">Na app</TableHead>
            <TableHead>Data</TableHead>
            <TableHead>Autor</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((c) => (
            <TableRow key={c.id} className="hover:bg-[#F5F5F5]" data-testid={`comunicado-row-${c.id}`}>
              <TableCell className="font-medium text-grafite max-w-[16rem] truncate" title={c.subject}>
                {c.subject}
              </TableCell>
              <TableCell className="text-[#6B7280]">{TIPO_LABELS[c.tipo] || c.tipo}</TableCell>
              <TableCell className="text-[#6B7280]">
                {(c.channels || []).map((ch) => CHANNEL_LABELS[ch] || ch).join(' · ')}
              </TableCell>
              <TableCell className="text-[#6B7280] max-w-[12rem] truncate" title={segmentDescription(c.segment)}>
                {segmentDescription(c.segment)}
              </TableCell>
              <TableCell><StatusBadge status={c.status} /></TableCell>
              <TableCell className="text-right text-[#6B7280] tabular-nums">
                {c.email_sent ?? 0}
                {(c.email_failed ?? 0) > 0 && (
                  <span className="text-[#B91C1C]"> / {c.email_failed}</span>
                )}
              </TableCell>
              <TableCell className="text-right text-[#6B7280] tabular-nums">{c.inapp_created ?? 0}</TableCell>
              <TableCell className="text-[#6B7280] whitespace-nowrap">{formatDate(c.created_at)}</TableCell>
              <TableCell className="text-[#6B7280] max-w-[10rem] truncate" title={c.created_by}>
                {c.created_by}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {(page > 0 || hasNext) && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-[#E5E7EB]">
          <span className="text-xs text-[#6B7280]">
            {total > 0 ? `${skip + 1}–${skip + items.length} de ${total}` : '—'}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
              data-testid="comunicados-prev-page"
            >
              <ChevronLeft className="w-4 h-4" aria-hidden="true" />
              Anterior
            </button>
            <button
              type="button"
              onClick={() => setPage((p) => p + 1)}
              disabled={!hasNext}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
              data-testid="comunicados-next-page"
            >
              Próxima
              <ChevronRight className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Página
// ──────────────────────────────────────────────────────────────────────────
export function AdminComunicadosPage() {
  const qc = useQueryClient();

  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [tipo, setTipo] = useState('informativo');
  const [channels, setChannels] = useState(['in_app']);
  const [segKind, setSegKind] = useState('all_active');
  const [segValue, setSegValue] = useState('');
  const [userIds, setUserIds] = useState([]);
  const [ctaLabel, setCtaLabel] = useState('');
  const [ctaUrl, setCtaUrl] = useState('');
  const [confirmOpen, setConfirmOpen] = useState(false);

  // Contagens por segmento (popula os pickers de valor).
  const { data: segments } = useQuery({
    queryKey: queryKeys.comunicados.segments(),
    queryFn: async () => (await comunicadosAPI.segments()).data,
    staleTime: 5 * 60 * 1000,
  });

  const toggleChannel = (ch) => {
    setChannels((prev) => (prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch]));
  };

  const toggleUser = (id) => {
    setUserIds((prev) => (prev.includes(id) ? prev.filter((u) => u !== id) : [...prev, id]));
  };

  // Constrói o objeto de segmento para a API.
  const segment = useMemo(() => {
    if (segKind === 'manual') return { kind: 'manual', value: null, user_ids: userIds };
    if (segKind === 'all_active') return { kind: 'all_active', value: null, user_ids: null };
    return { kind: segKind, value: segValue || null, user_ids: null };
  }, [segKind, segValue, userIds]);

  // Segmento coerente o suficiente para pedir a contagem ao backend.
  const segmentReady = useMemo(() => {
    if (segKind === 'all_active') return true;
    if (segKind === 'manual') return userIds.length > 0;
    return !!segValue;
  }, [segKind, segValue, userIds]);

  // ── Contagem ao vivo de destinatários (debounce ~400ms) ──
  const countKey = useMemo(
    () => JSON.stringify({ tipo, channels, segment }),
    [tipo, channels, segment],
  );
  const debouncedCountKey = useDebounced(countKey, 400);

  const { data: recipients, isFetching: countingRecipients } = useQuery({
    queryKey: queryKeys.comunicados.recipientsCount(debouncedCountKey),
    queryFn: async () => {
      const { tipo: t, channels: ch, segment: seg } = JSON.parse(debouncedCountKey);
      return (await comunicadosAPI.recipientsCount({ tipo: t, channels: ch, segment: seg })).data;
    },
    enabled: channels.length > 0 && segmentReady,
    staleTime: 30 * 1000,
  });

  const createMutation = useMutation({
    mutationFn: (payload) => comunicadosAPI.create(payload),
    onSuccess: (res) => {
      toast.success(`Comunicado em envio para ${res.data?.recipients_total ?? 0} destinatário(s).`);
      // Reset do compositor.
      setSubject('');
      setBody('');
      setTipo('informativo');
      setChannels(['in_app']);
      setSegKind('all_active');
      setSegValue('');
      setUserIds([]);
      setCtaLabel('');
      setCtaUrl('');
      qc.invalidateQueries({ queryKey: ['comunicados'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao enviar o comunicado'),
  });

  // Validação cliente (espelha as regras do backend).
  const ctaUrlValid = !ctaUrl || /^https?:\/\//.test(ctaUrl.trim());
  const validationError = useMemo(() => {
    if (!subject.trim()) return 'Indique o assunto.';
    if (body.trim().length < 10) return 'O corpo deve ter pelo menos 10 caracteres.';
    if (channels.length === 0) return 'Selecione pelo menos um canal.';
    if (!segmentReady) {
      return segKind === 'manual'
        ? 'Selecione pelo menos um sócio.'
        : 'Escolha um valor para o segmento.';
    }
    if (!ctaUrlValid) return 'O URL do botão deve começar por http:// ou https://.';
    return null;
  }, [subject, body, channels, segmentReady, segKind, ctaUrlValid]);

  const canSubmit = !validationError && !createMutation.isPending;

  const handleSubmitClick = () => {
    if (validationError) {
      toast.error(validationError);
      return;
    }
    setConfirmOpen(true);
  };

  const handleConfirmSend = () => {
    setConfirmOpen(false);
    createMutation.mutate({
      subject: subject.trim(),
      body: body.trim(),
      tipo,
      channels,
      segment,
      cta_label: ctaLabel.trim() || null,
      cta_url: ctaUrl.trim() || null,
    });
  };

  const inApp = recipients?.in_app ?? 0;
  const emailCount = recipients?.email ?? 0;
  const recipientsTotal = recipients?.total ?? Math.max(inApp, emailCount);

  // Opções para o picker de valor do segmento.
  const valueOptions = useMemo(() => {
    if (!segments) return [];
    if (segKind === 'role') {
      return Object.entries(segments.roles || {})
        .filter(([k]) => k)
        .map(([k, n]) => ({ value: k, label: `${ROLE_LABELS[k] || k} (${n})` }));
    }
    if (segKind === 'member_category') {
      return Object.entries(segments.member_categories || {})
        .filter(([k]) => k)
        .map(([k, n]) => ({ value: k, label: `${MEMBER_CATEGORY_LABELS[k] || k} (${n})` }));
    }
    if (segKind === 'orgao') {
      return Object.entries(segments.orgaos || {})
        .map(([k, n]) => ({ value: k, label: `${ORGAO_SEGMENT_LABELS[k] || k} (${n})` }));
    }
    return [];
  }, [segments, segKind]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-carmesim/10 flex items-center justify-center">
          <Megaphone className="w-5 h-5 text-carmesim" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-grafite">Comunicados</h1>
          <p className="text-sm text-[#6B7280]">
            Componha e envie comunicados aos sócios por notificação na app e/ou e-mail.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {/* Compositor */}
        <div className="xl:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-grafite">Novo comunicado</CardTitle>
              <CardDescription>Preencha os campos e reveja antes de disparar.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* Assunto */}
              <div className="space-y-1.5">
                <Label htmlFor="comunicado-subject">Assunto</Label>
                <Input
                  id="comunicado-subject"
                  value={subject}
                  maxLength={200}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="Ex.: Convocatória da Assembleia Geral Ordinária"
                  data-testid="comunicado-subject"
                />
              </div>

              {/* Corpo */}
              <div className="space-y-1.5">
                <Label htmlFor="comunicado-body">Corpo da mensagem</Label>
                <Textarea
                  id="comunicado-body"
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  rows={6}
                  placeholder="Escreva o conteúdo do comunicado…"
                  data-testid="comunicado-body"
                />
                <p className="text-xs text-[#6B7280]">Mínimo 10 caracteres. As quebras de parágrafo são preservadas.</p>
              </div>

              {/* Tipo */}
              <div className="space-y-1.5">
                <Label htmlFor="comunicado-tipo">Tipo</Label>
                <Select value={tipo} onValueChange={setTipo}>
                  <SelectTrigger id="comunicado-tipo" data-testid="comunicado-tipo">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="informativo">Informativo</SelectItem>
                    <SelectItem value="oficial">Oficial</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-[#6B7280]">
                  {tipo === 'oficial'
                    ? 'Oficial: chega a todos os destinatários, ignorando as preferências de opt-out.'
                    : 'Informativo: respeita o opt-out de e-mails de cada sócio.'}
                </p>
              </div>

              {/* Canais */}
              <div className="space-y-2">
                <Label>Canais</Label>
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={channels.includes('in_app')}
                      onCheckedChange={() => toggleChannel('in_app')}
                      data-testid="comunicado-channel-in_app"
                    />
                    <span className="inline-flex items-center gap-1.5 text-sm text-grafite">
                      <Bell className="w-4 h-4 text-[#6B7280]" aria-hidden="true" />
                      Notificação na app
                    </span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={channels.includes('email')}
                      onCheckedChange={() => toggleChannel('email')}
                      data-testid="comunicado-channel-email"
                    />
                    <span className="inline-flex items-center gap-1.5 text-sm text-grafite">
                      <Mail className="w-4 h-4 text-[#6B7280]" aria-hidden="true" />
                      E-mail
                    </span>
                  </label>
                </div>
                {channels.length === 0 && (
                  <p className="text-xs text-[#B91C1C]">Selecione pelo menos um canal.</p>
                )}
              </div>

              {/* Segmento */}
              <div className="space-y-1.5">
                <Label htmlFor="comunicado-segment">Destinatários</Label>
                <Select
                  value={segKind}
                  onValueChange={(v) => { setSegKind(v); setSegValue(''); }}
                >
                  <SelectTrigger id="comunicado-segment" data-testid="comunicado-segment">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(SEGMENT_KIND_LABELS).map(([k, label]) => (
                      <SelectItem key={k} value={k}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {(segKind === 'role' || segKind === 'member_category' || segKind === 'orgao') && (
                  <div className="pt-1">
                    <Select value={segValue} onValueChange={setSegValue}>
                      <SelectTrigger data-testid="comunicado-segment-value">
                        <SelectValue placeholder="Escolha um valor…" />
                      </SelectTrigger>
                      <SelectContent>
                        {valueOptions.map((o) => (
                          <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                {segKind === 'manual' && (
                  <div className="pt-1">
                    <MemberSelector selectedIds={userIds} onToggle={toggleUser} />
                  </div>
                )}
              </div>

              {/* CTA opcional */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="comunicado-cta-label">Botão (texto) — opcional</Label>
                  <Input
                    id="comunicado-cta-label"
                    value={ctaLabel}
                    onChange={(e) => setCtaLabel(e.target.value)}
                    placeholder="Ex.: Ver convocatória"
                    data-testid="comunicado-cta-label"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="comunicado-cta-url">Botão (URL) — opcional</Label>
                  <Input
                    id="comunicado-cta-url"
                    value={ctaUrl}
                    onChange={(e) => setCtaUrl(e.target.value)}
                    placeholder="https://…"
                    aria-invalid={!ctaUrlValid}
                    data-testid="comunicado-cta-url"
                  />
                  {!ctaUrlValid && (
                    <p className="text-xs text-[#B91C1C]">Deve começar por http:// ou https://.</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Pré-visualização + contagem + disparar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-grafite">Pré-visualização</CardTitle>
              <CardDescription>Como o sócio verá o comunicado.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg border border-[#E5E7EB] bg-[#F5F5F5] p-4">
                <h3 className="font-semibold text-grafite break-words">
                  {subject || 'Assunto do comunicado'}
                </h3>
                <div className="mt-2 space-y-2 text-sm text-grafite">
                  {(body || 'O corpo da mensagem aparecerá aqui.')
                    .split('\n')
                    .map((para, i) => (
                      <p key={i} className="break-words whitespace-pre-wrap">{para || ' '}</p>
                    ))}
                </div>
                {ctaLabel && ctaUrl && ctaUrlValid && (
                  <a
                    href={ctaUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 inline-flex items-center gap-1.5 px-4 py-2 rounded-md bg-carmesim text-white text-sm font-semibold hover:bg-[#A51B27] transition-colors focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                  >
                    {ctaLabel}
                    <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
                  </a>
                )}
              </div>

              {/* Contagem ao vivo */}
              <div className="rounded-lg border border-[#E5E7EB] p-3">
                <div className="flex items-center gap-2 text-sm text-[#6B7280]">
                  <Users className="w-4 h-4" aria-hidden="true" />
                  {channels.length === 0 || !segmentReady ? (
                    <span>Selecione canais e destinatários para ver o alcance.</span>
                  ) : countingRecipients ? (
                    <span className="inline-flex items-center gap-1.5">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
                      A calcular…
                    </span>
                  ) : (
                    <span>
                      Vai para <strong className="text-grafite tabular-nums">{inApp}</strong> na app
                      {' · '}
                      <strong className="text-grafite tabular-nums">{emailCount}</strong> por e-mail
                    </span>
                  )}
                </div>
              </div>

              {validationError && (
                <p className="text-xs text-[#B91C1C]" data-testid="comunicado-validation">{validationError}</p>
              )}

              {/* O ÚNICO botão primário (Carmesim) da vista */}
              <button
                type="button"
                onClick={handleSubmitClick}
                disabled={!canSubmit}
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-carmesim text-white font-semibold hover:bg-[#A51B27] transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                data-testid="comunicado-submit"
              >
                {createMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Send className="w-4 h-4" aria-hidden="true" />
                )}
                {createMutation.isPending ? 'A disparar…' : 'Disparar comunicado'}
              </button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Histórico */}
      <Card>
        <CardHeader>
          <CardTitle className="text-grafite">Histórico</CardTitle>
          <CardDescription>Comunicados enviados, do mais recente ao mais antigo.</CardDescription>
        </CardHeader>
        <CardContent>
          <HistoryTable />
        </CardContent>
      </Card>

      {/* Confirmação de envio */}
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar envio</AlertDialogTitle>
            <AlertDialogDescription>
              {segmentReady && !countingRecipients
                ? `Vai enviar este comunicado a ${recipientsTotal} destinatário(s) (${inApp} na app · ${emailCount} por e-mail). Esta ação não pode ser anulada.`
                : 'Vai enviar este comunicado. Esta ação não pode ser anulada.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="comunicado-confirm-cancel">Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmSend}
              className="bg-carmesim text-white hover:bg-[#A51B27]"
              data-testid="comunicado-confirm-send"
            >
              Enviar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export default AdminComunicadosPage;
