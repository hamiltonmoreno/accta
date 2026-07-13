// Tokens partilhados pelos painéis da sala de assembleia.
import { Calendar, CheckCircle2, ShieldCheck, XCircle } from 'lucide-react';

export const secondaryBtn =
  'inline-flex items-center gap-1.5 bg-white border border-[#D1D5DB] text-[#3A3A3A] hover:bg-[#F5F5F5] rounded-md px-3 py-1.5 text-sm font-medium transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50';
export const dangerBtn =
  'inline-flex items-center gap-1.5 bg-white border border-[#FECACA] text-[#B91C1C] hover:bg-[#FEF2F2] rounded-md px-3 py-1.5 text-sm font-medium transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 disabled:opacity-50';
export const fieldCls =
  'w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none';
export const labelCls = 'block text-xs font-medium text-[#6B7280] mb-1.5';
export const cardCls = 'rounded-lg border border-[#E5E7EB] bg-white p-5';
export const sectionTitle = 'text-sm font-semibold text-[#3A3A3A] uppercase tracking-wide';

export const PHASE_ORDER = ['fechada', 'checkin', 'antes_ot', 'ordem_trabalhos', 'encerramento'];

export const STATUS_STYLES = {
  rascunho: { cls: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]', Icon: Calendar },
  convocada: { cls: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]', Icon: Calendar },
  em_curso: { cls: 'bg-[#FFFBEB] text-[#B45309] border-[#FDE68A]', Icon: ShieldCheck },
  encerrada: { cls: 'bg-[#F0FDF4] text-[#15803D] border-[#BBF7D0]', Icon: CheckCircle2 },
  anulada: { cls: 'bg-[#FEF2F2] text-[#B91C1C] border-[#FECACA]', Icon: XCircle },
};

export { formatDateTime } from '../../../lib/date';
