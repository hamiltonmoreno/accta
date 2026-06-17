export const TIPO_OPTIONS = ['ordinaria', 'extraordinaria', 'eleitoral'];
export const MAIORIA_OPTIONS = ['absoluta', 'qualificada_2_3', 'qualificada_3_4_presentes', 'qualificada_3_4_universo'];

export const formatDateTime = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('pt-PT', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return '—';
  }
};

export const fieldCls = 'w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none';
export const labelCls = 'block text-xs font-medium text-[#6B7280] mb-1.5';
export const secondaryBtn = 'inline-flex items-center gap-1.5 bg-white border border-[#D1D5DB] text-[#3A3A3A] hover:bg-[#F5F5F5] rounded-md px-4 py-2 text-sm font-medium transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50';

export const EMPTY_CONVOCAR = { tipo: 'ordinaria', titulo: '', data: '', local: '', requerente_tipo: '' };
export const EMPTY_PRESENCA = { presente: null, representados: [], repCurrent: null };
export const EMPTY_DELIB = { ponto: '', descricao: '', tipo_maioria: 'absoluta', votos_favor: 0, votos_contra: 0, abstencoes: 0, source_article: '' };
