import React, { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { cargosAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { ROLE_LABELS, PRIVILEGE_LABELS } from '../../lib/cargoLabels';
import { toast } from 'sonner';
import { Award, UserPlus, ArrowRightLeft, UserMinus, Search, Hash } from 'lucide-react';
import {
  Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle,
} from '../../components/ui/dialog';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

const ROLE_OPTIONS = ['admin', 'financeiro', 'moderador', 'socio'];

const formatDate = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return '—';
  }
};

// Procura de sócios elegíveis (debounced) para atribuir/transferir um cargo.
const CandidatePicker = ({ excludeCargo, value, onSelect, testId }) => {
  const [search, setSearch] = useState('');
  const [debounced, setDebounced] = useState('');

  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  const { data: candidates = [], isFetching } = useQuery({
    queryKey: queryKeys.cargos.candidates({ q: debounced, excludeCargo }),
    queryFn: async () => (await cargosAPI.candidates({ q: debounced, exclude_cargo: excludeCargo || undefined })).data.candidates,
    staleTime: 30 * 1000,
  });

  return (
    <div>
      {value ? (
        <div className="flex items-center justify-between px-3 py-2.5 rounded-lg border border-[#D1D5DB] bg-[#F5F5F5]">
          <span className="text-sm text-grafite">
            {value.name} <span className="font-mono text-xs text-[#6B7280]">{value.member_id || ''}</span>
          </span>
          <button onClick={() => onSelect(null)} className="text-xs text-carmesim font-semibold hover:underline">
            Alterar
          </button>
        </div>
      ) : (
        <>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Procurar por nome, email ou nº associado..."
              className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 outline-none"
              data-testid={testId}
            />
          </div>
          <div className="mt-1.5 max-h-44 overflow-y-auto rounded-lg border border-gray-100 divide-y divide-gray-50">
            {isFetching && candidates.length === 0 ? (
              <div className="px-3 py-3"><Skeleton className="h-4 w-40" /></div>
            ) : candidates.length === 0 ? (
              <p className="px-3 py-3 text-xs text-[#6B7280]">Nenhum sócio encontrado.</p>
            ) : (
              candidates.map((c) => (
                <button
                  key={c.id}
                  onClick={() => onSelect(c)}
                  className="w-full text-left px-3 py-2 hover:bg-[#F5F5F5] transition-colors"
                  data-testid={`candidate-${c.id}`}
                >
                  <span className="text-sm text-grafite">{c.name}</span>
                  <span className="ml-2 font-mono text-xs text-[#6B7280]">{c.member_id || ''}</span>
                  <span className="block text-xs text-[#6B7280]">{c.email} · {c.cargo}</span>
                </button>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
};

// Campos partilhados pelos modais de atribuir/transferir: role + privilégios + meta.
const MandateFields = ({ form, setForm, privileges }) => (
  <>
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1.5">Nível de acesso (role)</label>
      <select
        value={form.role}
        onChange={(e) => setForm({ ...form, role: e.target.value })}
        className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 outline-none"
        data-testid="mandate-role"
      >
        {ROLE_OPTIONS.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
      </select>
    </div>
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1.5">Privilégios</label>
      <div className="grid grid-cols-2 gap-1.5">
        {privileges.map((p) => {
          const checked = form.privileges.includes(p);
          return (
            <label key={p} className="flex items-center gap-2 text-xs text-grafite cursor-pointer">
              <input
                type="checkbox"
                checked={checked}
                onChange={() =>
                  setForm({
                    ...form,
                    privileges: checked ? form.privileges.filter((x) => x !== p) : [...form.privileges, p],
                  })
                }
                className="rounded border-gray-300 text-carmesim focus:ring-carmesim/40"
              />
              {PRIVILEGE_LABELS[p] || p}
            </label>
          );
        })}
      </div>
    </div>
    <div className="grid grid-cols-2 gap-3">
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1.5">Data efetiva</label>
        <input
          type="date"
          value={form.effectiveDate}
          onChange={(e) => setForm({ ...form, effectiveDate: e.target.value })}
          className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 outline-none"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1.5">Eleito por</label>
        <input
          type="text"
          value={form.electedBy}
          onChange={(e) => setForm({ ...form, electedBy: e.target.value })}
          placeholder="AGA 2026"
          className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 outline-none"
        />
      </div>
    </div>
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1.5">Notas</label>
      <textarea
        value={form.notes}
        onChange={(e) => setForm({ ...form, notes: e.target.value })}
        rows={2}
        maxLength={500}
        className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 outline-none resize-none"
      />
    </div>
  </>
);

const isoOrNull = (dateStr) => (dateStr ? `${dateStr}T00:00:00.000Z` : null);

export const AdminCargosPage = () => {
  const qc = useQueryClient();
  const [assigning, setAssigning] = useState(null); // cargo vago a atribuir
  const [transferring, setTransferring] = useState(null); // { cargo, holder }
  const [ending, setEnding] = useState(null); // { cargo, holder }
  const [form, setForm] = useState(null); // form partilhado de mandato
  const [endNotes, setEndNotes] = useState('');

  const { data: meta } = useQuery({
    queryKey: queryKeys.cargos.meta(),
    queryFn: async () => (await cargosAPI.getMeta()).data,
    staleTime: 60 * 60 * 1000, // estático
  });

  const { data: cargosResp, isLoading } = useQuery({
    queryKey: queryKeys.cargos.list(),
    queryFn: async () => (await cargosAPI.list()).data,
  });

  const cargos = cargosResp?.cargos || [];
  const privileges = meta?.privileges || [];
  const cargoDefaults = useMemo(() => meta?.cargo_defaults || {}, [meta]);

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['cargos'] });
    qc.invalidateQueries({ queryKey: ['users'] });
  };

  const buildForm = (cargo, toUser = null) => ({
    toUser,
    role: cargoDefaults[cargo]?.role || 'socio',
    privileges: [...(cargoDefaults[cargo]?.privileges || [])],
    effectiveDate: '',
    electedBy: '',
    notes: '',
  });

  const promoteMutation = useMutation({
    mutationFn: ({ userId, data }) => cargosAPI.promote(userId, data),
    onSuccess: (res) => { toast.success(res.data?.message || 'Cargo atribuído.'); setAssigning(null); setForm(null); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao atribuir o cargo'),
  });

  const transferMutation = useMutation({
    mutationFn: (data) => cargosAPI.transfer(data),
    onSuccess: (res) => { toast.success(res.data?.message || 'Cargo transferido.'); setTransferring(null); setForm(null); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao transferir o cargo'),
  });

  const demoteMutation = useMutation({
    mutationFn: ({ userId, data }) => cargosAPI.demote(userId, data),
    onSuccess: () => { toast.success('Mandato encerrado.'); setEnding(null); setEndNotes(''); invalidate(); },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao encerrar o mandato'),
  });

  const openAssign = (cargo) => { setForm(buildForm(cargo.cargo)); setAssigning(cargo); };
  const openTransfer = (cargo, holder) => { setForm(buildForm(cargo.cargo)); setTransferring({ cargo, holder }); };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-carmesim/10 flex items-center justify-center">
          <Award className="w-5 h-5 text-carmesim" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-grafite">Cargos & Mandatos</h1>
          <p className="text-sm text-[#6B7280]">Atribua, transfira ou encerre mandatos dos órgãos sociais.</p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(6)].map((_, i) => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}</div>
      ) : cargos.length === 0 ? (
        <EmptyState icon={Award} title="Sem cargos definidos" testId="no-cargos" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs uppercase tracking-wider text-[#6B7280]">
                <th className="px-4 py-3 font-semibold">Cargo</th>
                <th className="px-4 py-3 font-semibold">Titular(es)</th>
                <th className="px-4 py-3 font-semibold">Vagas</th>
                <th className="px-4 py-3 font-semibold text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {cargos.map((c) => {
                const occupied = c.holders.length;
                const hasVacancy = c.seats === 0 || occupied < c.seats;
                return (
                  <tr key={c.cargo} className="border-b border-gray-100 last:border-0 align-top" data-testid={`cargo-row-${c.cargo}`}>
                    <td className="px-4 py-3 font-medium text-grafite">{c.cargo}</td>
                    <td className="px-4 py-3">
                      {occupied === 0 ? (
                        <span className="text-xs text-[#6B7280] italic">Vago</span>
                      ) : (
                        <div className="space-y-1.5">
                          {c.holders.map((h) => (
                            <div key={h.id} className="flex items-center gap-2">
                              <span className="text-grafite">{h.name}</span>
                              <span className="font-mono text-xs text-[#6B7280] flex items-center gap-0.5">
                                <Hash className="w-3 h-3" aria-hidden="true" />{h.member_id || '—'}
                              </span>
                              <span className="text-xs text-[#6B7280]">desde {formatDate(h.since)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-[#6B7280]">{occupied}/{c.seats === 0 ? '∞' : c.seats}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        {hasVacancy && (
                          <button
                            onClick={() => openAssign(c)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[#D1D5DB] text-grafite text-xs font-medium hover:bg-[#F5F5F5] transition-colors"
                            data-testid={`assign-${c.cargo}`}
                          >
                            <UserPlus className="w-3.5 h-3.5" aria-hidden="true" />Atribuir
                          </button>
                        )}
                        {c.holders.map((h) => (
                          <React.Fragment key={h.id}>
                            <button
                              onClick={() => openTransfer(c, h)}
                              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[#D1D5DB] text-grafite text-xs font-medium hover:bg-[#F5F5F5] transition-colors"
                              data-testid={`transfer-${c.cargo}`}
                            >
                              <ArrowRightLeft className="w-3.5 h-3.5" aria-hidden="true" />Transferir
                            </button>
                            <button
                              onClick={() => setEnding({ cargo: c, holder: h })}
                              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[#D1D5DB] text-carmesim text-xs font-medium hover:bg-[#FEF2F2] transition-colors"
                              data-testid={`end-${c.cargo}`}
                            >
                              <UserMinus className="w-3.5 h-3.5" aria-hidden="true" />Terminar
                            </button>
                          </React.Fragment>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal Atribuir (promote) */}
      <Dialog open={!!assigning} onOpenChange={(o) => { if (!o) { setAssigning(null); setForm(null); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Atribuir cargo: {assigning?.cargo}</DialogTitle>
            <DialogDescription>Escolha o sócio e confirme o nível de acesso e privilégios.</DialogDescription>
          </DialogHeader>
          {form && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Sócio</label>
                <CandidatePicker
                  excludeCargo={assigning?.cargo}
                  value={form.toUser}
                  onSelect={(u) => setForm({ ...form, toUser: u })}
                  testId="assign-candidate-search"
                />
              </div>
              <MandateFields form={form} setForm={setForm} privileges={privileges} />
              <div className="flex justify-end gap-2 pt-1">
                <button onClick={() => { setAssigning(null); setForm(null); }} className="px-4 py-2 rounded-lg border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-gray-50 transition-colors">Cancelar</button>
                <button
                  onClick={() => promoteMutation.mutate({
                    userId: form.toUser.id,
                    data: { cargo: assigning.cargo, role: form.role, privileges: form.privileges, elected_by: form.electedBy || null, notes: form.notes || null, effective_date: isoOrNull(form.effectiveDate) },
                  })}
                  disabled={!form.toUser || promoteMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark transition-colors disabled:opacity-50"
                  data-testid="assign-confirm"
                >
                  {promoteMutation.isPending ? 'A atribuir...' : 'Confirmar atribuição'}
                </button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal Transferir */}
      <Dialog open={!!transferring} onOpenChange={(o) => { if (!o) { setTransferring(null); setForm(null); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Transferir cargo: {transferring?.cargo.cargo}</DialogTitle>
            <DialogDescription>De {transferring?.holder.name} para outro sócio (operação atómica).</DialogDescription>
          </DialogHeader>
          {form && (
            <div className="space-y-4">
              <div className="px-3 py-2.5 rounded-lg bg-[#F5F5F5] border border-[#D1D5DB] text-sm text-grafite">
                <span className="text-xs text-[#6B7280]">De:</span> {transferring?.holder.name}
                <span className="ml-1 font-mono text-xs text-[#6B7280]">{transferring?.holder.member_id || ''}</span>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Para</label>
                <CandidatePicker
                  excludeCargo={transferring?.cargo.cargo}
                  value={form.toUser}
                  onSelect={(u) => setForm({ ...form, toUser: u })}
                  testId="transfer-candidate-search"
                />
              </div>
              <MandateFields form={form} setForm={setForm} privileges={privileges} />
              <div className="flex justify-end gap-2 pt-1">
                <button onClick={() => { setTransferring(null); setForm(null); }} className="px-4 py-2 rounded-lg border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-gray-50 transition-colors">Cancelar</button>
                <button
                  onClick={() => transferMutation.mutate({
                    from_user_id: transferring.holder.id,
                    to_user_id: form.toUser.id,
                    cargo: transferring.cargo.cargo,
                    role: form.role,
                    privileges: form.privileges,
                    elected_by: form.electedBy || null,
                    notes: form.notes || null,
                    effective_date: isoOrNull(form.effectiveDate),
                  })}
                  disabled={!form.toUser || transferMutation.isPending}
                  className="px-4 py-2 rounded-lg bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark transition-colors disabled:opacity-50"
                  data-testid="transfer-confirm"
                >
                  {transferMutation.isPending ? 'A transferir...' : 'Confirmar transferência'}
                </button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Modal Terminar mandato (demote) */}
      <Dialog open={!!ending} onOpenChange={(o) => { if (!o) { setEnding(null); setEndNotes(''); } }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Terminar mandato</DialogTitle>
            <DialogDescription>
              {ending?.holder.name} deixa de ser {ending?.cargo.cargo} e volta a Sócio.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <textarea
              value={endNotes}
              onChange={(e) => setEndNotes(e.target.value)}
              rows={2}
              maxLength={500}
              placeholder="Notas (opcional)"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 outline-none resize-none"
              data-testid="end-notes"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => { setEnding(null); setEndNotes(''); }} className="px-4 py-2 rounded-lg border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-gray-50 transition-colors">Cancelar</button>
              <button
                onClick={() => demoteMutation.mutate({ userId: ending.holder.id, data: { notes: endNotes || null } })}
                disabled={demoteMutation.isPending}
                className="px-4 py-2 rounded-lg border border-[#D1D5DB] text-carmesim text-sm font-semibold hover:bg-[#FEF2F2] transition-colors disabled:opacity-50"
                data-testid="end-confirm"
              >
                {demoteMutation.isPending ? 'A encerrar...' : 'Confirmar fim de mandato'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminCargosPage;
