// Strings de classe canónicas para botões compostos à mão (páginas que não usam
// o primitivo <Button> de components/ui/button.jsx). Fonte única para a taxonomia
// de cor de ação se manter consistente. Ver tasks/spec-botoes-cor-acao.md.
//
// Taxonomia (psicologia da cor + UX):
//   primaryBtn          → ação POSITIVA (Guardar/Aprovar/Submeter/Criar/Entrar…)  = Floresta sólido
//   destructiveBtn      → ação DESTRUTIVA/negativa (Apagar/Rejeitar/Suspender…)   = outline Carmesim
//   destructiveSolidBtn → só confirmação IRREVERSÍVEL dentro de diálogo            = Carmesim cheio
//   secondaryBtn        → NEUTRA (Cancelar/Fechar/Filtrar/Exportar/Voltar…)        = branco + borda
//   ghostBtn            → terciária/discreta (logout, ações de linha)              = transparente
//
// Carmesim #C7202F mantém-se como IDENTIDADE de marca (links, nav ativa, anel de
// foco, realces de erro) — nunca como botão primário positivo.

const RING =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2';

const BASE =
  `inline-flex items-center justify-center gap-1.5 rounded-md px-4 py-2 text-sm transition-colors cursor-pointer disabled:opacity-50 disabled:pointer-events-none ${RING}`;

export const primaryBtn = `${BASE} font-semibold bg-floresta text-white hover:bg-floresta-dark`;

export const destructiveBtn = `${BASE} font-semibold bg-white border border-carmesim text-carmesim hover:bg-carmesim-50`;

export const destructiveSolidBtn = `${BASE} font-semibold bg-carmesim text-white hover:bg-carmesim-dark`;

export const secondaryBtn = `${BASE} font-medium bg-white border border-[#D1D5DB] text-[#3A3A3A] hover:bg-[#F5F5F5]`;

export const ghostBtn = `${BASE} font-medium text-[#3A3A3A] hover:bg-[#F5F5F5]`;
