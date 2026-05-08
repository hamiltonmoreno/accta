import React, { useEffect, useState, useCallback } from 'react';
import { financesAPI } from '../../../utils/api';
import { toast } from 'sonner';
import { Download, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import { CATEGORY_LABELS, MONTH_NAMES } from './constants';

export const DRETab = () => {
  const [year, setYear] = useState(new Date().getFullYear());
  const [dre, setDRE] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const loadDRE = useCallback(async () => {
    setLoading(true);
    try {
      const res = await financesAPI.getDRE(year);
      setDRE(res.data);
    } catch { toast.error('Erro ao carregar DRE'); }
    finally { setLoading(false); }
  }, [year]);

  useEffect(() => { loadDRE(); }, [loadDRE]);

  const handleExportPDF = async () => {
    setExporting(true);
    try {
      const res = await financesAPI.exportDREPdf(year);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `DRE_ACCTA_${year}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('PDF exportado com sucesso');
    } catch { toast.error('Erro ao exportar PDF'); }
    finally { setExporting(false); }
  };

  if (loading) {
    return <div className="p-10 text-center"><div className="inline-block w-7 h-7 border-3 border-carmesim border-t-transparent rounded-full animate-spin" /></div>;
  }
  if (!dre) return null;

  const maxMonthly = Math.max(...Object.values(dre.monthly).map((m) => Math.max(m.receitas, m.despesas)), 1);
  const calcPct = (val, total) => total > 0 ? ((val / total) * 100).toFixed(0) : '0';

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <label className="text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>Ano:</label>
        <select value={year} onChange={(e) => setYear(parseInt(e.target.value))}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-carmesim/20 focus:border-carmesim outline-none"
          data-testid="dre-year-select">
          {[2024, 2025, 2026, 2027].map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
        <button onClick={handleExportPDF} disabled={exporting || loading}
          className="ml-auto btn-primary flex items-center gap-2 text-sm" data-testid="export-dre-pdf-btn">
          <Download className={`w-4 h-4 ${exporting ? 'animate-bounce' : ''}`} />
          {exporting ? 'A exportar...' : 'Exportar PDF'}
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        <div className="card-technical p-4 sm:p-5 border-l-4 border-l-green-500">
          <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>Total Receitas</div>
          <div className="font-mono text-xl sm:text-2xl font-bold text-green-600" data-testid="dre-total-receitas">{dre.total_receitas.toLocaleString('pt')} CVE</div>
        </div>
        <div className="card-technical p-4 sm:p-5 border-l-4 border-l-red-500">
          <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>Total Despesas</div>
          <div className="font-mono text-xl sm:text-2xl font-bold text-red-600" data-testid="dre-total-despesas">{dre.total_despesas.toLocaleString('pt')} CVE</div>
        </div>
        <div className={`card-technical p-4 sm:p-5 border-l-4 ${dre.resultado_liquido >= 0 ? 'border-l-grafite' : 'border-l-orange-500'}`}>
          <div className="text-xs uppercase tracking-wider mb-1" style={{ color: 'var(--text-muted)' }}>Resultado Liquido</div>
          <div className={`font-mono text-xl sm:text-2xl font-bold ${dre.resultado_liquido >= 0 ? '' : 'text-orange-600'}`}
            style={dre.resultado_liquido >= 0 ? { color: 'var(--text-primary)' } : undefined} data-testid="dre-resultado">
            {dre.resultado_liquido.toLocaleString('pt')} CVE
          </div>
        </div>
      </div>

      {/* Monthly Chart */}
      <div className="card-technical p-4 sm:p-5">
        <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>Evolucao Mensal</h3>
        <div className="space-y-2">
          {Object.entries(dre.monthly).map(([month, data]) => (
            <div key={month} className="flex items-center gap-2 sm:gap-3" data-testid={`dre-month-${month}`}>
              <span className="text-xs font-mono w-7 text-right" style={{ color: 'var(--text-muted)' }}>{MONTH_NAMES[parseInt(month) - 1]}</span>
              <div className="flex-1 flex gap-1 h-5">
                <div className="bg-green-500 rounded-sm h-full transition-all duration-500"
                  style={{ width: `${(data.receitas / maxMonthly) * 100}%`, minWidth: data.receitas > 0 ? '2px' : '0px' }}
                  title={`Receitas: ${data.receitas.toLocaleString('pt')} CVE`} />
                <div className="bg-red-400 rounded-sm h-full transition-all duration-500"
                  style={{ width: `${(data.despesas / maxMonthly) * 100}%`, minWidth: data.despesas > 0 ? '2px' : '0px' }}
                  title={`Despesas: ${data.despesas.toLocaleString('pt')} CVE`} />
              </div>
              <span className="text-xs font-mono w-20 text-right hidden sm:block" style={{ color: 'var(--text-muted)' }}>
                {(data.receitas - data.despesas).toLocaleString('pt')}
              </span>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-4 mt-4 pt-3" style={{ borderTop: '1px solid var(--surface-border)' }}>
          <span className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--text-muted)' }}>
            <span className="w-3 h-3 bg-green-500 rounded-sm" /> Receitas
          </span>
          <span className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--text-muted)' }}>
            <span className="w-3 h-3 bg-red-400 rounded-sm" /> Despesas
          </span>
        </div>
      </div>

      {/* Category Breakdown */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="card-technical p-4 sm:p-5">
          <h3 className="font-semibold text-sm mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <ArrowUpCircle className="w-4 h-4 text-green-500" /> Receitas por Categoria
          </h3>
          {Object.keys(dre.receitas_por_categoria).length === 0 ? (
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Sem receitas neste periodo</p>
          ) : (
            <div className="space-y-2.5">
              {Object.entries(dre.receitas_por_categoria).sort((a, b) => b[1] - a[1]).map(([cat, val]) => {
                const pct = calcPct(val, dre.total_receitas);
                return (
                  <div key={cat}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs capitalize" style={{ color: 'var(--text-secondary)' }}>{CATEGORY_LABELS[cat] || cat}</span>
                      <span className="font-mono text-xs font-bold text-green-600">{val.toLocaleString('pt')} CVE <span style={{ color: 'var(--text-muted)' }} className="font-normal">({pct}%)</span></span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div className="bg-green-500 h-1.5 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="card-technical p-4 sm:p-5">
          <h3 className="font-semibold text-sm mb-3 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <ArrowDownCircle className="w-4 h-4 text-red-500" /> Despesas por Categoria
          </h3>
          {Object.keys(dre.despesas_por_categoria).length === 0 ? (
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Sem despesas neste periodo</p>
          ) : (
            <div className="space-y-2.5">
              {Object.entries(dre.despesas_por_categoria).sort((a, b) => b[1] - a[1]).map(([cat, val]) => {
                const pct = calcPct(val, dre.total_despesas);
                return (
                  <div key={cat}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs capitalize" style={{ color: 'var(--text-secondary)' }}>{CATEGORY_LABELS[cat] || cat}</span>
                      <span className="font-mono text-xs font-bold text-red-600">{val.toLocaleString('pt')} CVE <span style={{ color: 'var(--text-muted)' }} className="font-normal">({pct}%)</span></span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div className="bg-red-400 h-1.5 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
