import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { propostasAgAPI, assembleiasAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { Lightbulb, Plus, Check, X, ListPlus, Loader2, Link2 } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';

const TIPO_LABEL = { medida: 'Medida', ponto: 'Ponto', tema: 'Tema' };
const STATUS = {
  submetida: { label: 'Submetida', cls: 'bg-[#FFFBEB] text-[#B45309]' },
  em_triagem: { label: 'Em triagem', cls: 'bg-[#EFF6FF] text-[#1D4ED8]' },
  aceite: { label: 'Aceite', cls: 'bg-[#F0FDF4] text-[#15803D]' },
  recusada: { label: 'Recusada', cls: 'bg-[#F5F5F5] text-[#6B7280]' },
  incluida: { label: 'Incluída na OT', cls: 'bg-[#F0FDF4] text-[#15803D]' },
  arquivada: { label: 'Arquivada', cls: 'bg-[#F5F5F5] text-[#6B7280]' },
};

export const PropostasPage = () => {
  const qc = useQueryClient();
  const { isAdmin, isMesaAG, isDirecao } = useAuth();
  const canTriage = isAdmin || isMesaAG || isDirecao;
  const canInclude = isAdmin || isMesaAG;

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ titulo: '', descricao: '', tipo: 'ponto' });
  const [statusFilter, setStatusFilter] = useState('');
  const [motivo, setMotivo] = useState({});
  const [incluir, setIncluir] = useState({}); // { [propostaId]: { assembleia_id, ordem_index } }

  const KEY = ['propostas-ag', statusFilter];
  const { data: itens = [], isLoading } = useQuery({
    queryKey: KEY,
    queryFn: async () => (await propostasAgAPI.list(statusFilter || undefined)).data,
  });
  // Assembleias para ligar a proposta à ordem de trabalhos (§2.4, F6).
  const { data: assembleias = [] } = useQuery({
    queryKey: ['assembleias', 'para-ligar'],
    queryFn: async () => (await assembleiasAPI.list()).data.assembleias || [],
    enabled: canInclude,
  });
  const assembleiaLabel = (id) => assembleias.find((a) => a.id === id)?.titulo || id;
  const invalidate = () => qc.invalidateQueries({ queryKey: ['propostas-ag'] });

  const createMut = useMutation({
    mutationFn: () => propostasAgAPI.create(form),
    onSuccess: () => {
      toast.success('Proposta submetida.');
      invalidate();
      setShowCreate(false);
      setForm({ titulo: '', descricao: '', tipo: 'ponto' });
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao submeter'),
  });
  const triarMut = useMutation({
    mutationFn: ({ id, decisao }) => propostasAgAPI.triar(id, { decisao, decisao_motivo: motivo[id] || null }),
    onSuccess: () => { toast.success('Proposta triada.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao triar'),
  });
  const incluirMut = useMutation({
    mutationFn: ({ id, data }) => propostasAgAPI.incluir(id, data),
    onSuccess: () => { toast.success('Proposta incluída na ordem de trabalhos.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao incluir'),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title" data-testid="propostas-title">Propostas para a ordem de trabalhos</h1>
          <p className="page-subtitle">Submeta medidas, pontos ou temas para a Assembleia Geral. A Mesa e a Direcção triam e podem incluí-los na ordem de trabalhos (Art. 9.g/9.h).</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 bg-floresta text-white px-4 py-2 rounded-lg hover:bg-floresta-dark transition-colors text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="new-proposta-btn">
          <Plus className="w-4 h-4" aria-hidden="true" /> Nova proposta
        </button>
      </div>

      {canTriage && (
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-[#6B7280]">Filtrar por estado</label>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="px-3 py-1.5 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="proposta-filter">
            <option value="">Todas</option>
            {Object.entries(STATUS).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-28 w-full rounded-lg" />)}</div>
      ) : itens.length === 0 ? (
        <EmptyState icon={Lightbulb} title="Sem propostas" testId="no-propostas" />
      ) : (
        <div className="space-y-3">
          {itens.map((pr) => {
            const st = STATUS[pr.status] || STATUS.submetida;
            return (
              <div key={pr.id} className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-4 space-y-2" data-testid={`proposta-${pr.id}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-grafite">{pr.titulo}</h3>
                    <p className="text-xs text-[#6B7280]">{TIPO_LABEL[pr.tipo] || pr.tipo} · {pr.created_at ? format(new Date(pr.created_at), 'dd MMM yyyy', { locale: ptBR }) : ''}</p>
                  </div>
                  <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${st.cls}`}>{st.label}</span>
                </div>
                <p className="text-sm text-grafite whitespace-pre-wrap">{pr.descricao}</p>
                {pr.decisao_motivo && (
                  <div className="rounded-md bg-[#F5F5F5] p-3">
                    <p className="text-xs font-medium text-[#6B7280] mb-1">Motivo da triagem</p>
                    <p className="text-sm text-grafite whitespace-pre-wrap">{pr.decisao_motivo}</p>
                  </div>
                )}

                {canTriage && ['submetida', 'em_triagem'].includes(pr.status) && (
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <input type="text" value={motivo[pr.id] || ''} onChange={(ev) => setMotivo({ ...motivo, [pr.id]: ev.target.value })} placeholder="Motivo (opcional)…" className="flex-1 min-w-[12rem] px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`motivo-${pr.id}`} />
                    <button onClick={() => triarMut.mutate({ id: pr.id, decisao: 'aceite' })} disabled={triarMut.isPending} className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`aceitar-${pr.id}`}>
                      <Check className="w-4 h-4 text-[#15803D]" aria-hidden="true" /> Aceitar
                    </button>
                    <button onClick={() => triarMut.mutate({ id: pr.id, decisao: 'recusada' })} disabled={triarMut.isPending} className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`recusar-${pr.id}`}>
                      <X className="w-4 h-4 text-[#6B7280]" aria-hidden="true" /> Recusar
                    </button>
                  </div>
                )}
                {canInclude && pr.status === 'aceite' && (
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <select value={incluir[pr.id]?.assembleia_id || ''} onChange={(e) => setIncluir({ ...incluir, [pr.id]: { ...incluir[pr.id], assembleia_id: e.target.value } })} className="px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`incluir-assembleia-${pr.id}`}>
                      <option value="">Assembleia (opcional)…</option>
                      {assembleias.map((a) => <option key={a.id} value={a.id}>{a.titulo}</option>)}
                    </select>
                    <input type="number" min="1" value={incluir[pr.id]?.ordem_index || ''} onChange={(e) => setIncluir({ ...incluir, [pr.id]: { ...incluir[pr.id], ordem_index: e.target.value } })} placeholder="Ponto nº" className="w-24 px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`incluir-ordem-${pr.id}`} />
                    <button onClick={() => incluirMut.mutate({ id: pr.id, data: { assembleia_id: incluir[pr.id]?.assembleia_id || null, ordem_index: incluir[pr.id]?.ordem_index ? Number(incluir[pr.id].ordem_index) : null } })} disabled={incluirMut.isPending} className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`incluir-${pr.id}`}>
                      <ListPlus className="w-4 h-4" aria-hidden="true" /> Incluir na ordem de trabalhos
                    </button>
                  </div>
                )}
                {pr.status === 'incluida' && pr.assembleia_id && (
                  <p className="text-xs text-[#6B7280] inline-flex items-center gap-1.5 pt-1" data-testid={`incluida-${pr.id}`}>
                    <Link2 className="w-3.5 h-3.5" aria-hidden="true" /> Incluída na AG: {assembleiaLabel(pr.assembleia_id)}{pr.ordem_index ? ` · ponto ${pr.ordem_index}` : ''}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      <Dialog open={showCreate} onOpenChange={(o) => { if (!o) setShowCreate(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Nova proposta</DialogTitle><DialogDescription>Medida, ponto ou tema para a ordem de trabalhos (Art. 9.g/9.h).</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Tipo</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="prop-tipo">
                <option value="ponto">Ponto</option>
                <option value="medida">Medida</option>
                <option value="tema">Tema</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Título *</label>
              <input type="text" value={form.titulo} maxLength={180} onChange={(e) => setForm({ ...form, titulo: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="prop-titulo" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Descrição *</label>
              <textarea value={form.descricao} maxLength={5000} rows={4} onChange={(e) => setForm({ ...form, descricao: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="prop-descricao" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button onClick={() => createMut.mutate()} disabled={createMut.isPending || form.titulo.trim().length < 3 || !form.descricao.trim()} className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-floresta text-white text-sm font-semibold hover:bg-floresta-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="prop-submit">
                {createMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Plus className="w-4 h-4" aria-hidden="true" />} Submeter
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PropostasPage;
