import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { esclarecimentosAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { HelpCircle, Plus, Send, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';

const KEY = ['esclarecimentos'];
const ORGAO_LABEL = { direcao: 'Direcção', mesa_ag: 'Mesa da AG', conselho_fiscal: 'Conselho Fiscal' };

export const EsclarecimentosPage = () => {
  const qc = useQueryClient();
  const { isAdmin, isDirecao, isMesaAG, isConselhoFiscal } = useAuth();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ orgao_destino: 'direcao', assunto: '', pergunta: '' });
  const [respText, setRespText] = useState({});

  const { data: itens = [], isLoading } = useQuery({ queryKey: KEY, queryFn: async () => (await esclarecimentosAPI.list()).data });
  const invalidate = () => qc.invalidateQueries({ queryKey: KEY });

  const canAnswer = (orgao) =>
    isAdmin || (orgao === 'direcao' && isDirecao) || (orgao === 'mesa_ag' && isMesaAG) || (orgao === 'conselho_fiscal' && isConselhoFiscal);

  const createMut = useMutation({
    mutationFn: () => esclarecimentosAPI.create(form),
    onSuccess: () => { toast.success('Pergunta enviada.'); invalidate(); setShowCreate(false); setForm({ orgao_destino: 'direcao', assunto: '', pergunta: '' }); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao enviar'),
  });
  const respMut = useMutation({
    mutationFn: ({ id, texto }) => esclarecimentosAPI.responder(id, texto),
    onSuccess: () => { toast.success('Resposta registada.'); invalidate(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao responder'),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title" data-testid="esclarecimentos-title">Pedidos de esclarecimento</h1>
          <p className="page-subtitle">Faça uma pergunta formal a um órgão (Direcção, Mesa da AG ou Conselho Fiscal) e receba resposta escrita (Art. 9.j).</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 bg-floresta text-white px-4 py-2 rounded-lg hover:bg-floresta-dark transition-colors text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="new-esclarecimento-btn">
          <Plus className="w-4 h-4" aria-hidden="true" /> Nova pergunta
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-24 w-full rounded-lg" />)}</div>
      ) : itens.length === 0 ? (
        <EmptyState icon={HelpCircle} title="Sem pedidos de esclarecimento" testId="no-esclarecimentos" />
      ) : (
        <div className="space-y-3">
          {itens.map((e) => (
            <div key={e.id} className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-4 space-y-2" data-testid={`esclarecimento-${e.id}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="font-semibold text-grafite">{e.assunto}</h3>
                  <p className="text-xs text-[#6B7280]">{ORGAO_LABEL[e.orgao_destino] || e.orgao_destino} · {e.created_at ? format(new Date(e.created_at), 'dd MMM yyyy', { locale: ptBR }) : ''}</p>
                </div>
                <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${e.status === 'respondido' ? 'bg-[#F0FDF4] text-[#15803D]' : 'bg-[#FFFBEB] text-[#B45309]'}`}>{e.status === 'respondido' ? 'Respondido' : 'Submetido'}</span>
              </div>
              <p className="text-sm text-grafite whitespace-pre-wrap">{e.pergunta}</p>
              {e.resposta?.text && (
                <div className="rounded-md bg-[#F5F5F5] p-3">
                  <p className="text-xs font-medium text-[#6B7280] mb-1">Resposta do órgão</p>
                  <p className="text-sm text-grafite whitespace-pre-wrap">{e.resposta.text}</p>
                </div>
              )}
              {canAnswer(e.orgao_destino) && e.status !== 'respondido' && (
                <div className="flex gap-2 pt-1">
                  <input type="text" value={respText[e.id] || ''} onChange={(ev) => setRespText({ ...respText, [e.id]: ev.target.value })} placeholder="Escreva a resposta…" className="flex-1 px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`resp-input-${e.id}`} />
                  <button onClick={() => respMut.mutate({ id: e.id, texto: respText[e.id] })} disabled={respMut.isPending || !(respText[e.id] || '').trim()} className="inline-flex items-center gap-1.5 bg-floresta text-white px-3 py-2 rounded-md text-sm font-semibold hover:bg-floresta-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid={`resp-btn-${e.id}`}>
                    <Send className="w-4 h-4" aria-hidden="true" /> Responder
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <Dialog open={showCreate} onOpenChange={(o) => { if (!o) setShowCreate(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Nova pergunta</DialogTitle><DialogDescription>Pedido de esclarecimento a um órgão (Art. 9.j).</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Órgão destinatário</label>
              <select value={form.orgao_destino} onChange={(e) => setForm({ ...form, orgao_destino: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="esc-orgao">
                <option value="direcao">Direcção</option>
                <option value="mesa_ag">Mesa da AG</option>
                <option value="conselho_fiscal">Conselho Fiscal</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Assunto *</label>
              <input type="text" value={form.assunto} maxLength={180} onChange={(e) => setForm({ ...form, assunto: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="esc-assunto" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Pergunta *</label>
              <textarea value={form.pergunta} maxLength={4000} rows={4} onChange={(e) => setForm({ ...form, pergunta: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="esc-pergunta" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button onClick={() => createMut.mutate()} disabled={createMut.isPending || form.assunto.trim().length < 3 || !form.pergunta.trim()} className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-floresta text-white text-sm font-semibold hover:bg-floresta-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="esc-submit">
                {createMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Plus className="w-4 h-4" aria-hidden="true" />} Enviar
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EsclarecimentosPage;
