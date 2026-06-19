// Fonte unica de configuracao de status/estado do Portal ACCTA.
//
// Cada entrada = { label, className, icon, dotClassName }
//   - label        : texto PT a renderizar (nunca cor sozinha)
//   - className     : par tint+texto da paleta semantica do SKILL §4
//   - icon          : componente lucide-react (sempre acompanha o label)
//   - dotClassName  : cor solida (badge dot / preenchimento) — SKILL §4 "Solid"
//
// Paleta canonica (SKILL.md §4 — "Semantic status: always icon + text"):
//   success  text-[#15803D] bg-[#F0FDF4]  · solid #16A34A · CheckCircle
//   warning  text-[#B45309] bg-[#FFFBEB]  · solid #D97706 · AlertTriangle/Clock
//   error    text-[#B91C1C] bg-[#FEF2F2]  · solid #C7202F · XCircle
//   info     text-[#1D4ED8] bg-[#EFF6FF]  · solid #2563EB · Info
//   neutro   text-[#3A3A3A] bg-[#F5F5F5]  · solid #9CA3AF · (icone conforme contexto)
//
// Carmesim (#C7202F) e o acento de MARCA, nao um estado: nunca usado para
// comunicar "ativo"/prioridade. Erro usa o #B91C1C acessivel em texto.
import {
  CheckCircle, Clock, XCircle, Info, AlertTriangle,
  FolderKanban, Flag, Calendar, DollarSign, Shield, User as UserIcon,
} from 'lucide-react';

// ---- Tons semanticos base (SKILL §4) ---------------------------------------
const TONE = {
  success: { className: 'bg-[#F0FDF4] text-[#15803D]', dotClassName: 'bg-[#16A34A]' },
  warning: { className: 'bg-[#FFFBEB] text-[#B45309]', dotClassName: 'bg-[#D97706]' },
  error: { className: 'bg-[#FEF2F2] text-[#B91C1C]', dotClassName: 'bg-[#C7202F]' },
  info: { className: 'bg-[#EFF6FF] text-[#1D4ED8]', dotClassName: 'bg-[#2563EB]' },
  neutro: { className: 'bg-[#F5F5F5] text-[#3A3A3A]', dotClassName: 'bg-[#9CA3AF]' },
};

// ---- Estado de projeto -----------------------------------------------------
// proposta/pendente -> warning · aprovado/em_curso -> info ·
// concluido -> success · cancelado -> error
export const PROJECT_STATUS_CONFIG = {
  proposta: { label: 'Proposta', icon: Clock, ...TONE.warning },
  aprovado: { label: 'Aprovado', icon: Info, ...TONE.info },
  em_curso: { label: 'Em Curso', icon: Info, ...TONE.info },
  concluido: { label: 'Concluído', icon: CheckCircle, ...TONE.success },
  cancelado: { label: 'Cancelado', icon: XCircle, ...TONE.error },
};
export const PROJECT_STATUS_FALLBACK = 'proposta';

// ---- Prioridade de tarefa --------------------------------------------------
// alta -> warning (NAO Carmesim — Carmesim e acento de marca, nao estado) ·
// media -> info · baixa -> neutro
export const TASK_PRIORITY_CONFIG = {
  baixa: { label: 'Baixa', icon: Flag, ...TONE.neutro },
  media: { label: 'Média', icon: Flag, ...TONE.info },
  alta: { label: 'Alta', icon: AlertTriangle, ...TONE.warning },
};
export const TASK_PRIORITY_FALLBACK = 'media';

// ---- Estado de tarefa (icone de toggle) ------------------------------------
// concluido -> success · em_curso -> info · pendente -> neutro
export const TASK_STATUS_CONFIG = {
  concluido: { label: 'Concluído', icon: CheckCircle, ...TONE.success },
  em_curso: { label: 'Em Curso', icon: Clock, ...TONE.info },
  pendente: { label: 'Pendente', icon: Clock, ...TONE.neutro },
};
export const TASK_STATUS_FALLBACK = 'pendente';

// ---- Tipo de evento --------------------------------------------------------
// Categoria (sem semantica de estado) -> tudo neutro; reuniao mantem destaque
// de aviso (era warning no map antigo).
export const EVENT_TYPE_CONFIG = {
  assembleia: { label: 'Assembleia', icon: Calendar, border: 'border-[#9CA3AF]', ...TONE.neutro },
  formacao: { label: 'Formação', icon: Calendar, border: 'border-[#9CA3AF]', ...TONE.neutro },
  social: { label: 'Social', icon: Calendar, border: 'border-[#9CA3AF]', ...TONE.neutro },
  reuniao: { label: 'Reunião', icon: Clock, border: 'border-[#D97706]', ...TONE.warning },
  outro: { label: 'Outro', icon: Calendar, border: 'border-[#9CA3AF]', ...TONE.neutro },
};
export const EVENT_TYPE_FALLBACK = 'outro';

// ---- Estado de utilizador --------------------------------------------------
// ativo -> success · pendente_convite/pendente_aprovacao -> warning ·
// inativo -> neutro · rejeitado -> error
// (NAO existe "inadimplente" — quotas sao descontadas em folha)
export const USER_STATUS_CONFIG = {
  ativo: { label: 'ativo', icon: CheckCircle, ...TONE.success },
  inativo: { label: 'inativo', icon: XCircle, ...TONE.neutro },
  pendente_convite: { label: 'pendente_convite', icon: Clock, ...TONE.warning },
  pendente_aprovacao: { label: 'pendente_aprovacao', icon: Clock, ...TONE.warning },
  rejeitado: { label: 'rejeitado', icon: XCircle, ...TONE.error },
};
export const USER_STATUS_FALLBACK = 'inativo';

// ---- Role (categoria — sem semantica de estado -> neutro) ------------------
export const ROLE_CONFIG = {
  admin: { label: 'Administrador', icon: Shield, ...TONE.neutro },
  socio: { label: 'Sócio', icon: UserIcon, ...TONE.neutro },
  financeiro: { label: 'Financeiro', icon: DollarSign, ...TONE.neutro },
  moderador: { label: 'Moderador', icon: Shield, ...TONE.neutro },
};
export const ROLE_FALLBACK = 'socio';

// ---- Resultado de validacao de carteira (publico) --------------------------
// valida/ativo -> success (CheckCircle) · invalida/erro -> error (XCircle)
// Sucesso e erro TEM de ficar visualmente distintos (nunca ambos Carmesim).
export const WALLET_VALIDATION_CONFIG = {
  valida: { label: 'Carteira Válida', icon: CheckCircle, ...TONE.success },
  invalida: { label: 'Carteira Inválida', icon: XCircle, ...TONE.error },
};

const NEUTRAL_ENTRY = { label: '—', icon: FolderKanban, ...TONE.neutro };

// Lookup seguro: devolve a entrada do map, ou o fallback, ou um neutro.
export function getStatusConfig(map, key, fallbackKey) {
  if (map && Object.prototype.hasOwnProperty.call(map, key)) return map[key];
  if (map && fallbackKey && Object.prototype.hasOwnProperty.call(map, fallbackKey)) {
    return map[fallbackKey];
  }
  return NEUTRAL_ENTRY;
}
