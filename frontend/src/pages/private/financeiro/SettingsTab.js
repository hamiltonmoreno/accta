import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { financesAPI } from '../../../utils/api';
import { toast } from 'sonner';
import { DollarSign, Settings, RefreshCw, CheckCircle, Users } from 'lucide-react';
import { MONTH_NAMES } from './constants';

export const SettingsTab = () => {
  const [settings, setSettings] = useState(null);
  const [quotaAmount, setQuotaAmount] = useState('');
  const [quotaDesc, setQuotaDesc] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [genMonth, setGenMonth] = useState(new Date().getMonth() + 1);
  const [genYear, setGenYear] = useState(new Date().getFullYear());
  const [genResult, setGenResult] = useState(null);

  useEffect(() => { loadSettings(); }, []);

  const loadSettings = async () => {
    try {
      const res = await financesAPI.getSettings();
      setSettings(res.data);
      setQuotaAmount(res.data.quota_amount);
      setQuotaDesc(res.data.quota_description);
    } catch { toast.error('Erro ao carregar configuracoes'); }
    finally { setLoading(false); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await financesAPI.updateSettings({ quota_amount: parseFloat(quotaAmount), quota_description: quotaDesc });
      toast.success('Configuracoes atualizadas');
      loadSettings();
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro ao salvar'); }
    finally { setSaving(false); }
  };

  const handleGenerate = async () => {
    if (!window.confirm(`Gerar quotas de ${MONTH_NAMES[genMonth - 1]}/${genYear} para todos os socios ativos?`)) return;
    setGenerating(true);
    setGenResult(null);
    try {
      const res = await financesAPI.generateQuotas(genMonth, genYear);
      setGenResult(res.data);
      toast.success(res.data.message);
    } catch (err) { toast.error(err.response?.data?.detail || 'Erro ao gerar quotas'); }
    finally { setGenerating(false); }
  };

  if (loading) {
    return <div className="p-10 text-center"><div className="inline-block w-7 h-7 border-3 border-carmesim border-t-transparent rounded-full animate-spin" /></div>;
  }

  return (
    <div className="space-y-5">
      <div className="card-technical p-5 sm:p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
          <Settings className="w-4 h-4 text-carmesim" /> Configuracao de Quotas
        </h3>
        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Valor da Quota Mensal (CVE)</label>
            <input type="number" inputMode="decimal" min="0" value={quotaAmount} onChange={(e) => setQuotaAmount(e.target.value)}
              className="w-full max-w-xs px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="quota-amount-input" />
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Descricao da Quota</label>
            <input type="text" value={quotaDesc} onChange={(e) => setQuotaDesc(e.target.value)}
              className="w-full max-w-sm px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="quota-desc-input" />
          </div>
          <button onClick={handleSave} disabled={saving} className="btn-primary text-sm px-6" data-testid="save-settings-btn">
            {saving ? 'A guardar...' : 'Guardar Configuracoes'}
          </button>
        </div>
      </div>

      <div className="card-technical p-5 sm:p-6">
        <h3 className="font-semibold mb-2 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
          <RefreshCw className="w-4 h-4 text-carmesim" /> Gerar Quotas Mensais
        </h3>
        <p className="text-xs mb-4 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
          Gera automaticamente as quotas mensais para todos os socios ativos. Socios que ja possuem quota para o mes selecionado serao ignorados.
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Mes</label>
            <select value={genMonth} onChange={(e) => setGenMonth(parseInt(e.target.value))}
              className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="gen-month-select">
              {MONTH_NAMES.map((name, i) => <option key={i} value={i + 1}>{name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 block">Ano</label>
            <select value={genYear} onChange={(e) => setGenYear(parseInt(e.target.value))}
              className="px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
              data-testid="gen-year-select">
              {[2024, 2025, 2026, 2027].map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary text-sm px-5 flex items-center gap-2" data-testid="generate-quotas-btn">
            <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'A gerar...' : 'Gerar Quotas'}
          </button>
        </div>

        {genResult && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg" data-testid="gen-result">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="font-semibold text-sm text-green-700">Quotas Geradas com Sucesso</span>
            </div>
            <div className="grid grid-cols-3 gap-3 mt-2">
              <div className="text-center">
                <div className="font-mono text-lg font-bold text-green-700" data-testid="gen-created">{genResult.created}</div>
                <div className="text-[10px] text-green-600 uppercase tracking-wider">Criadas</div>
              </div>
              <div className="text-center">
                <div className="font-mono text-lg font-bold text-gray-500" data-testid="gen-skipped">{genResult.skipped}</div>
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">Ignoradas</div>
              </div>
              <div className="text-center">
                <div className="font-mono text-lg font-bold" style={{ color: 'var(--text-primary)' }} data-testid="gen-total-value">{genResult.total_value?.toLocaleString('pt')}</div>
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">CVE Total</div>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      <div className="card-technical p-4 sm:p-5 border-l-4 border-l-carmesim bg-carmesim/5">
        <div className="flex items-start gap-3">
          <DollarSign className="w-5 h-5 text-carmesim flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm mb-1" style={{ color: 'var(--text-primary)' }}>Desconto em Folha</h4>
            <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
              As quotas dos socios ativos sao descontadas diretamente na folha de pagamento. Nao existe o conceito de "socio inadimplente" nesta associacao.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
