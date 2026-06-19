import React, { useEffect, useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { financesAPI } from '../../../utils/api';
import { toast } from 'sonner';
import { DollarSign, Settings, RefreshCw, CheckCircle, Users } from 'lucide-react';
import { MONTH_NAMES } from './constants';
import { Skeleton } from '../../../components/ui/skeleton';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '../../../components/ui/alert-dialog';

export const buildSettingsUpdate = ({ settings, quotaAmount, quotaDesc, assembleiaId, deliberacaoId }) => {
  const nextAmount = parseFloat(quotaAmount);
  const quotaChanged = Number.isFinite(nextAmount) && nextAmount !== Number(settings?.quota_amount);
  const payload = { quota_description: quotaDesc };

  if (quotaChanged) {
    payload.quota_amount = nextAmount;
    payload.assembleia_id = assembleiaId.trim();
    payload.deliberacao_id = deliberacaoId.trim();
  }

  return payload;
};

export const SettingsTab = () => {
  const qc = useQueryClient();
  const [quotaAmount, setQuotaAmount] = useState('');
  const [quotaDesc, setQuotaDesc] = useState('');
  const [assembleiaId, setAssembleiaId] = useState('');
  const [deliberacaoId, setDeliberacaoId] = useState('');
  const [genMonth, setGenMonth] = useState(new Date().getMonth() + 1);
  const [genYear, setGenYear] = useState(new Date().getFullYear());
  const [genResult, setGenResult] = useState(null);
  const [confirmGen, setConfirmGen] = useState(false);

  const { data: settings, isLoading: loading } = useQuery({
    queryKey: ['finance', 'settings'],
    queryFn: async () => (await financesAPI.getSettings()).data,
  });

  // Inicializa os campos do formulário só na 1ª vez que settings chegam. Após
  // isso o utilizador é dono do form: um refetch (ex.: invalidate pós-save) não
  // sobrescreve o que ele estiver a editar.
  const initializedRef = useRef(false);
  useEffect(() => {
    if (settings && !initializedRef.current) {
      initializedRef.current = true;
      setQuotaAmount(settings.quota_amount);
      setQuotaDesc(settings.quota_description);
    }
  }, [settings]);

  const updateMutation = useMutation({
    mutationFn: (data) => financesAPI.updateSettings(data),
    onSuccess: () => {
      toast.success('Configuracoes atualizadas');
      qc.invalidateQueries({ queryKey: ['finance', 'settings'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao salvar'),
  });

  const generateMutation = useMutation({
    mutationFn: ({ month, year }) => financesAPI.generateQuotas(month, year),
    onSuccess: (res) => {
      setGenResult(res.data);
      toast.success(res.data.message);
      // As quotas geradas são transactions — invalidar a vista admin e a
      // vista self-service do sócio (Minhas Quotas).
      qc.invalidateQueries({ queryKey: ['transactions'] });
      qc.invalidateQueries({ queryKey: ['finances', 'me', 'quotas'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Erro ao gerar quotas'),
  });

  const saving = updateMutation.isPending;
  const generating = generateMutation.isPending;
  const parsedQuotaAmount = parseFloat(quotaAmount);
  const quotaChanged = Number.isFinite(parsedQuotaAmount) && parsedQuotaAmount !== Number(settings?.quota_amount);
  const validQuotaAmount = Number.isFinite(parsedQuotaAmount) && parsedQuotaAmount > 0;
  const hasQuotaDeliberacao = !!assembleiaId.trim() && !!deliberacaoId.trim();

  const handleSave = () => {
    updateMutation.mutate(buildSettingsUpdate({
      settings,
      quotaAmount,
      quotaDesc,
      assembleiaId,
      deliberacaoId,
    }));
  };

  const handleGenerate = () => setConfirmGen(true);

  const confirmGenerate = () => {
    setConfirmGen(false);
    setGenResult(null);
    generateMutation.mutate({ month: genMonth, year: genYear });
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-28 w-full rounded-lg" />
        <Skeleton className="h-28 w-full rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="card-technical p-5 sm:p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2 text-grafite-auto">
          <Settings className="w-4 h-4 text-carmesim" /> Configuracao de Quotas
        </h3>
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Valor da Quota Mensal (CVE)</label>
            <input type="number" inputMode="decimal" min="0" value={quotaAmount} onChange={(e) => setQuotaAmount(e.target.value)}
              className="w-full max-w-xs px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="quota-amount-input" />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Descricao da Quota</label>
            <input type="text" value={quotaDesc} onChange={(e) => setQuotaDesc(e.target.value)}
              className="w-full max-w-sm px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="quota-desc-input" />
          </div>
          {quotaChanged && (
            <div className="grid gap-3 sm:grid-cols-2 max-w-xl">
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">ID Assembleia</label>
                <input type="text" value={assembleiaId} onChange={(e) => setAssembleiaId(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                  data-testid="quota-assembleia-id" />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">ID Deliberacao 3/4</label>
                <input type="text" value={deliberacaoId} onChange={(e) => setDeliberacaoId(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
                  data-testid="quota-deliberacao-id" />
              </div>
            </div>
          )}
          <button onClick={handleSave} disabled={saving || !validQuotaAmount || (quotaChanged && !hasQuotaDeliberacao)} className="btn-primary text-sm px-6" data-testid="save-settings-btn">
            {saving ? 'A guardar...' : 'Guardar Configuracoes'}
          </button>
        </div>
      </div>

      <div className="card-technical p-5 sm:p-6">
        <h3 className="font-semibold mb-2 flex items-center gap-2 text-grafite-auto">
          <RefreshCw className="w-4 h-4 text-carmesim" /> Gerar Quotas Mensais
        </h3>
        <p className="text-xs mb-4 leading-relaxed text-muted-auto">
          Gera automaticamente as quotas mensais para todos os socios ativos. Socios que ja possuem quota para o mes selecionado serao ignorados.
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Mes</label>
            <select value={genMonth} onChange={(e) => setGenMonth(parseInt(e.target.value))}
              className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="gen-month-select">
              {MONTH_NAMES.map((name, i) => <option key={i} value={i + 1}>{name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Ano</label>
            <select value={genYear} onChange={(e) => setGenYear(parseInt(e.target.value))}
              className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim outline-none"
              data-testid="gen-year-select">
              {[2024, 2025, 2026, 2027].map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
          <button onClick={handleGenerate} disabled={generating} className="btn-outline text-sm px-5 flex items-center gap-2" data-testid="generate-quotas-btn">
            <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'A gerar...' : 'Gerar Quotas'}
          </button>
        </div>

        {genResult && (
          <div className="mt-4 p-4 bg-[#F0FDF4] border border-[#BBF7D0] rounded-lg animate-fade-up" data-testid="gen-result">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-4 h-4 text-[#15803D]" />
              <span className="font-semibold text-sm text-[#15803D]">Quotas Geradas com Sucesso</span>
            </div>
            <div className="grid grid-cols-3 gap-3 mt-2">
              <div className="text-center">
                <div className="font-mono text-lg font-bold text-[#15803D]" data-testid="gen-created">{genResult.created}</div>
                <div className="text-xs text-[#15803D] uppercase tracking-wider">Criadas</div>
              </div>
              <div className="text-center">
                <div className="font-mono text-lg font-bold text-gray-500" data-testid="gen-skipped">{genResult.skipped}</div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">Ignoradas</div>
              </div>
              <div className="text-center">
                <div className="font-mono text-lg font-bold text-grafite-auto" data-testid="gen-total-value">{genResult.total_value?.toLocaleString('pt')}</div>
                <div className="text-xs text-gray-500 uppercase tracking-wider">CVE Total</div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="card-technical p-4 sm:p-5 border-l-4 border-l-carmesim bg-carmesim/5">
        <div className="flex items-start gap-3">
          <DollarSign className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm mb-1 text-grafite-auto">Desconto em Folha</h4>
            <p className="text-xs leading-relaxed text-secondary-auto">
              As quotas dos sócios ativos são descontadas diretamente na folha de pagamento. Não existe o conceito de "sócio inadimplente" nesta associação.
            </p>
          </div>
        </div>
      </div>

      <AlertDialog open={confirmGen} onOpenChange={setConfirmGen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Gerar quotas mensais?</AlertDialogTitle>
            <AlertDialogDescription>
              Serão geradas as quotas de {MONTH_NAMES[genMonth - 1]}/{genYear} para todos os sócios ativos. Sócios que já tenham quota neste mês serão ignorados.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={confirmGenerate}>Gerar</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
