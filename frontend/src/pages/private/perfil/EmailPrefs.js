import React from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Mail } from 'lucide-react';
import { Switch } from '../../../components/ui/switch';
import { comunicadosAPI } from '../../../utils/api';

export const EmailPrefs = ({ user, refreshUser }) => {
  // Preferência de comunicados informativos por email. O switch reflecte se o
  // sócio RECEBE (ON) — o campo persistido é o opt-OUT, logo invertemos.
  const emailPrefsMutation = useMutation({
    mutationFn: (data) => comunicadosAPI.updateEmailPreferences(data),
    onSuccess: async () => {
      if (refreshUser) await refreshUser();
      toast.success('Preferência de email atualizada.');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Erro ao atualizar a preferência de email.');
    },
  });

  return (
    <div className="card-technical p-5 animate-fade-up" data-testid="email-prefs-section">
      <h3 className="font-semibold text-xs uppercase tracking-widest text-[#6B7280] mb-3">
        <Mail className="w-3 h-3 inline mr-1" aria-hidden="true" /> Preferências de Email
      </h3>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <label htmlFor="email-opt-informativos" className="text-sm font-medium text-grafite block">
            Receber comunicados informativos por email
          </label>
          <p className="text-xs text-[#6B7280] mt-1">
            Os comunicados oficiais (convocatórias, deliberações) chegam sempre.
          </p>
        </div>
        <Switch
          id="email-opt-informativos"
          checked={!user.email_opt_out_informativos}
          disabled={emailPrefsMutation.isPending}
          onCheckedChange={(checked) =>
            emailPrefsMutation.mutate({ email_opt_out_informativos: !checked })
          }
          data-testid="email-opt-informativos-switch"
        />
      </div>
      <div className="flex items-start justify-between gap-4 mt-4 pt-4 border-t border-[#E5E7EB]">
        <div className="min-w-0">
          <label htmlFor="quota-reminder-opt" className="text-sm font-medium text-grafite block">
            Receber lembretes de quota
          </label>
          <p className="text-xs text-[#6B7280] mt-1">
            Aviso informativo na app quando uma quota é registada, com o total acumulado. Sem cobrança.
          </p>
        </div>
        <Switch
          id="quota-reminder-opt"
          checked={!user.quota_reminder_opt_out}
          disabled={emailPrefsMutation.isPending}
          onCheckedChange={(checked) =>
            emailPrefsMutation.mutate({ quota_reminder_opt_out: !checked })
          }
          data-testid="quota-reminder-opt-switch"
        />
      </div>
    </div>
  );
};
