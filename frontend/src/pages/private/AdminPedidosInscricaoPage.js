import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { registrationAPI, financesAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { toast } from 'sonner';
import { UserPlus, Check, X, Mail, Phone, Building2, BadgeCheck, Clock } from 'lucide-react';
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle,
} from '../../components/ui/dialog';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

const ROLE_OPTIONS = [
  { value: 'socio', label: 'Sócio' },
  { value: 'moderador', label: 'Moderador' },
  { value: 'financeiro', label: 'Financeiro' },
  { value: 'admin', label: 'Administrador' },
];

const TABS = [
  { value: 'pendente_aprovacao', label: 'Pendentes' },
  { value: 'rejeitado', label: 'Rejeitados' },
];

const formatDate = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return '—';
  }
};

export const AdminPedidosInscricaoPage = () => {
  const qc = useQueryClient();
  const [tab, setTab] = useState('pendente_aprovacao');
  const [approving, setApproving] = useState(null); // request a aprovar
  const [approveForm, setApproveForm] = useState({ role: 'socio', cargo: '', waive: false, cta_qualified_since: '' });
  const [rejecting, setRejecting] = useState(null); // request a rejeitar
  const [rejectReason, setRejectReason] = useState('');

  const { data: requests = [], isLoading } = useQuery({
    queryKey: queryKeys.registration.requests(tab),
    queryFn: async () => (await registrationAPI.listPending({ status: tab })).data,
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ['registration'] });

  const approveMutation = useMutation({
    mutationFn: ({ id, data }) => registrationAPI.approve(id, data),
    onSuccess: (res) => {
      toast.success(res.data?.message || 'Pedido aprovado.');
      setApproving(null);
      invalidate();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao aprovar o pedido'),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }) => registrationAPI.reject(id, reason),
    onSuccess: () => {
      toast.success('Pedido rejeitado.');
      setRejecting(null);
      setRejectReason('');
      invalidate();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao rejeitar o pedido'),
  });

  // Jóia (Art. 6): pré-visualiza sem gravar; reage à data de qualificação CTA.
  const { data: joiaPreview } = useQuery({
    queryKey: queryKeys.registration.joiaPreview(approving?.id, approveForm.cta_qualified_since),
    queryFn: async () =>
      (await financesAPI.getJoiaPreview(approving.id, approveForm.cta_qualified_since || undefined)).data,
    enabled: !!approving,
    staleTime: 0,
  });

  const openApprove = (req) => {
    setApproveForm({
      role: 'socio',
      cargo: req.cargo_declarado || req.cargo || 'Sócio',
      waive: false,
      cta_qualified_since: req.cta_qualified_since || '',
    });
    setApproving(req);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-carmesim/10 flex items-center justify-center">
          <UserPlus className="w-5 h-5 text-carmesim" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-grafite">Pedidos de inscrição</h1>
          <p className="text-sm text-[#6B7280]">Aprove ou rejeite pedidos de auto-registo de sócios.</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200">
        {TABS.map((t) => (
          <button
            key={t.value}
            onClick={() => setTab(t.value)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t.value
                ? 'border-carmesim text-carmesim'
                : 'border-transparent text-[#6B7280] hover:text-grafite'
            }`}
            data-testid={`tab-${t.value}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Conteúdo */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}
        </div>
      ) : requests.length === 0 ? (
        <EmptyState
          icon={UserPlus}
          title={tab === 'pendente_aprovacao' ? 'Sem pedidos pendentes' : 'Sem pedidos rejeitados'}
          testId="no-registration-requests"
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs uppercase tracking-wider text-[#6B7280]">
                <th className="px-4 py-3 font-semibold">Sócio</th>
                <th className="px-4 py-3 font-semibold">Cargo declarado</th>
                <th className="px-4 py-3 font-semibold">Nº associado</th>
                <th className="px-4 py-3 font-semibold">Contacto</th>
                <th className="px-4 py-3 font-semibold">Patrocínios</th>
                <th className="px-4 py-3 font-semibold">Data</th>
                {tab === 'pendente_aprovacao' && <th className="px-4 py-3 font-semibold text-right">Ações</th>}
              </tr>
            </thead>
            <tbody>
              {requests.map((req) => (
                <tr key={req.id} className="border-b border-gray-100 last:border-0" data-testid="registration-row">
                  <td className="px-4 py-3">
                    <p className="font-medium text-grafite">{req.name}</p>
                    <p className="text-xs text-[#6B7280] flex items-center gap-1">
                      <Mail className="w-3 h-3" aria-hidden="true" />{req.email}
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-gray-100 text-grafite text-xs font-medium">
                      <BadgeCheck className="w-3 h-3" aria-hidden="true" />{req.cargo_declarado || '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-grafite">{req.member_id || '—'}</td>
                  <td className="px-4 py-3 text-xs text-[#6B7280]">
                    {req.phone_number && <p className="flex items-center gap-1"><Phone className="w-3 h-3" aria-hidden="true" />{req.phone_number}</p>}
                    {req.department && <p className="flex items-center gap-1"><Building2 className="w-3 h-3" aria-hidden="true" />{req.department}</p>}
                    {!req.phone_number && !req.department && '—'}
                  </td>
                  <td className="px-4 py-3">
                    {(req.sponsors || []).length === 0 ? (
                      <span className="text-xs text-[#6B7280]">—</span>
                    ) : (
                      <div className="space-y-1">
                        <span className="text-xs font-medium text-grafite">{req.confirmed_count || 0}/2 confirmados</span>
                        <div className="flex flex-wrap gap-1">
                          {(req.sponsors || []).map((s, i) => (
                            <span
                              key={i}
                              title={s.name || s.member_id || ''}
                              className={`inline-flex items-center px-1.5 py-0.5 rounded text-[11px] ${
                                s.status === 'confirmado'
                                  ? 'bg-[#F0FDF4] text-[#15803D]'
                                  : s.status === 'recusado'
                                    ? 'bg-[#FEF2F2] text-[#B91C1C]'
                                    : 'bg-[#FFFBEB] text-[#B45309]'
                              }`}
                            >
                              {s.member_id || s.name || '—'}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-[#6B7280]">
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" aria-hidden="true" />{formatDate(req.registration_request_at)}</span>
                  </td>
                  {tab === 'pendente_aprovacao' && (
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => openApprove(req)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-carmesim text-white text-xs font-semibold hover:bg-carmesim-dark transition-colors"
                          data-testid="approve-btn"
                        >
                          <Check className="w-3.5 h-3.5" />Aprovar
                        </button>
                        <button
                          onClick={() => { setRejecting(req); setRejectReason(''); }}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[#D1D5DB] text-grafite text-xs font-medium hover:bg-gray-50 transition-colors"
                          data-testid="reject-btn"
                        >
                          <X className="w-3.5 h-3.5" />Rejeitar
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal Aprovar */}
      <Dialog open={!!approving} onOpenChange={(o) => { if (!o) setApproving(null); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Aprovar pedido</DialogTitle>
            <DialogDescription>
              {approving?.name} — será enviado um email de ativação para definir a password.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Nível de acesso (role)</label>
              <select
                value={approveForm.role}
                onChange={(e) => setApproveForm({ ...approveForm, role: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-white focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none"
                data-testid="approve-role"
              >
                {ROLE_OPTIONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Cargo</label>
              <input
                type="text"
                value={approveForm.cargo}
                onChange={(e) => setApproveForm({ ...approveForm, cargo: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none"
                data-testid="approve-cargo"
              />
            </div>
            {/* Jóia de admissão (Art. 6): data de qualificação CTA + pré-visualização. */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Qualificado como CTA desde (Art. 6 — jóia)</label>
              <input
                type="date"
                value={approveForm.cta_qualified_since}
                max={new Date().toISOString().slice(0, 10)}
                onChange={(e) => setApproveForm({ ...approveForm, cta_qualified_since: e.target.value })}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none"
                data-testid="approve-cta-since"
              />
              {joiaPreview && (
                <p className="mt-1.5 text-xs text-grafite bg-[#F5F5F5] rounded-md px-2.5 py-1.5" data-testid="joia-preview">
                  {joiaPreview.joia_devida != null ? (
                    <>Jóia devida: <strong>{joiaPreview.joia_devida.toLocaleString('pt-PT')} CVE</strong>. Cobrança manual pelo Tesoureiro.</>
                  ) : (
                    <>Sem jóia — {joiaPreview.motivo}.</>
                  )}
                </p>
              )}
            </div>
            {/* Gate de patrocínio (Art. 8.3): aprovar exige 2 confirmados, salvo dispensa. */}
            <div className={`rounded-lg px-3 py-2.5 text-xs ${(approving?.confirmed_count || 0) >= 2 ? 'bg-[#F0FDF4] text-[#15803D]' : 'bg-[#FFFBEB] text-[#B45309]'}`}>
              Patrocínio (Art. 8.3): <strong>{approving?.confirmed_count || 0}/2</strong> confirmados.
            </div>
            {(approving?.confirmed_count || 0) < 2 && (
              <label className="flex items-start gap-2 text-xs text-[#6B7280] cursor-pointer">
                <input
                  type="checkbox"
                  checked={approveForm.waive}
                  onChange={(e) => setApproveForm({ ...approveForm, waive: e.target.checked })}
                  className="mt-0.5 h-4 w-4 rounded border-gray-300 text-carmesim focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                  data-testid="approve-waive"
                />
                <span>Dispensar patrocínio (Art. 8.3). A dispensa fica registada no audit log.</span>
              </label>
            )}
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setApproving(null)}
                className="px-4 py-2 rounded-lg border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={() => approveMutation.mutate({ id: approving.id, data: { role: approveForm.role, cargo: approveForm.cargo || null, waive_sponsorship: approveForm.waive, cta_qualified_since: approveForm.cta_qualified_since || null } })}
                disabled={approveMutation.isPending || (!approveForm.waive && (approving?.confirmed_count || 0) < 2)}
                className="px-4 py-2 rounded-lg bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="approve-confirm"
              >
                {approveMutation.isPending ? 'A aprovar...' : 'Confirmar aprovação'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Modal Rejeitar */}
      <Dialog open={!!rejecting} onOpenChange={(o) => { if (!o) setRejecting(null); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Rejeitar pedido</DialogTitle>
            <DialogDescription>
              {rejecting?.name} — opcionalmente indique um motivo (incluído no email).
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={3}
              maxLength={500}
              placeholder="Motivo (opcional)"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none resize-none"
              data-testid="reject-reason"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setRejecting(null)}
                className="px-4 py-2 rounded-lg border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={() => rejectMutation.mutate({ id: rejecting.id, reason: rejectReason || null })}
                disabled={rejectMutation.isPending}
                className="px-4 py-2 rounded-lg border border-[#D1D5DB] text-carmesim text-sm font-semibold hover:bg-[#FEF2F2] transition-colors disabled:opacity-50"
                data-testid="reject-confirm"
              >
                {rejectMutation.isPending ? 'A rejeitar...' : 'Confirmar rejeição'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminPedidosInscricaoPage;
