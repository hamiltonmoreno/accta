// Tokens partilhados pelas vistas/painéis/modais de eleições.
import {
  AlertTriangle, Clock, FileSignature, ListChecks, Trophy, Vote, XCircle,
} from 'lucide-react';

export const MODO_LABELS = {
  presencial: 'Presencial',
  correspondencia: 'Correspondência',
  digital: 'Digital',
  hibrido: 'Híbrido',
};

// Mapeia cada status ao seu par semântico (icone + cor). Status = icone + texto + cor.
export const STATUS_STYLE = {
  preparacao: { icon: Clock, fg: 'text-[#6B7280]', bg: 'bg-[#F5F5F5]', ring: 'ring-[#E5E7EB]' },
  candidaturas: { icon: FileSignature, fg: 'text-[#1D4ED8]', bg: 'bg-[#EFF6FF]', ring: 'ring-[#BFDBFE]' },
  campanha: { icon: FileSignature, fg: 'text-[#1D4ED8]', bg: 'bg-[#EFF6FF]', ring: 'ring-[#BFDBFE]' },
  votacao: { icon: Vote, fg: 'text-[#B45309]', bg: 'bg-[#FFFBEB]', ring: 'ring-[#FDE68A]' },
  apurada: { icon: ListChecks, fg: 'text-[#15803D]', bg: 'bg-[#F0FDF4]', ring: 'ring-[#BBF7D0]' },
  recurso: { icon: AlertTriangle, fg: 'text-[#B45309]', bg: 'bg-[#FFFBEB]', ring: 'ring-[#FDE68A]' },
  proclamada: { icon: Trophy, fg: 'text-[#15803D]', bg: 'bg-[#F0FDF4]', ring: 'ring-[#BBF7D0]' },
  anulada: { icon: XCircle, fg: 'text-[#B91C1C]', bg: 'bg-[#FEF2F2]', ring: 'ring-[#FECACA]' },
};

export const ESTADO_LISTA_STYLE = {
  submetida: { fg: 'text-[#6B7280]', bg: 'bg-[#F5F5F5]', label: 'Submetida' },
  aceite: { fg: 'text-[#15803D]', bg: 'bg-[#F0FDF4]', label: 'Aceite' },
  rejeitada: { fg: 'text-[#B91C1C]', bg: 'bg-[#FEF2F2]', label: 'Rejeitada' },
};

export { formatDate } from '../../../lib/date';

export const fieldClass = 'w-full px-3 py-2 border border-[#E5E7EB] rounded-md text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none';
export const labelClass = 'block text-xs font-medium text-[#6B7280] mb-1.5';
export const secondaryBtn = 'px-4 py-2 rounded-md bg-white border border-[#D1D5DB] text-grafite text-sm font-medium hover:bg-[#F5F5F5] transition-colors cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 disabled:opacity-50';
