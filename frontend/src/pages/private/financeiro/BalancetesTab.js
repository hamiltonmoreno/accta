import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { balancetesAPI } from '../../../utils/api';
import { useAuth } from '../../../contexts/AuthContext';
import { queryKeys } from '../../../lib/queryClient';
import { ClipboardList, Plus, Loader2, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { EmptyState } from '../../../components/EmptyState';
import { Skeleton } from '../../../components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../../components/ui/dialog';
import { DocumentUploadField } from '../../../components/DocumentUploadField';

const TIPO_LABEL = { periodico: 'Balancete periódico', balanco_anual: 'Balanço anual' };
const fmtCve = (v) => `${Number(v || 0).toLocaleString('pt-PT')} CVE`;
const fmtDate = (d) => (d ? format(new Date(d), 'dd MMM yyyy', { locale: ptBR }) : '');

const anoAtual = new Date().getFullYear();

export const BalancetesTab = () => {
  const qc = useQueryClient();
  const { isAdmin, isConselhoFiscal, canManageFinances } = useAuth();
  const podePublicar = canManageFinances;
  const podeAuditar = isConselhoFiscal || isAdmin;

  const [showPublish, setShowPublish] = useState(false);
  const [form, setForm] = useState({ tipo: 'periodico', periodo: '', exercicio_ano: anoAtual, month: '' });
  const [auditTarget, setAuditTarget] = useState(null); // balancete a auditar
  const [auditForm, setAuditForm] = useState({ conferido: true, observacoes: '' });

  const invalidate = () => qc.invalidateQueries({ queryKey: ['balancetes'] });

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.balancetes.list(),
    queryFn: async () => (await balancetesAPI.list()).data,
  });
  const balancetes = data?.items || [];

  const publishMut = useMutation({
    mutationFn: () =>
      balancetesAPI.publicar({
        tipo: form.tipo,
        periodo: form.periodo.trim(),
        exercicio_ano: Number(form.exercicio_ano),
        month: form.month === '' ? null : Number(form.month),
        document_id: form.document_id || undefined,
      }),
    onSuccess: () => {
      toast.success('Balancete publicado.');
      invalidate();
      setShowPublish(false);
      setForm({ tipo: 'periodico', periodo: '', exercicio_ano: anoAtual, month: '' });
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao publicar balancete'),
  });

  const auditMut = useMutation({
    mutationFn: () => balancetesAPI.auditar(auditTarget.id, { conferido: auditForm.conferido, observacoes: auditForm.observacoes.trim() || null }),
    onSuccess: () => {
      toast.success('Auditoria registada.');
      invalidate();
      setAuditTarget(null);
      setAuditForm({ conferido: true, observacoes: '' });
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao registar auditoria'),
  });

  const renderCard = (b) => {
    const s = b.snapshot || {};
    const audit = b.cf_audit;
    return (
      <div key={b.id} className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-5 space-y-4" data-testid={`balancete-${b.id}`}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="font-semibold text-grafite">{b.periodo}</h3>
            <p className="text-xs text-[#6B7280]">
              {TIPO_LABEL[b.tipo] || b.tipo} · Exercício {b.exercicio_ano}
              {b.published_at && ` · ${fmtDate(b.published_at)}`}
            </p>
          </div>
          {audit ? (
            <span className={`shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${audit.conferido ? 'bg-[#F0FDF4] text-[#15803D]' : 'bg-[#FFFBEB] text-[#B45309]'}`}>
              {audit.conferido ? <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" /> : <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />}
              {audit.conferido ? 'Conferido' : 'Com observações'}
            </span>
          ) : (
            <span className="shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-[#F5F5F5] text-[#6B7280]">Por auditar</span>
          )}
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-md bg-[#F5F5F5] p-3">
            <p className="text-xs text-[#6B7280]">Receitas</p>
            <p className="text-sm font-semibold text-grafite">{fmtCve(s.total_receitas)}</p>
          </div>
          <div className="rounded-md bg-[#F5F5F5] p-3">
            <p className="text-xs text-[#6B7280]">Despesas</p>
            <p className="text-sm font-semibold text-grafite">{fmtCve(s.total_despesas)}</p>
          </div>
          <div className="rounded-md bg-[#F5F5F5] p-3">
            <p className="text-xs text-[#6B7280]">Resultado</p>
            <p className={`text-sm font-semibold ${(s.resultado_liquido || 0) >= 0 ? 'text-[#15803D]' : 'text-[#B91C1C]'}`}>{fmtCve(s.resultado_liquido)}</p>
          </div>
        </div>

        {audit?.observacoes && (
          <p className="text-xs text-[#6B7280] border-l-2 border-[#E5E7EB] pl-3">{audit.observacoes}</p>
        )}

        {podeAuditar && (
          <div className="pt-1">
            <button
              onClick={() => { setAuditTarget(b); setAuditForm({ conferido: true, observacoes: audit?.observacoes || '' }); }}
              className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
              data-testid={`auditar-${b.id}`}
            >
              <ShieldCheck className="w-4 h-4 text-[#6B7280]" aria-hidden="true" /> {audit ? 'Rever auditoria' : 'Auditar'}
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-[#6B7280]">Balancetes periódicos e balanço anual publicados pelo Tesoureiro; o Conselho Fiscal audita (Art. 34, 37).</p>
        {podePublicar && (
          <button onClick={() => setShowPublish(true)} className="flex items-center gap-2 bg-carmesim text-white px-4 py-2 rounded-lg hover:bg-carmesim-dark transition-colors text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="publicar-balancete-btn">
            <Plus className="w-4 h-4" aria-hidden="true" /> Publicar balancete
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="grid gap-3 md:grid-cols-2">{[...Array(2)].map((_, i) => <Skeleton key={i} className="h-44 w-full rounded-lg" />)}</div>
      ) : balancetes.length === 0 ? (
        <EmptyState icon={ClipboardList} title="Sem balancetes" description="Ainda não há balancetes publicados." testId="no-balancetes" />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">{balancetes.map(renderCard)}</div>
      )}

      {/* Publicar */}
      <Dialog open={showPublish} onOpenChange={(o) => { if (!o) setShowPublish(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Publicar balancete</DialogTitle>
            <DialogDescription>O snapshot dos totais é congelado no momento da publicação.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-[#6B7280] mb-1">Tipo</label>
                <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="balancete-tipo">
                  <option value="periodico">Periódico</option>
                  <option value="balanco_anual">Balanço anual</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-[#6B7280] mb-1">Exercício (ano)</label>
                <input type="number" min="2000" max="2100" value={form.exercicio_ano} onChange={(e) => setForm({ ...form, exercicio_ano: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="balancete-ano" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-[#6B7280] mb-1">Rótulo do período *</label>
                <input type="text" value={form.periodo} placeholder="2026-03 · 2026-Q1 · 2026" maxLength={12} onChange={(e) => setForm({ ...form, periodo: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="balancete-periodo" />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#6B7280] mb-1">Mês (opcional)</label>
                <select value={form.month} onChange={(e) => setForm({ ...form, month: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="balancete-mes">
                  <option value="">Ano inteiro</option>
                  {[...Array(12)].map((_, i) => <option key={i + 1} value={i + 1}>{String(i + 1).padStart(2, '0')}</option>)}
                </select>
              </div>
            </div>
            <DocumentUploadField
              kind="balancete"
              value={form.document_id}
              onChange={(id) => setForm({ ...form, document_id: id })}
              label="Balancete (PDF, opcional)"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowPublish(false)} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button onClick={() => publishMut.mutate()} disabled={publishMut.isPending || form.periodo.trim().length < 4} className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="balancete-submit">
                {publishMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Plus className="w-4 h-4" aria-hidden="true" />} Publicar
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Auditar */}
      <Dialog open={!!auditTarget} onOpenChange={(o) => { if (!o) setAuditTarget(null); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Auditar balancete {auditTarget?.periodo}</DialogTitle>
            <DialogDescription>Conselho Fiscal: confere o período e regista observações.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <input id="conferido" type="checkbox" checked={auditForm.conferido} onChange={(e) => setAuditForm({ ...auditForm, conferido: e.target.checked })} className="h-4 w-4 accent-[#C7202F] cursor-pointer" data-testid="audit-conferido" />
              <label htmlFor="conferido" className="text-sm text-grafite cursor-pointer">Período conferido (sem reservas)</label>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Observações</label>
              <textarea value={auditForm.observacoes} maxLength={2000} rows={3} onChange={(e) => setAuditForm({ ...auditForm, observacoes: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="audit-observacoes" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setAuditTarget(null)} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button onClick={() => auditMut.mutate()} disabled={auditMut.isPending} className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="audit-submit">
                {auditMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <ShieldCheck className="w-4 h-4" aria-hidden="true" />} Registar auditoria
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BalancetesTab;
