import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { patrociniosAPI } from '../../utils/api';
import { Handshake, Check, X, Loader2 } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';
import { EmptyState } from '../../components/EmptyState';
import { Skeleton } from '../../components/ui/skeleton';

const PATROCINIOS_KEY = ['patrocinios', 'pendentes'];

export const PatrociniosPage = () => {
  const qc = useQueryClient();
  const { data: pedidos = [], isLoading } = useQuery({
    queryKey: PATROCINIOS_KEY,
    queryFn: async () => (await patrociniosAPI.pendentes()).data,
  });

  const respond = useMutation({
    mutationFn: ({ candidateId, action }) =>
      action === 'confirmar' ? patrociniosAPI.confirmar(candidateId) : patrociniosAPI.recusar(candidateId),
    onSuccess: (_d, vars) => {
      toast.success(vars.action === 'confirmar' ? 'Patrocínio confirmado.' : 'Patrocínio recusado.');
      qc.invalidateQueries({ queryKey: PATROCINIOS_KEY });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao responder ao patrocínio'),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title" data-testid="patrocinios-title">Patrocínios</h1>
        <p className="page-subtitle">Candidatos a sócio que o indicaram como padrinho (Art. 8.3). Confirme ou recuse.</p>
      </div>

      {isLoading ? (
        <div className="space-y-2">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-20 w-full rounded-lg" />)}</div>
      ) : pedidos.length === 0 ? (
        <EmptyState icon={Handshake} title="Nenhum patrocínio à sua espera" testId="no-patrocinios" />
      ) : (
        <div className="space-y-3">
          {pedidos.map((p) => {
            const busy = respond.isPending && respond.variables?.candidateId === p.candidate_id;
            return (
              <div
                key={p.candidate_id}
                className="bg-white rounded-lg border border-[#E5E7EB] shadow-sm p-4 flex items-center justify-between gap-4"
                data-testid={`patrocinio-${p.candidate_id}`}
              >
                <div className="min-w-0">
                  <div className="font-medium text-grafite truncate">{p.candidate_name || 'Candidato'}</div>
                  <div className="text-xs text-[#6B7280]">
                    {p.candidate_member_id ? `${p.candidate_member_id} · ` : ''}
                    {p.created_at ? format(new Date(p.created_at), 'dd MMM yyyy', { locale: ptBR }) : ''}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => respond.mutate({ candidateId: p.candidate_id, action: 'confirmar' })}
                    disabled={busy}
                    className="inline-flex items-center gap-1.5 bg-carmesim text-white px-3 py-2 rounded-md text-sm font-semibold hover:bg-carmesim-dark transition-colors cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                    data-testid={`confirmar-${p.candidate_id}`}
                  >
                    {busy ? <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> : <Check className="w-4 h-4" aria-hidden="true" />}
                    Confirmar
                  </button>
                  <button
                    onClick={() => respond.mutate({ candidateId: p.candidate_id, action: 'recusar' })}
                    disabled={busy}
                    className="inline-flex items-center gap-1.5 bg-white border border-[#D1D5DB] text-grafite px-3 py-2 rounded-md text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
                    data-testid={`recusar-${p.candidate_id}`}
                  >
                    <X className="w-4 h-4" aria-hidden="true" /> Recusar
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default PatrociniosPage;
