import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reclamacoesAPI, assembleiasAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { ShieldAlert, Plus, Send, Loader2, Gavel, Link2 } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';

const KEY = ['reclamacoes'];
const STATUS = {
  submetida: { label: 'Submetida', cls: 'bg-[#FFFBEB] text-[#B45309]' },
  em_analise: { label: 'Em análise', cls: 'bg-[#EFF6FF] text-[#1D4ED8]' },
  respondida: { label: 'Respondida', cls: 'bg-[#EFF6FF] text-[#1D4ED8]' },
  resolvida: { label: 'Resolvida', cls: 'bg-[#F0FDF4] text-[#15803D]' },
  recurso: { label: 'Em recurso', cls: 'bg-[#FBEAEC] text-carmesim' },
  encerrada: { label: 'Encerrada', cls: 'bg-[#F5F5F5] text-[#6B7280]' },
};

export const ReclamacoesPage = () => {
  const qc = useQueryClient();
  const { user, isAdmin, isDirecao, isMesaAG } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ assunto: '', descricao: '' });
  const [resp, setResp] = useState({});
  const [dec, setDec] = useState({});

  const { data: itens = [], isLoading } = useQuery({ queryKey: KEY, queryFn: async () => (await reclamacoesAPI.list()).data });
  // Assembleias para ligar a decisão do recurso a uma deliberação da AG (§2.4, F6).
  const { data: assembleias = [] } = useQuery({
    queryKey: ['assembleias', 'para-ligar'],
    queryFn: async () => (await assembleiasAPI.list()).data.assembleias || [],
    enabled: isAdmin || isMesaAG,
  });
  const assembleiaLabel = (id) => assembleias.find((a) => a.id === id)?.titulo || id;
  const invalidate = () => qc.invalidateQueries({ queryKey: KEY });

  const createMut = useMutation({
    mutationFn: () => reclamacoesAPI.create(form),
    onSuccess: () => { toast.success('Reclamação submetida.'); invalidate(); setShowCreate(false); setForm({ assunto: '', descricao: '' }); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao submeter'),
  });
  const respMut = useMutation({
    mutationFn: ({ id, texto, resolvida }) => reclamacoesAPI.responder(id, { texto, resolvida }),
    onSuccess: () => { toast.success('Resposta registada.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao responder'),
  });
  const recursoMut = useMutation({
    mutationFn: (id) => reclamacoesAPI.recurso(id),
    onSuccess: () => { toast.success('Recurso aberto.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao recorrer'),
  });
  const decMut = useMutation({
    mutationFn: ({ id, data }) => reclamacoesAPI.decidirRecurso(id, data),
    onSuccess: () => { toast.success('Recurso decidido.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao decidir'),
  });

  const canRespond = isAdmin || isDirecao;
  const canDecide = isAdmin || isMesaAG;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title" data-testid="reclamacoes-title">Reclamações e recursos</h1>
          <p className="page-subtitle">Reclame à Direcção de actos que considere lesivos; se não for resolvido, pode recorrer à Assembleia (Art. 9.i). Conteúdo visível só ao autor e à Direcção.</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 bg-carmesim text-white px-4 py-2 rounded-lg hover:bg-carmesim-dark transition-colors text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="new-reclamacao-btn">
          <Plus className="w-4 h-4" aria-hidden="true" /> Nova reclamação
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-28 w-full rounded-lg" />)}</div>
      ) : itens.length === 0 ? (
        <EmptyState icon={ShieldAlert} title="Sem reclamações" testId="no-reclamacoes" />
      ) : (
        <div className="space-y-3">
          {itens.map((r) => {
            const st = STATUS[r.status] || STATUS.submetida;
            const isAuthor = r.created_by === user?.id;
            const answered = !!r.direcao_resposta;
            const expired = r.prazo_resposta && r.prazo_resposta < new Date().toISOString();
            const canRecorrer = isAuthor && (answered || expired) && !['recurso', 'encerrada'].includes(r.status);
            return (
              <div key={r.id} className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-4 space-y-2" data-testid={`reclamacao-${r.id}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-grafite">{r.assunto}</h3>
                    <p className="text-xs text-[#6B7280]">{r.created_at ? format(new Date(r.created_at), 'dd MMM yyyy', { locale: ptBR }) : ''}{r.prazo_resposta ? ` · prazo ${format(new Date(r.prazo_resposta), 'dd MMM', { locale: ptBR })}` : ''}</p>
                  </div>
                  <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${st.cls}`}>{st.label}</span>
                </div>
                <p className="text-sm text-grafite whitespace-pre-wrap">{r.descricao}</p>
                {r.direcao_resposta?.text && (
                  <div className="rounded-md bg-[#F5F5F5] p-3"><p className="text-xs font-medium text-[#6B7280] mb-1">Resposta da Direcção</p><p className="text-sm text-grafite whitespace-pre-wrap">{r.direcao_resposta.text}</p></div>
                )}
                {r.recurso?.decisao && (
                  <div className="rounded-md bg-[#FBEAEC] p-3">
                    <p className="text-xs font-medium text-carmesim mb-1">Decisão do recurso (AG)</p>
                    <p className="text-sm text-grafite whitespace-pre-wrap">{r.recurso.decisao}</p>
                    {r.recurso.assembleia_id && (
                      <p className="text-xs text-[#6B7280] mt-1 inline-flex items-center gap-1.5">
                        <Link2 className="w-3.5 h-3.5" aria-hidden="true" /> {assembleiaLabel(r.recurso.assembleia_id)}{r.recurso.deliberacao_id ? ` · deliberação ${r.recurso.deliberacao_id}` : ''}
                      </p>
                    )}
                  </div>
                )}

                {canRespond && !['resolvida', 'recurso', 'encerrada'].includes(r.status) && (
                  <div className="flex flex-col sm:flex-row gap-2 pt-1">
                    <input type="text" value={resp[r.id]?.texto || ''} onChange={(e) => setResp({ ...resp, [r.id]: { ...resp[r.id], texto: e.target.value } })} placeholder="Resposta da Direcção…" className="flex-1 px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`rec-resp-${r.id}`} />
                    <label className="flex items-center gap-1.5 text-xs text-[#6B7280] whitespace-nowrap"><input type="checkbox" checked={!!resp[r.id]?.resolvida} onChange={(e) => setResp({ ...resp, [r.id]: { ...resp[r.id], resolvida: e.target.checked } })} className="h-4 w-4 rounded border-gray-300 text-carmesim" /> Resolvida</label>
                    <button onClick={() => respMut.mutate({ id: r.id, texto: resp[r.id]?.texto, resolvida: !!resp[r.id]?.resolvida })} disabled={respMut.isPending || !(resp[r.id]?.texto || '').trim()} className="inline-flex items-center gap-1.5 bg-carmesim text-white px-3 py-2 rounded-md text-sm font-semibold hover:bg-carmesim-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`rec-resp-btn-${r.id}`}>
                      <Send className="w-4 h-4" aria-hidden="true" /> Responder
                    </button>
                  </div>
                )}

                {canRecorrer && (
                  <button onClick={() => recursoMut.mutate(r.id)} disabled={recursoMut.isPending} className="inline-flex items-center gap-1.5 bg-white border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer disabled:opacity-50" data-testid={`rec-recurso-${r.id}`}>
                    <Gavel className="w-4 h-4" aria-hidden="true" /> Recorrer à AG
                  </button>
                )}

                {canDecide && r.status === 'recurso' && (
                  <div className="space-y-2 pt-1">
                    <input type="text" value={dec[r.id]?.decisao || ''} onChange={(e) => setDec({ ...dec, [r.id]: { ...dec[r.id], decisao: e.target.value } })} placeholder="Decisão da AG sobre o recurso…" className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`rec-dec-${r.id}`} />
                    <div className="flex flex-wrap items-center gap-2">
                      <select value={dec[r.id]?.assembleia_id || ''} onChange={(e) => setDec({ ...dec, [r.id]: { ...dec[r.id], assembleia_id: e.target.value } })} className="px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`rec-dec-assembleia-${r.id}`}>
                        <option value="">Assembleia (opcional)…</option>
                        {assembleias.map((a) => <option key={a.id} value={a.id}>{a.titulo}</option>)}
                      </select>
                      <input type="text" value={dec[r.id]?.deliberacao_id || ''} onChange={(e) => setDec({ ...dec, [r.id]: { ...dec[r.id], deliberacao_id: e.target.value } })} placeholder="ID deliberação (opcional)" className="px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`rec-dec-delib-${r.id}`} />
                      <button onClick={() => decMut.mutate({ id: r.id, data: { decisao: dec[r.id]?.decisao, assembleia_id: dec[r.id]?.assembleia_id || null, deliberacao_id: dec[r.id]?.deliberacao_id || null } })} disabled={decMut.isPending || !(dec[r.id]?.decisao || '').trim()} className="inline-flex items-center gap-1.5 bg-carmesim text-white px-3 py-2 rounded-md text-sm font-semibold hover:bg-carmesim-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`rec-dec-btn-${r.id}`}>
                        <Gavel className="w-4 h-4" aria-hidden="true" /> Decidir
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <Dialog open={showCreate} onOpenChange={(o) => { if (!o) setShowCreate(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Nova reclamação</DialogTitle><DialogDescription>Dirigida à Direcção (Art. 9.i). Tem 15 dias para resposta.</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Assunto *</label>
              <input type="text" value={form.assunto} maxLength={180} onChange={(e) => setForm({ ...form, assunto: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="rec-assunto" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Descrição *</label>
              <textarea value={form.descricao} maxLength={5000} rows={5} onChange={(e) => setForm({ ...form, descricao: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="rec-descricao" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button onClick={() => createMut.mutate()} disabled={createMut.isPending || form.assunto.trim().length < 3 || !form.descricao.trim()} className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-carmesim text-white text-sm font-semibold hover:bg-carmesim-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="rec-submit">
                {createMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Plus className="w-4 h-4" aria-hidden="true" />} Submeter
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ReclamacoesPage;
