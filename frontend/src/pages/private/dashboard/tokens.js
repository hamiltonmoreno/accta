// Tokens e helpers partilhados pelas secções do dashboard.
import {
  Activity, Calendar, DollarSign, FolderKanban, MessageSquare, Trophy, Vote,
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const MONTH_LABELS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

export const CATEGORY_LABELS = {
  quotas: 'Quotas', patrocinios: 'Patrocinios', doacoes: 'Doacoes',
  eventos: 'Eventos', outros_receita: 'Outros',
  operacional: 'Operacional', juridico: 'Juridico',
  comunicacao: 'Comunicacao', viagens: 'Viagens', outros_despesa: 'Outros Desp.',
};

export const ACTIVITY_ICONS = {
  mural: MessageSquare,
  projeto: FolderKanban,
  evento: Calendar,
  financeiro: DollarSign,
  votacao: Vote,
  trophy: Trophy,
};

export const ACTIVITY_COLORS = {
  mural: { bg: 'bg-[#F5F5F5]', text: 'text-[#3A3A3A]' },
  projeto: { bg: 'bg-[#FFFBEB]', text: 'text-[#B45309]' },
  evento: { bg: 'bg-[#F5F5F5]', text: 'text-[#3A3A3A]' },
  financeiro: { bg: 'bg-[#F0FDF4]', text: 'text-[#15803D]' },
  votacao: { bg: 'bg-[#F5F5F5]', text: 'text-[#3A3A3A]' },
};

export { Activity };

export const timeAgo = (dateStr) => {
  if (!dateStr) return '';
  try {
    const now = new Date();
    const date = new Date(dateStr);
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return 'agora mesmo';
    if (diff < 3600) return `ha ${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `ha ${Math.floor(diff / 3600)}h`;
    if (diff < 604800) return `ha ${Math.floor(diff / 86400)}d`;
    return format(date, 'dd MMM', { locale: ptBR });
  } catch {
    return '';
  }
};
