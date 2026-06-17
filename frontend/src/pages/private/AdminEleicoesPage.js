import React, { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { eleicoesAPI, governanceAPI } from '../../utils/api';
import { queryKeys } from '../../lib/queryClient';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { Vote, ListChecks, Plus, Hash } from 'lucide-react';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';
import { primaryBtn } from '../../lib/buttonStyles';

import { StatusBadge } from './eleicoes/StatusBadge';
import { CriarEleicaoModal } from './eleicoes/CriarEleicaoModal';
import { EleicaoDetail } from './eleicoes/EleicaoDetail';

// Re-exporta os componentes testados para manter o contrato de
// `require('../AdminEleicoesPage')` da suite AdminEleicoesPage.test.js.
export { ValidarListaModal } from './eleicoes/ValidarListaModal';
export { VotoCorrespondenciaModal } from './eleicoes/VotoCorrespondenciaModal';

export const AdminEleicoesPage = () => {
  const qc = useQueryClient();
  const { isAdmin, isMesaAG, isVotingMember } = useAuth();
  const canManage = isAdmin || isMesaAG;

  const [selectedId, setSelectedId] = useState(null);
  const [criarOpen, setCriarOpen] = useState(false);

  const { data: structure } = useQuery({
    queryKey: queryKeys.governance.structure(),
    queryFn: async () => (await governanceAPI.structure()).data,
    staleTime: 60 * 60 * 1000,
  });

  const { data: listResp, isLoading } = useQuery({
    queryKey: queryKeys.eleicoes.list(),
    queryFn: async () => (await eleicoesAPI.list()).data,
  });

  const eleicoes = useMemo(() => listResp?.eleicoes || [], [listResp]);

  // Selecciona a primeira eleição por defeito.
  useEffect(() => {
    if (!selectedId && eleicoes.length > 0) setSelectedId(eleicoes[0].id);
  }, [eleicoes, selectedId]);

  const criarMutation = useMutation({
    mutationFn: (data) => eleicoesAPI.create(data),
    onSuccess: (res) => {
      toast.success('Eleição criada.');
      setCriarOpen(false);
      qc.invalidateQueries({ queryKey: ['eleicoes'] });
      const newId = res.data?.id;
      if (newId) setSelectedId(newId);
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao criar a eleição'),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-carmesim/10 flex items-center justify-center">
            <Vote className="w-5 h-5 text-carmesim" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-grafite">Eleições</h1>
            <p className="text-sm text-[#6B7280]">Listas, votação e apuramento dos órgãos sociais. O voto é secreto.</p>
          </div>
        </div>
        {canManage && (
          <button type="button" onClick={() => setCriarOpen(true)} className={primaryBtn} data-testid="criar-eleicao-btn">
            <Plus className="w-4 h-4 inline -mt-0.5 mr-1.5" aria-hidden="true" />Criar eleição
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
          <div className="space-y-2">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}</div>
          <Skeleton className="h-64 w-full rounded-lg" />
        </div>
      ) : eleicoes.length === 0 ? (
        <EmptyState icon={ListChecks} title="Sem eleições" description="Ainda não foi criada nenhuma eleição." testId="no-eleicoes" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6 items-start">
          {/* Master: lista de eleições */}
          <nav className="space-y-2" aria-label="Eleições">
            {eleicoes.map((e) => {
              const active = e.id === selectedId;
              return (
                <button
                  key={e.id}
                  type="button"
                  onClick={() => setSelectedId(e.id)}
                  className={`w-full text-left rounded-lg border p-4 transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 ${active ? 'border-carmesim bg-carmesim/5' : 'border-[#E5E7EB] bg-white hover:bg-[#F5F5F5]'}`}
                  data-testid={`eleicao-item-${e.id}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-1.5 text-sm font-semibold text-grafite">
                      <Hash className="w-3.5 h-3.5 text-[#6B7280]" aria-hidden="true" />Eleição {e.ano}
                    </span>
                  </div>
                  <div className="mt-2"><StatusBadge status={e.status} /></div>
                </button>
              );
            })}
          </nav>

          {/* Detail */}
          <div>
            {selectedId ? (
              <EleicaoDetail
                eleicaoId={selectedId}
                structure={structure}
                canManage={canManage}
                isVotingMember={isVotingMember}
                qc={qc}
              />
            ) : (
              <EmptyState icon={Vote} title="Selecione uma eleição" testId="no-selection" />
            )}
          </div>
        </div>
      )}

      <CriarEleicaoModal
        open={criarOpen}
        onClose={() => setCriarOpen(false)}
        onSubmit={(data) => criarMutation.mutate(data)}
        pending={criarMutation.isPending}
      />
    </div>
  );
};

export default AdminEleicoesPage;
