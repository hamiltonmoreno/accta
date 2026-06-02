import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { regulamentosAPI, documentsAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import { ScrollText, Plus, Loader2, Download, Send, CheckCircle2, Ban, FilePlus2 } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';

const COMPETENCIA_LABEL = { direcao: 'Direção', assembleia_geral: 'Assembleia Geral' };
const VERSAO_STATUS = {
  rascunho: { label: 'Rascunho', cls: 'bg-[#F5F5F5] text-[#6B7280]' },
  em_aprovacao: { label: 'Em aprovação', cls: 'bg-[#FFFBEB] text-[#B45309]' },
  aprovado: { label: 'Em vigor', cls: 'bg-[#F0FDF4] text-[#15803D]' },
  revogado: { label: 'Revogado', cls: 'bg-[#F5F5F5] text-[#6B7280]' },
};
const fmtDate = (d) => (d ? format(new Date(d), 'dd MMM yyyy', { locale: ptBR }) : '');

export const RegulamentosPage = () => {
  const qc = useQueryClient();
  const { isAdmin, isDirecao, isMesaAG } = useAuth();
  const podeGerir = isAdmin || isDirecao;

  const [selectedId, setSelectedId] = useState(null);
  const [dialog, setDialog] = useState(null); // 'criar' | 'versao' | 'aprovar'
  const [form, setForm] = useState({});
  const [aprovarCtx, setAprovarCtx] = useState(null); // { vid, competencia }

  const invalidate = () => qc.invalidateQueries({ queryKey: ['regulamentos'] });
  const closeDialog = () => { setDialog(null); setForm({}); setAprovarCtx(null); };

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.regulamentos.list(),
    queryFn: async () => (await regulamentosAPI.list()).data,
  });
  const regulamentos = data?.items || [];

  const { data: detail } = useQuery({
    queryKey: queryKeys.regulamentos.byId(selectedId),
    queryFn: async () => (await regulamentosAPI.get(selectedId)).data,
    enabled: !!selectedId,
  });

  const refreshDetail = () => { invalidate(); if (selectedId) qc.invalidateQueries({ queryKey: ['regulamentos', selectedId] }); };

  const criarMut = useMutation({
    mutationFn: () => regulamentosAPI.create({ slug: form.slug.trim(), titulo: form.titulo.trim(), descricao: form.descricao?.trim() || null, competencia_aprovacao: form.competencia_aprovacao || 'direcao' }),
    onSuccess: () => { toast.success('Regulamento criado.'); invalidate(); closeDialog(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao criar regulamento'),
  });
  const versaoMut = useMutation({
    mutationFn: () => regulamentosAPI.criarVersao(selectedId, { document_id: form.document_id.trim(), changelog: form.changelog?.trim() || null }),
    onSuccess: () => { toast.success('Versão criada (rascunho).'); refreshDetail(); closeDialog(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao criar versão'),
  });
  const submeterMut = useMutation({
    mutationFn: (vid) => regulamentosAPI.submeterVersao(selectedId, vid),
    onSuccess: () => { toast.success('Versão submetida a aprovação.'); refreshDetail(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao submeter'),
  });
  const aprovarMut = useMutation({
    mutationFn: ({ vid, competencia }) =>
      regulamentosAPI.aprovarVersao(
        selectedId,
        vid,
        competencia === 'assembleia_geral'
          ? { deliberacao_id: form.deliberacao_id?.trim(), assembleia_id: form.assembleia_id?.trim() || null }
          : {}
      ),
    onSuccess: () => { toast.success('Versão aprovada e em vigor.'); refreshDetail(); closeDialog(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao aprovar'),
  });
  const revogarMut = useMutation({
    mutationFn: (vid) => regulamentosAPI.revogarVersao(selectedId, vid),
    onSuccess: () => { toast.success('Versão revogada.'); refreshDetail(); },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro ao revogar'),
  });

  const openAprovar = (versao, competencia) => {
    if (competencia === 'assembleia_geral') {
      // Competência da AG: precisa de uma deliberação → abre diálogo.
      setAprovarCtx({ vid: versao.id, competencia });
      setForm({ deliberacao_id: '', assembleia_id: '' });
      setDialog('aprovar');
    } else {
      // Competência da Direção: aprova directamente.
      aprovarMut.mutate({ vid: versao.id, competencia });
    }
  };

  const renderVersao = (v, competencia) => {
    const st = VERSAO_STATUS[v.status] || VERSAO_STATUS.rascunho;
    const podeAGaprovar = competencia === 'assembleia_geral' ? (isAdmin || isMesaAG) : podeGerir;
    return (
      <div key={v.id} className="flex items-start justify-between gap-3 py-3 border-b border-[#F5F5F5] last:border-0" data-testid={`versao-${v.id}`}>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-grafite">v{v.versao}</span>
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${st.cls}`}>{st.label}</span>
          </div>
          {v.changelog && <p className="text-xs text-[#6B7280] mt-0.5">{v.changelog}</p>}
          <p className="text-xs text-[#6B7280] mt-0.5">{v.effective_from ? `Em vigor desde ${fmtDate(v.effective_from)}` : `Criada ${fmtDate(v.created_at)}`}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          {v.document_id && (
            <a href={documentsAPI.downloadUrl(v.document_id)} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-[#C7202F] underline cursor-pointer" data-testid={`download-${v.id}`}>
              <Download className="w-3.5 h-3.5" aria-hidden="true" /> Documento
            </a>
          )}
          {podeGerir && v.status === 'rascunho' && (
            <IconBtn onClick={() => submeterMut.mutate(v.id)} icon={Send} label="Submeter" testId={`submeter-${v.id}`} />
          )}
          {podeAGaprovar && v.status === 'em_aprovacao' && (
            <IconBtn onClick={() => openAprovar(v, competencia)} icon={CheckCircle2} label="Aprovar" testId={`aprovar-${v.id}`} />
          )}
          {podeGerir && ['aprovado', 'em_aprovacao'].includes(v.status) && (
            <IconBtn onClick={() => revogarMut.mutate(v.id)} icon={Ban} label="Revogar" testId={`revogar-${v.id}`} />
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title" data-testid="regulamentos-title">Regulamentos</h1>
          <p className="page-subtitle">Repositório versionado de regulamentos internos. O Regimento da AG e outros de competência da Assembleia exigem deliberação para entrar em vigor (Art. 31.j, 56).</p>
        </div>
        {podeGerir && (
          <button onClick={() => { setForm({ competencia_aprovacao: 'direcao' }); setDialog('criar'); }} className="flex items-center gap-2 bg-floresta text-white px-4 py-2 rounded-lg hover:bg-floresta-dark transition-colors text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="novo-regulamento-btn">
            <Plus className="w-4 h-4" aria-hidden="true" /> Novo regulamento
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-20 w-full rounded-lg" />)}</div>
      ) : regulamentos.length === 0 ? (
        <EmptyState icon={ScrollText} title="Sem regulamentos" description="Ainda não há regulamentos registados." testId="no-regulamentos" />
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {regulamentos.map((r) => {
            const cur = r.current_version;
            const isSel = selectedId === r.id;
            return (
              <div key={r.id} className={`rounded-lg border p-4 transition-all ${isSel ? 'border-[#C7202F]' : 'border-[#E5E7EB]'} bg-white shadow-sm`} data-testid={`regulamento-${r.id}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-grafite">{r.titulo}</h3>
                    <p className="text-xs text-[#6B7280]">
                      {COMPETENCIA_LABEL[r.competencia_aprovacao] || r.competencia_aprovacao}
                      {cur ? ` · em vigor: v${cur.versao}` : ' · sem versão em vigor'}
                    </p>
                  </div>
                </div>
                {r.descricao && <p className="text-sm text-[#6B7280] mt-2">{r.descricao}</p>}
                <button onClick={() => setSelectedId(isSel ? null : r.id)} className="mt-3 text-sm text-[#C7202F] underline cursor-pointer" data-testid={`detalhe-${r.id}`}>
                  {isSel ? 'Ocultar versões' : 'Ver versões'}
                </button>

                {isSel && (
                  <div className="mt-3 border-t border-[#E5E7EB] pt-3">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="text-xs font-semibold uppercase tracking-[0.12em] text-[#6B7280]">Histórico</h4>
                      {podeGerir && (
                        <button onClick={() => { setForm({ document_id: '', changelog: '' }); setDialog('versao'); }} className="inline-flex items-center gap-1 text-xs text-[#C7202F] underline cursor-pointer" data-testid="nova-versao-btn">
                          <FilePlus2 className="w-3.5 h-3.5" aria-hidden="true" /> Nova versão
                        </button>
                      )}
                    </div>
                    {detail?.versoes?.length ? (
                      <div>{detail.versoes.map((v) => renderVersao(v, r.competencia_aprovacao))}</div>
                    ) : (
                      <p className="text-xs text-[#6B7280] py-2">Sem versões ainda.</p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Criar regulamento */}
      <Dialog open={dialog === 'criar'} onOpenChange={(o) => { if (!o) closeDialog(); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Novo regulamento</DialogTitle><DialogDescription>Define a competência de aprovação (Direção ou Assembleia Geral).</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-[#6B7280] mb-1">Slug *</label>
                <input type="text" value={form.slug || ''} placeholder="regulamento-x" maxLength={80} onChange={(e) => setForm({ ...form, slug: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="reg-slug" />
              </div>
              <div>
                <label className="block text-xs font-medium text-[#6B7280] mb-1">Competência</label>
                <select value={form.competencia_aprovacao || 'direcao'} onChange={(e) => setForm({ ...form, competencia_aprovacao: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="reg-competencia">
                  <option value="direcao">Direção</option>
                  <option value="assembleia_geral">Assembleia Geral</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Título *</label>
              <input type="text" value={form.titulo || ''} maxLength={200} onChange={(e) => setForm({ ...form, titulo: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="reg-titulo" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Descrição</label>
              <textarea value={form.descricao || ''} maxLength={2000} rows={2} onChange={(e) => setForm({ ...form, descricao: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="reg-descricao" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={closeDialog} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button onClick={() => criarMut.mutate()} disabled={criarMut.isPending || !form.slug?.trim() || !form.titulo?.trim()} className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-floresta text-white text-sm font-semibold hover:bg-floresta-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="reg-submit">
                {criarMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Plus className="w-4 h-4" aria-hidden="true" />} Criar
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Nova versão */}
      <Dialog open={dialog === 'versao'} onOpenChange={(o) => { if (!o) closeDialog(); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Nova versão</DialogTitle><DialogDescription>Anexe o documento (PDF) carregado e descreva as alterações.</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">ID do documento *</label>
              <input type="text" value={form.document_id || ''} onChange={(e) => setForm({ ...form, document_id: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="versao-doc" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Changelog</label>
              <textarea value={form.changelog || ''} maxLength={2000} rows={2} onChange={(e) => setForm({ ...form, changelog: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="versao-changelog" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={closeDialog} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button onClick={() => versaoMut.mutate()} disabled={versaoMut.isPending || !form.document_id?.trim()} className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-floresta text-white text-sm font-semibold hover:bg-floresta-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="versao-submit">
                {versaoMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <FilePlus2 className="w-4 h-4" aria-hidden="true" />} Criar versão
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Aprovar (competência AG → deliberação) */}
      <Dialog open={dialog === 'aprovar'} onOpenChange={(o) => { if (!o) closeDialog(); }}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>Aprovar versão (Assembleia Geral)</DialogTitle><DialogDescription>Esta competência exige uma deliberação aprovada da AG.</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">ID da deliberação *</label>
              <input type="text" value={form.deliberacao_id || ''} onChange={(e) => setForm({ ...form, deliberacao_id: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="aprovar-delib" />
            </div>
            <div className="flex justify-end gap-2">
              <button onClick={closeDialog} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
              <button onClick={() => aprovarMut.mutate({ vid: aprovarCtx?.vid, competencia: 'assembleia_geral' })} disabled={aprovarMut.isPending || !form.deliberacao_id?.trim()} className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-floresta text-white text-sm font-semibold hover:bg-floresta-dark cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="aprovar-ag-submit">
                {aprovarMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <CheckCircle2 className="w-4 h-4" aria-hidden="true" />} Aprovar
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const IconBtn = ({ onClick, icon: Icon, label, testId }) => (
  <button onClick={onClick} className="inline-flex items-center gap-1 border border-[#D1D5DB] text-grafite px-2.5 py-1.5 rounded-md text-xs font-medium hover:bg-[#F5F5F5] cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid={testId}>
    <Icon className="w-3.5 h-3.5 text-[#6B7280]" aria-hidden="true" /> {label}
  </button>
);

export default RegulamentosPage;
