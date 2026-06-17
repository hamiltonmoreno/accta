import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { comunicadosAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { ROLE_LABELS } from '../../lib/cargoLabels';
import { MEMBER_CATEGORY_LABELS } from '../../lib/governanceLabels';
import { toast } from 'sonner';
import { Megaphone } from 'lucide-react';
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from '../../components/ui/card';

import { ORGAO_SEGMENT_LABELS, useDebounced } from './comunicados/tokens';
import { HistoryTable } from './comunicados/HistoryTable';
import { ComposerCard } from './comunicados/ComposerCard';
import { PreviewCard } from './comunicados/PreviewCard';
import { ConfirmDialog } from './comunicados/ConfirmDialog';

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
          <ComposerCard
            subject={subject} setSubject={setSubject}
            body={body} setBody={setBody}
            tipo={tipo} setTipo={setTipo}
            channels={channels} toggleChannel={toggleChannel}
            segKind={segKind} setSegKind={setSegKind}
            segValue={segValue} setSegValue={setSegValue}
            userIds={userIds} toggleUser={toggleUser}
            ctaLabel={ctaLabel} setCtaLabel={setCtaLabel}
            ctaUrl={ctaUrl} setCtaUrl={setCtaUrl}
            ctaUrlValid={ctaUrlValid}
            valueOptions={valueOptions}
          />
        </div>

        {/* Pré-visualização + contagem + disparar */}
        <div className="space-y-6">
          <PreviewCard
            subject={subject} body={body}
            ctaLabel={ctaLabel} ctaUrl={ctaUrl} ctaUrlValid={ctaUrlValid}
            channels={channels} segmentReady={segmentReady}
            countingRecipients={countingRecipients}
            inApp={inApp} emailCount={emailCount}
            validationError={validationError}
            canSubmit={canSubmit}
            pending={createMutation.isPending}
            onSubmitClick={handleSubmitClick}
          />
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

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        onConfirm={handleConfirmSend}
        segmentReady={segmentReady}
        countingRecipients={countingRecipients}
        recipientsTotal={recipientsTotal}
        inApp={inApp}
        emailCount={emailCount}
      />
    </div>
  );
}

export default AdminComunicadosPage;
