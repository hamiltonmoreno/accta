import {
  AlertTriangle, Archive, Ban, CheckCircle2, CircleDollarSign, Clock,
  FileText, Scale, ShieldAlert, Undo2, XCircle,
} from 'lucide-react';

export const TIPO_OPTIONS = ['advertencia', 'multa', 'perda_direitos', 'expulsao'];
export const STATUS_OPTIONS = [
  'proposta', 'inquerito', 'decidida', 'recurso', 'aplicada', 'arquivada', 'anulada',
];

// Paleta semântica por tipo de sanção. perda_direitos/expulsão = graves.
export const TIPO_META = {
  advertencia: { icon: AlertTriangle, cls: 'bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]' },
  multa: { icon: CircleDollarSign, cls: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]' },
  perda_direitos: { icon: ShieldAlert, cls: 'bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]' },
  expulsao: { icon: Ban, cls: 'bg-[#FEF2F2] text-[#B91C1C] border-[#FECACA]' },
};

// Paleta semântica por estado do processo. icon + label + cor (nunca só cor).
export const STATUS_META = {
  proposta: { icon: FileText, cls: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
  inquerito: { icon: Clock, cls: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]' },
  decidida: { icon: Scale, cls: 'bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]' },
  recurso: { icon: Undo2, cls: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]' },
  aplicada: { icon: CheckCircle2, cls: 'bg-[#FEF2F2] text-[#B91C1C] border-[#FECACA]' },
  arquivada: { icon: Archive, cls: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
  anulada: { icon: XCircle, cls: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
};

export { formatDate } from '../../../lib/date';

export const formatEscudo = (v) => {
  if (v === null || v === undefined || v === '') return '—';
  const n = Number(v);
  if (Number.isNaN(n)) return '—';
  return `${n.toLocaleString('pt-PT')} CVE`;
};

// Meio-dia UTC evita o desvio de dia em fusos negativos (campo só-data).
export const isoOrNull = (dateStr) => (dateStr ? `${dateStr}T12:00:00.000Z` : null);

export const inputCls = 'w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none';
export const selectCls = `${inputCls} bg-white`;
export const secondaryBtn = 'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white border border-[#D1D5DB] text-grafite text-xs font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50';
export const cancelBtn = 'px-4 py-2 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2';

export const EMPTY_CREATE_FORM = {
  visado: null,
  tipo: 'advertencia',
  motivo: '',
  artigo_violado: '',
  multa_valor: '',
  perda_direitos_ate: '',
};

export const EMPTY_COMISSAO_FORM = { m: [null, null, null], prazo_dias: 30 };
export const EMPTY_DECIDIR_FORM = { aprovado: true, fundamentacao: '', assembleia_id: '', deliberacao_id: '' };
export const EMPTY_RECURSO_FORM = { fundamentacao: '' };
