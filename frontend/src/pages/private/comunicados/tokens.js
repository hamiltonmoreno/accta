import { Ban, CheckCircle2, Clock, FileText, XCircle } from 'lucide-react';

export const PAGE_SIZE = 20;

// Rótulos PT para as chaves de órgão devolvidas por /comunicados/segments
// (mesa_ag/direcao/conselho_fiscal — distintas das chaves de ORGAO_LABELS).
export const ORGAO_SEGMENT_LABELS = {
  mesa_ag: 'Mesa da Assembleia Geral',
  direcao: 'Direcção',
  conselho_fiscal: 'Conselho Fiscal',
};

export const TIPO_LABELS = { informativo: 'Informativo', oficial: 'Oficial' };

export const SEGMENT_KIND_LABELS = {
  all_active: 'Todos os sócios ativos',
  role: 'Por função',
  member_category: 'Por categoria',
  orgao: 'Por órgão social',
  manual: 'Seleção manual',
};

export const CHANNEL_LABELS = { in_app: 'Notificação na app', email: 'E-mail' };

// Estados do dispatch -> aparência neutra; Carmesim só no estado de falha.
export const STATUS_CONFIG = {
  rascunho: { label: 'Rascunho', icon: FileText, className: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
  a_enviar: { label: 'A enviar', icon: Clock, className: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
  enviando: { label: 'A enviar', icon: Clock, className: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
  cancelado: { label: 'Cancelado', icon: Ban, className: 'bg-[#F5F5F5] text-[#6B7280] border-[#E5E7EB]' },
  enviado: { label: 'Enviado', icon: CheckCircle2, className: 'bg-[#F0FDF4] text-[#15803D] border-[#15803D]/30' },
  parcial: { label: 'Parcial', icon: Clock, className: 'bg-[#FFFBEB] text-[#B45309] border-[#B45309]/30' },
  falhado: { label: 'Falhado', icon: XCircle, className: 'bg-[#FEF2F2] text-[#B91C1C] border-[#C7202F]/40' },
};

export const formatDate = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('pt-PT', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return '—';
  }
};
