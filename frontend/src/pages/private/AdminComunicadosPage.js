import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { comunicadosAPI, governanceAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import { ROLE_LABELS } from '../../lib/cargoLabels';
import { MEMBER_CATEGORY_LABELS } from '../../lib/governanceLabels';
import { toast } from 'sonner';
import { Megaphone } from 'lucide-react';
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent,
} from '../../components/ui/card';

import { ORGAO_SEGMENT_LABELS } from './comunicados/tokens';
import { useDebounced } from './comunicados/hooks';
import { HistoryTable } from './comunicados/HistoryTable';
import { ComposerCard } from './comunicados/ComposerCard';
import { PreviewCard } from './comunicados/PreviewCard';
import { ConfirmDialog } from './comunicados/ConfirmDialog';

const EMPTY_AF = {
  orgaos: [], cargos: [], categorias: [], statuses: [],
  joined_after: '', joined_before: '', nominal: '',
};

export function AdminComunicadosPage() {
  const qc = useQueryClient();
  const { can, hasPrivilege } = useAuth();
  // Emissor pleno (admin/send_comunicados) vs. restrito a órgãos (US4): quem só
  // tem `comunicar_intra_orgao` fica trancado ao modo segmentado por órgão.
  const isFullSender = can('send_comunicados');
  const restricted = !isFullSender && hasPrivilege('comunicar_intra_orgao');

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
  // Modo segmentado (spec-comunicados-segmentados). Emissor restrito arranca e
  // permanece em segmentada (só órgãos).
  const [audienceMode, setAudienceMode] = useState(restricted ? 'segmentada' : 'simples');
  const [af, setAf] = useState(EMPTY_AF);
  const [dryRun, setDryRun] = useState(false);
  const segmented = audienceMode === 'segmentada';

  // Contagens por segmento (popula os pickers do modo simples).
  const { data: segments } = useQuery({
    queryKey: queryKeys.comunicados.segments(),
    queryFn: async () => (await comunicadosAPI.segments()).data,
    staleTime: 5 * 60 * 1000,
    enabled: !restricted,  // caminho `segment` é só para emissores plenos (US4)
  });

  // Estrutura de governança (cargos canónicos — FR-012, sem hard-code).
  const { data: structure } = useQuery({
    queryKey: ['governance', 'structure'],
    queryFn: async () => (await governanceAPI.structure()).data,
    staleTime: 10 * 60 * 1000,
    enabled: segmented,
  });

  const cargoOptions = useMemo(
    () => (structure?.cargos || [])
      .filter((c) => c.key && c.key !== 'socio')
      .map((c) => [c.key, c.label || c.key]),
    [structure],
  );
  const categoriaOptions = useMemo(
    () => Object.entries(MEMBER_CATEGORY_LABELS),
    [],
  );

  const toggleChannel = (ch) => {
    setChannels((prev) => (prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch]));
  };

  const toggleUser = (id) => {
    setUserIds((prev) => (prev.includes(id) ? prev.filter((u) => u !== id) : [...prev, id]));
  };

  // ── Modo simples: objeto de segmento ──
  const segment = useMemo(() => {
    if (segKind === 'manual') return { kind: 'manual', value: null, user_ids: userIds };
    if (segKind === 'all_active') return { kind: 'all_active', value: null, user_ids: null };
    return { kind: segKind, value: segValue || null, user_ids: null };
  }, [segKind, segValue, userIds]);

  const segmentReady = useMemo(() => {
    if (segKind === 'all_active') return true;
    if (segKind === 'manual') return userIds.length > 0;
    return !!segValue;
  }, [segKind, segValue, userIds]);

  // ── Modo segmentado: audience_filter (arrays/datas vazias removidas) ──
  const audienceFilter = useMemo(() => {
    const tokens = (af.nominal || '').split(/[\s,;]+/).map((s) => s.trim()).filter(Boolean);
    const nominal_emails = tokens.filter((t) => t.includes('@'));
    const nominal_member_ids = tokens.filter((t) => !t.includes('@'));
    const f = {};
    if (af.orgaos.length) f.orgaos = af.orgaos;
    if (af.cargos.length) f.cargos = af.cargos;
    if (af.categorias.length) f.categorias = af.categorias;
    if (af.statuses.length) f.statuses = af.statuses;
    if (af.joined_after) f.joined_after = af.joined_after;
    if (af.joined_before) f.joined_before = af.joined_before;
    if (nominal_member_ids.length) f.nominal_member_ids = nominal_member_ids;
    if (nominal_emails.length) f.nominal_emails = nominal_emails;
    return f;
  }, [af]);
  const audienceReady = Object.keys(audienceFilter).length > 0;

  // ── Contagem ao vivo, modo simples (debounce ~400ms) ──
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
    enabled: !segmented && channels.length > 0 && segmentReady,
    staleTime: 30 * 1000,
  });

  // ── Preview ao vivo, modo segmentado (debounce ~400ms) ──
  const previewKey = useMemo(
    () => JSON.stringify({ tipo, channels, audience_filter: audienceFilter }),
    [tipo, channels, audienceFilter],
  );
  const debouncedPreviewKey = useDebounced(previewKey, 400);
  const { data: audiencePreview, isFetching: previewing } = useQuery({
    queryKey: queryKeys.comunicados.previewAudience(debouncedPreviewKey),
    queryFn: async () => {
      const { tipo: t, channels: ch, audience_filter: f } = JSON.parse(debouncedPreviewKey);
      return (await comunicadosAPI.previewAudience({ tipo: t, channels: ch, audience_filter: f })).data;
    },
    enabled: segmented && channels.length > 0 && audienceReady,
    staleTime: 30 * 1000,
  });

  const resetComposer = () => {
    setSubject(''); setBody(''); setTipo('informativo'); setChannels(['in_app']);
    setSegKind('all_active'); setSegValue(''); setUserIds([]);
    setCtaLabel(''); setCtaUrl(''); setAf(EMPTY_AF); setDryRun(false);
    qc.invalidateQueries({ queryKey: ['comunicados'] });
  };

  // Modo simples: envio imediato (v1, inalterado).
  const createMutation = useMutation({
    mutationFn: (payload) => comunicadosAPI.create(payload),
    onSuccess: (res) => {
      toast.success(`Comunicado em envio para ${res.data?.recipients_total ?? 0} destinatário(s).`);
      resetComposer();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao enviar o comunicado'),
  });

  // Modo segmentado: cria rascunho e envia (create → enviar).
  const segmentedMutation = useMutation({
    mutationFn: async (payload) => {
      const created = await comunicadosAPI.create(payload);
      const sent = await comunicadosAPI.send(created.data.id);
      return sent.data;
    },
    onSuccess: (res) => {
      toast.success(
        res.dry_run
          ? `Simulação concluída: ${res.recipients_count} destinatário(s) — nada foi enviado.`
          : `Comunicado enviado a ${res.recipients_count} destinatário(s).`,
      );
      resetComposer();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao enviar o comunicado'),
  });

  // Validação cliente (espelha as regras do backend).
  const ctaUrlValid = !ctaUrl || /^https?:\/\//.test(ctaUrl.trim());
  const validationError = useMemo(() => {
    if (!subject.trim()) return 'Indique o assunto.';
    if (body.trim().length < 10) return 'O corpo deve ter pelo menos 10 caracteres.';
    if (channels.length === 0) return 'Selecione pelo menos um canal.';
    if (segmented) {
      if (!audienceReady) return 'Defina pelo menos um critério de audiência.';
      if (audiencePreview && audiencePreview.recipients_count === 0) {
        return 'O filtro não selecciona nenhum sócio — revê os critérios.';
      }
    } else if (!segmentReady) {
      return segKind === 'manual' ? 'Selecione pelo menos um sócio.' : 'Escolha um valor para o segmento.';
    }
    if (!ctaUrlValid) return 'O URL do botão deve começar por http:// ou https://.';
    return null;
  }, [subject, body, channels, segmented, audienceReady, audiencePreview, segmentReady, segKind, ctaUrlValid]);

  const pending = segmented ? segmentedMutation.isPending : createMutation.isPending;
  const canSubmit = !validationError && !pending && (!segmented || (!previewing && !!audiencePreview));

  const handleSubmitClick = () => {
    if (validationError) {
      toast.error(validationError);
      return;
    }
    setConfirmOpen(true);
  };

  const handleConfirmSend = () => {
    setConfirmOpen(false);
    const common = {
      subject: subject.trim(), body: body.trim(), tipo, channels,
      cta_label: ctaLabel.trim() || null, cta_url: ctaUrl.trim() || null,
    };
    if (segmented) {
      segmentedMutation.mutate({ ...common, audience_filter: audienceFilter, dry_run: dryRun });
    } else {
      createMutation.mutate({ ...common, segment });
    }
  };

  const inApp = recipients?.in_app ?? 0;
  const emailCount = recipients?.email ?? 0;
  const recipientsTotal = segmented
    ? (audiencePreview?.recipients_count ?? 0)
    : (recipients?.total ?? Math.max(inApp, emailCount));

  // Opções para o picker de valor do segmento (modo simples).
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
            audienceMode={audienceMode} setAudienceMode={setAudienceMode}
            af={af} setAf={setAf}
            cargoOptions={cargoOptions} categoriaOptions={categoriaOptions}
            dryRun={dryRun} setDryRun={setDryRun} showDryRun
            restricted={restricted}
          />
        </div>

        {/* Pré-visualização + alcance + enviar */}
        <div className="space-y-6">
          <PreviewCard
            subject={subject} body={body}
            ctaLabel={ctaLabel} ctaUrl={ctaUrl} ctaUrlValid={ctaUrlValid}
            channels={channels} segmentReady={segmentReady}
            countingRecipients={countingRecipients}
            inApp={inApp} emailCount={emailCount}
            validationError={validationError}
            canSubmit={canSubmit}
            pending={pending}
            onSubmitClick={handleSubmitClick}
            audienceMode={audienceMode} audienceReady={audienceReady}
            audiencePreview={audiencePreview} previewing={previewing} dryRun={dryRun}
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
        segmentReady={segmented ? audienceReady : segmentReady}
        countingRecipients={segmented ? previewing : countingRecipients}
        recipientsTotal={recipientsTotal}
        inApp={segmented ? recipientsTotal : inApp}
        emailCount={segmented ? recipientsTotal : emailCount}
        dryRun={segmented && dryRun}
      />
    </div>
  );
}

export default AdminComunicadosPage;
