import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { benefitsAPI } from '../../utils/api';
import { Gift, MapPin, Percent, ExternalLink, Phone, Tag } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import { queryKeys } from '../../lib/queryClient';
import { EmptyState } from '../../components/EmptyState';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../../components/ui/alert-dialog';

export const BeneficiosPage = () => {
  const { isAtivo } = useAuth();
  const [confirmId, setConfirmId] = useState(null);
  const qc = useQueryClient();

  const { data: benefits = [], isLoading } = useQuery({
    queryKey: queryKeys.benefits.list(),
    queryFn: async () => {
      const res = await benefitsAPI.getAll();
      return res.data;
    },
  });

  const validateMutation = useMutation({
    mutationFn: (id) => benefitsAPI.validate(id),
    onSuccess: () => {
      toast.success('Utilização registada com sucesso');
      // Invalidate para o validation_count voltar atualizado.
      qc.invalidateQueries({ queryKey: queryKeys.benefits.list() });
      setConfirmId(null);
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || 'Erro ao registar utilização');
      setConfirmId(null);
    },
  });

  const handleValidate = () => {
    if (!confirmId) return;
    validateMutation.mutate(confirmId);
  };

  const mapsUrl = (loc) => {
    if (loc.latitude != null && loc.longitude != null) {
      return `https://www.google.com/maps/search/?api=1&query=${loc.latitude},${loc.longitude}`;
    }
    const q = encodeURIComponent(`${loc.name} ${loc.address || ''} ${loc.city || ''}`.trim());
    return `https://www.google.com/maps/search/?api=1&query=${q}`;
  };

  const confirmedBenefit = benefits.find((b) => b.id === confirmId);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="page-title" data-testid="benefits-title">
          Clube de Benefícios
        </h1>
        <p className="page-subtitle">Descontos exclusivos para sócios ACCTA em parceiros selecionados</p>
      </div>

      {/* Status Alert */}
      {!isAtivo && (
        <div className="card-technical rounded-xl p-6 border-2 border-alert" data-testid="benefits-restricted">
          <div className="flex items-start gap-4">
            <Gift className="w-6 h-6 text-[#B91C1C] flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-sans font-semibold text-lg text-[#B91C1C] mb-2">Benefícios Restritos</h3>
              <p className="text-gray-600">
                Apenas sócios com status ativo têm acesso ao clube de benefícios. Por favor, regularize sua situação.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Info Card */}
      {isAtivo && (
        <div className="card-technical rounded-xl p-6 bg-carmesim/5 border-carmesim/20 animate-fade-up">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-carmesim rounded-lg flex items-center justify-center flex-shrink-0">
              <Gift className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-sans font-semibold text-lg text-grafite mb-2">Como Usar</h3>
              <p className="text-gray-600 mb-3">
                Apresente sua carteira digital nos estabelecimentos parceiros para validar seu status de sócio e aproveitar os descontos.
              </p>
              <p className="text-sm text-gray-500">
                Todos os descontos são válidos mediante apresentação do QR Code da carteira digital.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Benefits Grid */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
        </div>
      ) : benefits.length === 0 ? (
        <EmptyState
          icon={Gift}
          title="Nenhum benefício disponível no momento"
          testId="no-benefits"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {benefits.map((benefit, index) => (
            <div key={benefit.id}
              className="card-technical rounded-xl overflow-hidden hover:shadow-xl transition-shadow animate-fade-up"
              data-testid={`benefit-${benefit.id}`}>
              {benefit.logo_url && (
                <div className="h-48 bg-gray-100 flex items-center justify-center p-6">
                  <img src={benefit.logo_url} alt={benefit.name} className="max-h-full max-w-full object-contain" />
                </div>
              )}

              <div className="p-6">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <h3 className="font-sans font-semibold text-2xl text-grafite">{benefit.name}</h3>
                  {benefit.category && (
                    <span className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-wider text-grafite bg-grafite/5 px-2 py-1 rounded">
                      <Tag className="w-3 h-3" />
                      {benefit.category}
                    </span>
                  )}
                </div>
                <p className="text-gray-600 mb-4 line-clamp-3">{benefit.description}</p>

                {benefit.locations && benefit.locations.length > 0 && (
                  <div className="mb-4 space-y-2">
                    <p className="text-xs font-semibold text-grafite uppercase tracking-wider">Parceiros</p>
                    {benefit.locations.map((loc, idx) => (
                      <div key={idx} className="text-sm bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <div className="font-semibold text-grafite mb-1">{loc.name}</div>
                        {loc.address && (
                          <a
                            href={mapsUrl(loc)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-start gap-1.5 text-xs text-gray-600 hover:text-carmesim transition-colors"
                          >
                            <MapPin className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                            <span>{[loc.address, loc.city].filter(Boolean).join(', ')}</span>
                          </a>
                        )}
                        {loc.phone && (
                          <a
                            href={`tel:${loc.phone}`}
                            className="inline-flex items-center gap-1.5 text-xs text-gray-600 hover:text-carmesim transition-colors mt-1"
                          >
                            <Phone className="w-3.5 h-3.5" />
                            <span>{loc.phone}</span>
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {benefit.website && (
                  <a
                    href={benefit.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs text-grafite hover:text-carmesim mb-4"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Visitar website
                  </a>
                )}

                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="flex items-center gap-2">
                    <Percent className="w-5 h-5 text-carmesim" />
                    <span className="font-mono font-bold text-2xl text-carmesim">{benefit.discount_percent}%</span>
                  </div>
                  <div className="text-xs font-mono text-gray-500 uppercase">
                    {benefit.validation_count} usos
                  </div>
                </div>

                {isAtivo && (
                  <button
                    type="button"
                    onClick={() => setConfirmId(benefit.id)}
                    className="mt-4 w-full bg-carmesim text-white text-sm font-semibold py-2.5 rounded-lg hover:bg-carmesim/90 transition-colors disabled:opacity-50"
                    data-testid={`validate-benefit-${benefit.id}`}
                  >
                    Registar Utilização
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Confirmation dialog — prevents accidental clicks from inflating the counter */}
      <AlertDialog open={confirmId !== null} onOpenChange={(open) => !open && setConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar utilização do benefício</AlertDialogTitle>
            <AlertDialogDescription>
              {confirmedBenefit
                ? `Vais registar uma utilização do benefício "${confirmedBenefit.name}". Esta ação fica registada no teu perfil e no audit log da associação.`
                : 'Confirma que pretendes registar a utilização deste benefício.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={validateMutation.isPending}>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleValidate} disabled={validateMutation.isPending}>
              {validateMutation.isPending ? 'A registar...' : 'Confirmar'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
