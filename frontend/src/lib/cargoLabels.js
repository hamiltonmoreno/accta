// Rótulos PT (apresentação) para roles e privilégios. A LISTA canónica de
// cargos/privilégios vem SEMPRE do backend (GET /users/meta/cargos) — aqui
// ficam apenas as traduções legíveis, partilhadas pelas páginas de admin/perfil.

export const ROLE_LABELS = {
  admin: 'Administrador',
  socio: 'Sócio',
  // spec 018: já não são níveis atribuíveis (viraram funções seed) — os
  // rótulos ficam só para exibir dados históricos (audit logs, mandatos).
  financeiro: 'Financeiro',
  moderador: 'Moderador',
};

export const PRIVILEGE_LABELS = {
  manage_users: 'Gerir Utilizadores',
  manage_finances: 'Gerir Finanças',
  manage_events: 'Gerir Eventos',
  manage_documents: 'Gerir Documentos',
  moderate_content: 'Moderar Conteúdo',
  manage_benefits: 'Gerir Benefícios',
  view_audit_logs: 'Ver Audit Logs',
  view_finances_readonly: 'Ver Finanças (leitura)',
  emit_cf_parecer: 'Emitir Parecer (Conselho Fiscal)',
  send_comunicados: 'Enviar Comunicados',
  comunicar_intra_orgao: 'Comunicar entre Órgãos',
  manage_ranking: 'Gerir Ranking',
};

export const roleLabel = (role) => ROLE_LABELS[role] || role || '—';
export const privilegeLabel = (priv) => PRIVILEGE_LABELS[priv] || priv;
