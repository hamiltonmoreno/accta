import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { exerciciosAPI, financesAPI } from '../../../utils/api';
import { useAuth } from '../../../contexts/AuthContext';
import { queryKeys } from '../../../lib/queryClient';
import { CalendarClock, Plus, Loader2, FileText, ScrollText, Landmark, CheckCircle2, AlertTriangle, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { EmptyState } from '../../../components/EmptyState';
import { Skeleton } from '../../../components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../../components/ui/dialog';
import { DocumentUploadField } from '../../../components/DocumentUploadField';
import { primaryBtn } from '../../../lib/buttonStyles';

const STEPS = [
  { key: 'aberto', label: 'Aberto' },
  { key: 'relatorio_submetido', label: 'Relatório' },
  { key: 'parecer_emitido', label: 'Parecer CF' },
  { key: 'em_aprovacao_ag', label: 'Em AG' },
  { key: 'aprovado', label: 'Aprovado' },
];
const STATUS_LABEL = {
  aberto: 'Aberto', relatorio_submetido: 'Relatório submetido', parecer_emitido: 'Parecer emitido',
  em_aprovacao_ag: 'Em aprovação na AG', aprovado: 'Aprovado', rejeitado: 'Rejeitado', reaberto: 'Reaberto',
};
const PARECER_LABEL = { favoravel: 'Favorável', favoravel_com_reservas: 'Favorável com reservas', desfavoravel: 'Desfavorável' };
const fmtCve = (v) => `${Number(v || 0).toLocaleString('pt-PT')} CVE`;
const anoAtual = new Date().getFullYear();

const Stepper = ({ status }) => {
  const idx = STEPS.findIndex((s) => s.key === status);
  const rejeitado = status === 'rejeitado';
  return (
    <div className="flex flex-wrap items-center gap-1.5" data-testid="ciclo-stepper">
      {STEPS.map((s, i) => {
        const done = idx >= 0 && i <= idx;
        return (
          <span key={s.key} className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${done ? 'bg-[#FBEAEC] text-grafite font-semibold' : 'bg-[#F5F5F5] text-[#6B7280] font-medium'}`}>
            {s.label}
          </span>
        );
      })}
      {rejeitado && <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-[#FEF2F2] text-[#B91C1C]"><AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" /> Rejeitado</span>}
    </div>
  );
};

export const PrestacaoContasTab = () => {
  const qc = useQueryClient();
  const { isAdmin, isDirecao, isConselhoFiscal, isMesaAG, can } = useAuth();
  const podeDirecao = isAdmin || isDirecao;
  const podeCF = isAdmin || isConselhoFiscal || can('emit_cf_parecer');
  const podeMesa = isAdmin || isMesaAG;

  const [selectedAno, setSelectedAno] = useState(null);
  const [dialog, setDialog] = useState(null); // 'abrir' | 'relatorio' | 'orcamento' | 'plano' | 'parecer' | 'ag' | 'aprovar'
  const [form, setForm] = useState({});

  const invalidate = () => qc.invalidateQueries({ queryKey: ['exercicios'] });

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.exercicios.list(),
    queryFn: async () => (await exerciciosAPI.list()).data,
  });
  const exercicios = useMemo(() => data?.items || [], [data]);
  const selected = useMemo(
    () => exercicios.find((e) => e.ano === selectedAno) || exercicios[0] || null,
    [exercicios, selectedAno]
  );
  const ano = selected?.ano;

  const { data: categorias } = useQuery({
    queryKey: ['finances', 'categories'],
    queryFn: async () => (await financesAPI.getCategories()).data,
    staleTime: 5 * 60 * 1000,
    enabled: podeDirecao,
  });
  const catLabel = (c) => categorias?.labels?.[c] || c;

  const { data: execucao } = useQuery({
    queryKey: queryKeys.exercicios.execucao(ano),
    queryFn: async () => (await exerciciosAPI.execucaoOrcamento(ano)).data,
    enabled: !!ano && !!selected?.orcamento,
  });

  const closeDialog = () => { setDialog(null); setForm({}); };

  const runMut = useMutation({
    mutationFn: async ({ kind, payload }) => {
      switch (kind) {
        case 'abrir': return exerciciosAPI.abrir({ ano: Number(payload.ano) });
        case 'relatorio': return exerciciosAPI.submeterRelatorio(ano, { document_id: payload.document_id.trim() });
        case 'orcamento': return exerciciosAPI.submeterOrcamento(ano, { linhas: payload.linhas, document_id: payload.document_id });
        case 'plano': return exerciciosAPI.submeterPlano(ano, { atividades: payload.atividades, document_id: payload.document_id });
        case 'parecer': return exerciciosAPI.emitirParecer(ano, { sentido: payload.sentido, texto: payload.texto.trim(), document_id: payload.document_id || undefined });
        case 'ag': return exerciciosAPI.submeterAG(ano, { assembleia_id: payload.assembleia_id.trim() });
        case 'aprovar': return exerciciosAPI.aprovar(ano, { deliberacao_id: payload.deliberacao_id.trim(), aprovado: payload.aprovado });
        case 'reabrir': return exerciciosAPI.reabrir(ano);
        default: throw new Error('ação inválida');
      }
    },
    onSuccess: (resp) => {
      const aviso = resp?.data?.aviso;
      toast.success('Operação registada.');
      if (aviso) toast.warning(aviso);
      invalidate();
      qc.invalidateQueries({ queryKey: ['exercicios', ano] });
      closeDialog();
    },
    onError: (e) => toast.error(e.response?.data?.detail || 'Erro na operação'),
  });

  // ----- editores de linhas (orçamento) e atividades (plano) -----
  const linhas = form.linhas || [];
  const setLinhas = (l) => setForm({ ...form, linhas: l });
  const atividades = form.atividades || [];
  const setAtividades = (a) => setForm({ ...form, atividades: a });

  const renderExercicioCard = (e) => {
    const isSel = selected?.ano === e.ano;
    return (
      <button
        key={e.ano}
        onClick={() => setSelectedAno(e.ano)}
        className={`text-left rounded-lg border p-4 transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 ${isSel ? 'border-[#C7202F] bg-[#FBEAEC]' : 'border-[#E5E7EB] bg-white hover:bg-[#F5F5F5]'}`}
        data-testid={`exercicio-${e.ano}`}
      >
        <p className="font-semibold text-grafite">Exercício {e.ano}</p>
        <p className="text-xs text-[#6B7280]">{STATUS_LABEL[e.status] || e.status}</p>
      </button>
    );
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-[#6B7280]">Ciclo anual: Relatório e Contas → Parecer do CF → aprovação na AG ordinária do 1.º trimestre (Art. 19.1, 31.k, 37).</p>
        {podeDirecao && (
          <button onClick={() => { setForm({ ano: anoAtual - 1 }); setDialog('abrir'); }} className="flex items-center gap-2 bg-floresta text-white px-4 py-2 rounded-lg hover:bg-floresta-dark transition-colors text-sm font-semibold cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="abrir-exercicio-btn">
            <Plus className="w-4 h-4" aria-hidden="true" /> Abrir exercício
          </button>
        )}
      </div>

      {isLoading ? (
        <Skeleton className="h-24 w-full rounded-lg" />
      ) : exercicios.length === 0 ? (
        <EmptyState icon={CalendarClock} title="Sem exercícios" description="Ainda não foi aberto nenhum exercício." testId="no-exercicios" />
      ) : (
        <>
          <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-4">{exercicios.map(renderExercicioCard)}</div>

          {selected && (
            <div className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-5 space-y-5" data-testid="exercicio-detalhe">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-grafite">Exercício {selected.ano}</h3>
                  <p className="text-xs text-[#6B7280]">{STATUS_LABEL[selected.status] || selected.status}</p>
                </div>
              </div>
              <Stepper status={selected.status} />

              {/* Resumo de peças */}
              <div className="grid gap-2 sm:grid-cols-2">
                <PecaRow icon={FileText} label="Relatório e Contas" ok={!!selected.relatorio_contas} />
                <PecaRow icon={ScrollText} label="Orçamento (ano seguinte)" ok={!!selected.orcamento} />
                <PecaRow icon={ScrollText} label="Plano de Atividades" ok={!!selected.plano_atividades} />
                <PecaRow icon={CheckCircle2} label={selected.parecer_cf ? `Parecer CF: ${PARECER_LABEL[selected.parecer_cf.sentido] || selected.parecer_cf.sentido}` : 'Parecer do CF'} ok={!!selected.parecer_cf} />
              </div>

              {/* Ações contextuais por papel/estado */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                {podeDirecao && ['aberto', 'reaberto'].includes(selected.status) && (
                  <ActionBtn onClick={() => { setForm({ document_id: '' }); setDialog('relatorio'); }} testId="act-relatorio">Submeter relatório</ActionBtn>
                )}
                {podeDirecao && !['em_aprovacao_ag', 'aprovado', 'rejeitado'].includes(selected.status) && (
                  <>
                    <ActionBtn onClick={() => { setForm({ linhas: [] }); setDialog('orcamento'); }} testId="act-orcamento">Submeter orçamento</ActionBtn>
                    <ActionBtn onClick={() => { setForm({ atividades: [] }); setDialog('plano'); }} testId="act-plano">Submeter plano</ActionBtn>
                  </>
                )}
                {podeCF && selected.status === 'relatorio_submetido' && (
                  <ActionBtn onClick={() => { setForm({ sentido: 'favoravel', texto: '' }); setDialog('parecer'); }} testId="act-parecer">Emitir parecer (CF)</ActionBtn>
                )}
                {podeMesa && selected.status === 'parecer_emitido' && (
                  <ActionBtn onClick={() => { setForm({ assembleia_id: '' }); setDialog('ag'); }} testId="act-ag">Submeter à AG</ActionBtn>
                )}
                {podeMesa && selected.status === 'em_aprovacao_ag' && (
                  <button onClick={() => { setForm({ deliberacao_id: '', aprovado: true }); setDialog('aprovar'); }} className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-floresta text-white text-sm font-semibold hover:bg-floresta-dark cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid="act-aprovar">
                    <Landmark className="w-4 h-4" aria-hidden="true" /> Registar deliberação da AG
                  </button>
                )}
                {podeMesa && ['rejeitado', 'aprovado'].includes(selected.status) && (
                  <ActionBtn onClick={() => runMut.mutate({ kind: 'reabrir' })} testId="act-reabrir">Reabrir</ActionBtn>
                )}
              </div>

              {/* Execução orçamental */}
              {execucao?.linhas?.length > 0 && (
                <div className="pt-2">
                  <h4 className="text-sm font-semibold text-grafite mb-2">Orçado vs. realizado ({execucao.ano_orcamento})</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-[#6B7280] border-b border-[#E5E7EB]">
                          <th className="py-2 pr-3 font-medium">Categoria</th>
                          <th className="py-2 px-3 font-medium text-right">Orçado</th>
                          <th className="py-2 px-3 font-medium text-right">Realizado</th>
                          <th className="py-2 pl-3 font-medium text-right">Desvio</th>
                        </tr>
                      </thead>
                      <tbody>
                        {execucao.linhas.map((l) => (
                          <tr key={`${l.tipo}-${l.categoria}`} className="border-b border-[#F5F5F5]">
                            <td className="py-2 pr-3 text-grafite">{catLabel(l.categoria)} <span className="text-xs text-[#6B7280]">({l.tipo})</span></td>
                            <td className="py-2 px-3 text-right text-grafite">{fmtCve(l.orcado)}</td>
                            <td className="py-2 px-3 text-right text-grafite">{fmtCve(l.realizado)}</td>
                            <td className={`py-2 pl-3 text-right font-medium ${l.desvio >= 0 ? 'text-[#15803D]' : 'text-[#B91C1C]'}`}>{fmtCve(l.desvio)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ---------------- Dialogs ---------------- */}
      <Dialog open={dialog === 'abrir'} onOpenChange={(o) => { if (!o) closeDialog(); }}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>Abrir exercício</DialogTitle><DialogDescription>Ano económico a reportar.</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <input type="number" min="2000" max="2100" value={form.ano || ''} onChange={(e) => setForm({ ...form, ano: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="abrir-ano" />
            <DialogActions onCancel={closeDialog} onConfirm={() => runMut.mutate({ kind: 'abrir', payload: form })} pending={runMut.isPending} label="Abrir" testId="abrir-submit" />
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={dialog === 'relatorio'} onOpenChange={(o) => { if (!o) closeDialog(); }}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>Submeter Relatório e Contas</DialogTitle><DialogDescription>O DRE do ano é congelado no momento da submissão.</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <DocumentUploadField
              kind="relatorio"
              required
              value={form.document_id}
              onChange={(id) => setForm({ ...form, document_id: id })}
              label="Relatório e Contas (PDF)"
            />
            <DialogActions onCancel={closeDialog} onConfirm={() => runMut.mutate({ kind: 'relatorio', payload: form })} pending={runMut.isPending} disabled={!form.document_id?.trim()} label="Submeter" testId="relatorio-submit" />
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={dialog === 'orcamento'} onOpenChange={(o) => { if (!o) closeDialog(); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader><DialogTitle>Submeter orçamento</DialogTitle><DialogDescription>Linhas por categoria estatutária (orçado do ano seguinte).</DialogDescription></DialogHeader>
          <div className="space-y-3">
            {linhas.map((l, i) => (
              <div key={i} className="grid grid-cols-12 gap-2 items-center">
                <select value={l.tipo} onChange={(e) => { const n = [...linhas]; n[i] = { ...l, tipo: e.target.value, categoria: '' }; setLinhas(n); }} className="col-span-3 px-2 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40">
                  <option value="receita">Receita</option>
                  <option value="despesa">Despesa</option>
                </select>
                <select value={l.categoria} onChange={(e) => { const n = [...linhas]; n[i] = { ...l, categoria: e.target.value }; setLinhas(n); }} className="col-span-5 px-2 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40">
                  <option value="">Categoria…</option>
                  {((l.tipo === 'receita' ? categorias?.income : categorias?.expense) || []).map((c) => <option key={c} value={c}>{catLabel(c)}</option>)}
                </select>
                <input type="number" min="0" placeholder="Valor" value={l.valor_previsto} onChange={(e) => { const n = [...linhas]; n[i] = { ...l, valor_previsto: e.target.value }; setLinhas(n); }} className="col-span-3 px-2 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" />
                <button onClick={() => setLinhas(linhas.filter((_, j) => j !== i))} className="col-span-1 flex justify-center text-[#6B7280] hover:text-[#B91C1C] cursor-pointer" aria-label="Remover linha"><Trash2 className="w-4 h-4" /></button>
              </div>
            ))}
            <button onClick={() => setLinhas([...linhas, { tipo: 'receita', categoria: '', valor_previsto: '' }])} className="text-sm text-[#C7202F] underline cursor-pointer">+ Adicionar linha</button>
            <DocumentUploadField
              kind="orcamento"
              value={form.document_id}
              onChange={(id) => setForm({ ...form, document_id: id })}
              label="Orçamento (PDF, opcional)"
            />
            <DialogActions
              onCancel={closeDialog}
              onConfirm={() => runMut.mutate({ kind: 'orcamento', payload: { linhas: linhas.filter((l) => l.categoria).map((l) => ({ categoria: l.categoria, tipo: l.tipo, valor_previsto: Number(l.valor_previsto || 0) })), document_id: form.document_id || undefined } })}
              pending={runMut.isPending}
              disabled={linhas.filter((l) => l.categoria).length === 0}
              label="Submeter orçamento"
              testId="orcamento-submit"
            />
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={dialog === 'plano'} onOpenChange={(o) => { if (!o) closeDialog(); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader><DialogTitle>Submeter plano de atividades</DialogTitle><DialogDescription>Atividades planeadas para o ano seguinte.</DialogDescription></DialogHeader>
          <div className="space-y-3">
            {atividades.map((a, i) => (
              <div key={i} className="grid grid-cols-12 gap-2 items-center">
                <input type="text" placeholder="Título da atividade" value={a.titulo} onChange={(e) => { const n = [...atividades]; n[i] = { ...a, titulo: e.target.value }; setAtividades(n); }} className="col-span-8 px-2 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" />
                <select value={a.trimestre || ''} onChange={(e) => { const n = [...atividades]; n[i] = { ...a, trimestre: e.target.value }; setAtividades(n); }} className="col-span-3 px-2 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40">
                  <option value="">Trim.</option>{[1, 2, 3, 4].map((t) => <option key={t} value={t}>T{t}</option>)}
                </select>
                <button onClick={() => setAtividades(atividades.filter((_, j) => j !== i))} className="col-span-1 flex justify-center text-[#6B7280] hover:text-[#B91C1C] cursor-pointer" aria-label="Remover atividade"><Trash2 className="w-4 h-4" /></button>
              </div>
            ))}
            <button onClick={() => setAtividades([...atividades, { titulo: '', trimestre: '' }])} className="text-sm text-[#C7202F] underline cursor-pointer">+ Adicionar atividade</button>
            <DocumentUploadField
              kind="plano"
              value={form.document_id}
              onChange={(id) => setForm({ ...form, document_id: id })}
              label="Plano de Atividades (PDF, opcional)"
            />
            <DialogActions
              onCancel={closeDialog}
              onConfirm={() => runMut.mutate({ kind: 'plano', payload: { atividades: atividades.filter((a) => a.titulo.trim().length >= 2).map((a) => ({ titulo: a.titulo.trim(), trimestre: a.trimestre ? Number(a.trimestre) : null })), document_id: form.document_id || undefined } })}
              pending={runMut.isPending}
              disabled={atividades.filter((a) => a.titulo.trim().length >= 2).length === 0}
              label="Submeter plano"
              testId="plano-submit"
            />
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={dialog === 'parecer'} onOpenChange={(o) => { if (!o) closeDialog(); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>Parecer do Conselho Fiscal</DialogTitle><DialogDescription>Sentido e fundamentação do parecer sobre as contas.</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Sentido</label>
              <select value={form.sentido || 'favoravel'} onChange={(e) => setForm({ ...form, sentido: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="parecer-sentido">
                {Object.entries(PARECER_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Texto do parecer *</label>
              <textarea value={form.texto || ''} maxLength={10000} rows={4} onChange={(e) => setForm({ ...form, texto: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="parecer-texto" />
            </div>
            <DocumentUploadField
              kind="parecer"
              value={form.document_id}
              onChange={(id) => setForm({ ...form, document_id: id })}
              label="Parecer do CF (PDF, opcional)"
            />
            <DialogActions onCancel={closeDialog} onConfirm={() => runMut.mutate({ kind: 'parecer', payload: form })} pending={runMut.isPending} disabled={!form.texto?.trim()} label="Emitir parecer" testId="parecer-submit" />
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={dialog === 'ag'} onOpenChange={(o) => { if (!o) closeDialog(); }}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>Submeter à AG ordinária</DialogTitle><DialogDescription>Ligar o exercício à assembleia que aprecia as contas.</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">ID da assembleia *</label>
              <input type="text" value={form.assembleia_id || ''} onChange={(e) => setForm({ ...form, assembleia_id: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="ag-assembleia" />
            </div>
            <DialogActions onCancel={closeDialog} onConfirm={() => runMut.mutate({ kind: 'ag', payload: form })} pending={runMut.isPending} disabled={!form.assembleia_id?.trim()} label="Submeter à AG" testId="ag-submit" />
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={dialog === 'aprovar'} onOpenChange={(o) => { if (!o) closeDialog(); }}>
        <DialogContent className="max-w-md">
          <DialogHeader><DialogTitle>Registar deliberação da AG</DialogTitle><DialogDescription>A aprovação das contas é da Assembleia Geral (Art. 19.1/37).</DialogDescription></DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">ID da deliberação *</label>
              <input type="text" value={form.deliberacao_id || ''} onChange={(e) => setForm({ ...form, deliberacao_id: e.target.value })} className="w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40" data-testid="aprovar-delib" />
            </div>
            <div className="flex items-center gap-2">
              <input id="ap-aprovado" type="checkbox" checked={form.aprovado !== false} onChange={(e) => setForm({ ...form, aprovado: e.target.checked })} className="h-4 w-4 accent-[#C7202F] cursor-pointer" data-testid="aprovar-aprovado" />
              <label htmlFor="ap-aprovado" className="text-sm text-grafite cursor-pointer">Contas aprovadas pela AG</label>
            </div>
            <DialogActions onCancel={closeDialog} onConfirm={() => runMut.mutate({ kind: 'aprovar', payload: form })} pending={runMut.isPending} disabled={!form.deliberacao_id?.trim()} label="Registar" testId="aprovar-submit" />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

const PecaRow = ({ icon: Icon, label, ok }) => (
  <div className="flex items-center gap-2 text-sm">
    <Icon className={`w-4 h-4 ${ok ? 'text-[#15803D]' : 'text-[#9CA3AF]'}`} aria-hidden="true" />
    <span className={ok ? 'text-grafite' : 'text-[#6B7280]'}>{label}</span>
    {ok && <CheckCircle2 className="w-3.5 h-3.5 text-[#15803D]" aria-hidden="true" />}
  </div>
);

const ActionBtn = ({ onClick, children, testId }) => (
  <button onClick={onClick} className="inline-flex items-center gap-1.5 border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2" data-testid={testId}>
    {children}
  </button>
);

const DialogActions = ({ onCancel, onConfirm, pending, disabled, label, testId }) => (
  <div className="flex justify-end gap-2">
    <button onClick={onCancel} className="px-4 py-2 rounded-md border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] cursor-pointer">Cancelar</button>
    <button onClick={onConfirm} disabled={pending || disabled} className={primaryBtn} data-testid={testId}>
      {pending ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : null} {label}
    </button>
  </div>
);

export default PrestacaoContasTab;
