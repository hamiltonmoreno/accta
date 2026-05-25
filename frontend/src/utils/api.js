import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Sprint 10 — JWT em httpOnly cookie em vez de localStorage. withCredentials
// faz o axios incluir o cookie cross-origin (requer backend CORS allow_credentials
// + cookie SameSite=None;Secure em prod).
const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

// Handle 401 errors — dispatch event for AuthContext to handle
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      const publicPaths = ['/login', '/validador', '/profissao', '/noticias', '/transparencia', '/sobre', '/beneficios-publico', '/contactos', '/eventos-publico', '/galeria', '/forgot-password', '/reset-password', '/criar-conta'];
      const isPublic = currentPath === '/' || publicPaths.some(p => currentPath.startsWith(p));
      if (!isPublic) {
        // Cookie e httpOnly — JS nao consegue limpa-lo. Backend ja invalida
        // server-side em /logout; aqui so disparamos o evento + redirect.
        window.dispatchEvent(new Event('accta:force-logout'));
        window.location.replace('/login');
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
  setupAccount: (data) => api.post('/auth/setup-account', data),
  validateInvite: (token) => api.get('/auth/invite/validate', { params: { token } }),
  forgotPassword: (data) => api.post('/auth/forgot-password', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
};

// Admin API
export const adminAPI = {
  invite: (data) => api.post('/admin/invite', data),
  getPendingInvites: () => api.get('/admin/invites/pending'),
  revokeInvite: (userId) => api.delete(`/admin/invite/${userId}`),
};

// Auto-registo de sócios (spec-auto-registo)
export const registrationAPI = {
  options: () => api.get('/auth/registration-options'),
  submit: (payload) => api.post('/auth/register', payload),
  listPending: (params) => api.get('/admin/registration-requests', { params }),
  approve: (userId, data) => api.post(`/admin/registration-requests/${userId}/approve`, data),
  reject: (userId, reason) => api.post(`/admin/registration-requests/${userId}/reject`, { reason }),
};

// Patrocínio de admissão (spec-voz-participacao §3, Art. 8.3)
export const patrociniosAPI = {
  pendentes: () => api.get('/participacao/patrocinios/pendentes'),
  confirmar: (candidateId, note) => api.post(`/participacao/patrocinios/${candidateId}/confirmar`, { note }),
  recusar: (candidateId, note) => api.post(`/participacao/patrocinios/${candidateId}/recusar`, { note }),
};

// Petição para AG extraordinária (spec-voz-participacao §5, Art. 9.f/19.2.d)
export const peticoesAPI = {
  list: () => api.get('/peticoes'),
  get: (id) => api.get(`/peticoes/${id}`),
  create: (data) => api.post('/peticoes', data),
  assinar: (id) => api.post(`/peticoes/${id}/assinar`),
  retirar: (id) => api.delete(`/peticoes/${id}/assinar`),
  encaminhar: (id, assembleiaId) => api.post(`/peticoes/${id}/encaminhar`, { assembleia_id: assembleiaId }),
};

// Pedidos de esclarecimento (spec-voz-participacao §8, Art. 9.j)
export const esclarecimentosAPI = {
  list: () => api.get('/esclarecimentos'),
  get: (id) => api.get(`/esclarecimentos/${id}`),
  create: (data) => api.post('/esclarecimentos', data),
  responder: (id, texto) => api.post(`/esclarecimentos/${id}/responder`, { texto }),
};

// Comunicados e preferências de email (spec-comunicados-email)
export const comunicadosAPI = {
  list: (params) => api.get('/comunicados', { params }),
  get: (id) => api.get(`/comunicados/${id}`),
  create: (data) => api.post('/comunicados', data),
  recipientsCount: (data) => api.post('/comunicados/recipients/count', data),
  segments: () => api.get('/comunicados/segments'),
  updateEmailPreferences: (data) => api.patch('/me/email-preferences', data),
};

// Reclamações e recursos (spec-voz-participacao §7, Art. 9.i)
export const reclamacoesAPI = {
  list: () => api.get('/reclamacoes'),
  get: (id) => api.get(`/reclamacoes/${id}`),
  create: (data) => api.post('/reclamacoes', data),
  responder: (id, data) => api.post(`/reclamacoes/${id}/responder`, data),
  recurso: (id) => api.post(`/reclamacoes/${id}/recurso`),
  decidirRecurso: (id, data) => api.post(`/reclamacoes/${id}/decidir-recurso`, data),
};

// Propostas e temas para a ordem de trabalhos (spec-voz-participacao §6, Art. 9.g/9.h)
export const propostasAgAPI = {
  list: (status) => api.get('/propostas-ag', { params: status ? { status } : {} }),
  get: (id) => api.get(`/propostas-ag/${id}`),
  create: (data) => api.post('/propostas-ag', data),
  triar: (id, data) => api.post(`/propostas-ag/${id}/triagem`, data),
  incluir: (id, data) => api.post(`/propostas-ag/${id}/incluir`, data),
};

// Membros honorários (spec-voz-participacao §4, Art. 8.4): nomeação + votação 2/3
export const honorariosAPI = {
  list: (status) => api.get('/honorarios', { params: status ? { status } : {} }),
  get: (id) => api.get(`/honorarios/${id}`),
  create: (data) => api.post('/honorarios', data),
  abrirVotacao: (id) => api.post(`/honorarios/${id}/abrir-votacao`),
  apurar: (id) => api.post(`/honorarios/${id}/apurar`),
  // F6 — reconciliação §2.4: ligar nomeação apurada à deliberação da AG.
  ligar: (id, data) => api.post(`/honorarios/${id}/ligar-assembleia`, data),
};

// Cargos / mandatos (spec-identidade-cargos / spec-governanca)
export const cargosAPI = {
  getMeta: () => api.get('/users/meta/cargos'),  // [DEPRECATED] usar governanceAPI.structure
  list: () => api.get('/admin/cargos'),
  candidates: (params) => api.get('/admin/cargos/candidates', { params }),
  promote: (userId, data) => api.post(`/admin/users/${userId}/promote`, data),
  demote: (userId, data) => api.post(`/admin/users/${userId}/demote`, data),
  transfer: (data) => api.post('/admin/cargos/transfer', data),
  history: (userId) => api.get(`/users/${userId}/cargo-history`),
};

// Governança estatutária — estrutura canónica (spec-governanca §9)
export const governanceAPI = {
  structure: () => api.get('/governance/structure'),
};

// Banners de página (spec-padronizacao-banners)
export const bannersAPI = {
  getPublic: () => api.get('/banners/public'),
  getAll: () => api.get('/banners'),
  update: (key, data) => api.put(`/banners/${key}`, data),
};

// Marca / logo (spec-gestao-logo-marca)
export const brandAPI = {
  getPublic: () => api.get('/brand/public'),
  getAll: () => api.get('/brand'),
  update: (data) => api.patch('/brand', data),
};

// Assembleia Geral (spec-governanca §11)
export const assembleiasAPI = {
  list: (params) => api.get('/assembleias', { params }),
  get: (id) => api.get(`/assembleias/${id}`),
  create: (data) => api.post('/assembleias', data),
  quorum: (id) => api.get(`/assembleias/${id}/quorum`),
  addPresenca: (id, data) => api.post(`/assembleias/${id}/presencas`, data),
  deliberacoes: (id) => api.get(`/assembleias/${id}/deliberacoes`),
  addDeliberacao: (id, data) => api.post(`/assembleias/${id}/deliberacoes`, data),
  encerrar: (id, params) => api.post(`/assembleias/${id}/encerrar`, null, { params }),
};

// Eleições (spec-governanca §12)
export const eleicoesAPI = {
  list: (params) => api.get('/eleicoes', { params }),
  get: (id) => api.get(`/eleicoes/${id}`),
  create: (data) => api.post('/eleicoes', data),
  listas: (id) => api.get(`/eleicoes/${id}/listas`),
  submitLista: (id, data) => api.post(`/eleicoes/${id}/listas`, data),
  validarLista: (id, listaId, data) => api.post(`/eleicoes/${id}/listas/${listaId}/validar`, data),
  abrirVotacao: (id) => api.post(`/eleicoes/${id}/abrir-votacao`),
  votar: (id, data) => api.post(`/eleicoes/${id}/votar`, data),
  votoCorrespondencia: (id, data) => api.post(`/eleicoes/${id}/voto-correspondencia`, data),
  apurar: (id) => api.post(`/eleicoes/${id}/apurar`),
  proclamar: (id) => api.post(`/eleicoes/${id}/proclamar`),
};

// Regime disciplinar (spec-governanca §13)
export const sancoesAPI = {
  list: (params) => api.get('/sancoes', { params }),
  get: (id) => api.get(`/sancoes/${id}`),
  create: (data) => api.post('/sancoes', data),
  comissao: (id, data) => api.post(`/sancoes/${id}/comissao`, data),
  decidir: (id, data) => api.post(`/sancoes/${id}/decidir`, data),
  recurso: (id, data) => api.post(`/sancoes/${id}/recurso`, data),
  aplicar: (id) => api.post(`/sancoes/${id}/aplicar`),
  ofUser: (userId) => api.get(`/users/${userId}/sancoes`),
};

// Users API
export const usersAPI = {
  getAll: (params) => api.get('/users', { params }),
  getById: (userId) => api.get(`/users/${userId}`),
  updateProfile: (data) => api.patch('/users/me/profile', data),
  adminUpdate: (userId, data) => api.patch(`/users/${userId}`, data),
  updateStatus: (userId, status) => api.patch(`/users/${userId}/status`, null, { params: { status } }),
  delete: (userId) => api.delete(`/users/${userId}`),
  getCargos: () => api.get('/users/meta/cargos'),
  getPrivileges: () => api.get('/users/meta/privileges'),
};

// Invoices API
export const invoicesAPI = {
  getAll: () => api.get('/invoices'),
  create: (data) => api.post('/invoices', data),
  confirm: (invoiceId) => api.patch(`/invoices/${invoiceId}/confirm`),
};

// Finances API
export const financesAPI = {
  getTransactions: (params) => api.get('/finances/transactions', { params }),
  getTransactionCount: (params) => api.get('/finances/transactions/count', { params }),
  exportTransactionsCsv: (params) => api.get('/finances/transactions/csv', { params, responseType: 'blob' }),
  createTransaction: (data) => api.post('/finances/transactions', data),
  updateTransaction: (id, data) => api.patch(`/finances/transactions/${id}`, data),
  deleteTransaction: (id) => api.delete(`/finances/transactions/${id}`),
  getSummary: (params) => api.get('/finances/summary', { params }),
  getDRE: (year) => api.get('/finances/dre', { params: { year } }),
  exportDREPdf: (year) => api.get(`/finances/dre/pdf?year=${year}`, { responseType: 'blob' }),
  getSettings: () => api.get('/finances/settings'),
  updateSettings: (data) => api.patch('/finances/settings', data),
  generateQuotas: (month, year) => api.post(`/finances/generate-quotas?month=${month}&year=${year}`),
  getCategories: () => api.get('/finances/meta/categories'),
  getJoiaPreview: (userId, ctaQualifiedSince) =>
    api.get('/finances/joia/preview', {
      params: { user_id: userId, ...(ctaQualifiedSince ? { cta_qualified_since: ctaQualifiedSince } : {}) },
    }),
};

// Atos (co-aprovação / dupla assinatura — Art. 54). Módulo próprio (/atos).
export const atosAPI = {
  list: (params) => api.get('/atos', { params }),
  get: (id) => api.get(`/atos/${id}`),
  create: (data) => api.post('/atos', data),
  assinar: (id, decisao) => api.post(`/atos/${id}/assinar`, { decisao }),
  executar: (id, data) => api.post(`/atos/${id}/executar`, data || {}),
  cancelar: (id) => api.post(`/atos/${id}/cancelar`),
};

// Ciclo de prestação de contas — exercícios (spec-ciclo §4). Módulo /exercicios.
export const exerciciosAPI = {
  list: () => api.get('/exercicios'),
  get: (ano) => api.get(`/exercicios/${ano}`),
  abrir: (data) => api.post('/exercicios', data),
  submeterRelatorio: (ano, data) => api.post(`/exercicios/${ano}/relatorio`, data),
  submeterOrcamento: (ano, data) => api.post(`/exercicios/${ano}/orcamento`, data),
  submeterPlano: (ano, data) => api.post(`/exercicios/${ano}/plano`, data),
  emitirParecer: (ano, data) => api.post(`/exercicios/${ano}/parecer`, data),
  submeterAG: (ano, data) => api.post(`/exercicios/${ano}/submeter-ag`, data),
  aprovar: (ano, data) => api.post(`/exercicios/${ano}/aprovar`, data),
  reabrir: (ano) => api.post(`/exercicios/${ano}/reabrir`),
  execucaoOrcamento: (ano) => api.get(`/exercicios/${ano}/orcamento/execucao`),
};

// Balancetes periódicos / balanço anual (spec-ciclo §5). Módulo /balancetes.
export const balancetesAPI = {
  list: (params) => api.get('/balancetes', { params }),
  get: (id) => api.get(`/balancetes/${id}`),
  publicar: (data) => api.post('/balancetes', data),
  auditar: (id, data) => api.post(`/balancetes/${id}/auditar`, data),
};

// Regulamentos internos versionados (spec-ciclo §6). Módulo /regulamentos.
export const regulamentosAPI = {
  list: () => api.get('/regulamentos'),
  get: (id) => api.get(`/regulamentos/${id}`),
  create: (data) => api.post('/regulamentos', data),
  criarVersao: (id, data) => api.post(`/regulamentos/${id}/versoes`, data),
  submeterVersao: (id, vid) => api.post(`/regulamentos/${id}/versoes/${vid}/submeter`),
  aprovarVersao: (id, vid, data) => api.post(`/regulamentos/${id}/versoes/${vid}/aprovar`, data || {}),
  revogarVersao: (id, vid, data) => api.post(`/regulamentos/${id}/versoes/${vid}/revogar`, data || {}),
};

// Documentos de prestação de contas (multipart). Cria o registo `documents`
// com visibilidade/título por política server-side a partir de `kind`.
export const prestacaoContasAPI = {
  uploadDocumento: (file, { kind, title } = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('kind', kind);
    if (title) formData.append('title', title);
    return api.post('/prestacao-contas/documentos', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Polls API
export const pollsAPI = {
  getAll: () => api.get('/polls'),
  create: (data) => api.post('/polls', data),
  vote: (data) => api.post('/polls/vote', data),
  getResults: (pollId) => api.get(`/polls/${pollId}/results`),
};

// Posts API
export const postsAPI = {
  // Compat: chamadas antigas passam string `getAll('publico')`; novas passam
  // objeto de params `{ visibility, type, status, q, skip, limit }`.
  getAll: (params) => api.get('/posts', {
    params: typeof params === 'string' ? { visibility: params } : (params || {}),
  }),
  getOne: (idOrSlug) => api.get(`/posts/${idOrSlug}`),
  create: (data) => api.post('/posts', data),
  update: (id, data) => api.patch(`/posts/${id}`, data),
  remove: (id) => api.delete(`/posts/${id}`),
};

// Documents API
export const documentsAPI = {
  getPublic: () => api.get('/documents/public'),
  getAll: () => api.get('/documents'),
  create: (data) => api.post('/documents', data),
  publicDownloadUrl: (documentId) => `${API_BASE}/documents/public/${documentId}/download`,
  downloadUrl: (documentId) => `${API_BASE}/documents/${documentId}/download`,
  registerAccess: (documentId) => api.post(`/documents/${documentId}/access`),
};

// Contact API
export const contactAPI = {
  submit: (data) => api.post('/contact', data),
};

// Upload API
export const uploadAPI = {
  uploadFile: (category, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/upload/${category}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  deleteFile: (category, filename) => api.delete(`/upload/${category}/${filename}`),
};

// Benefits API
export const benefitsAPI = {
  getAll: () => api.get('/benefits'),
  getPublic: () => api.get('/benefits/public'),
  create: (data) => api.post('/benefits', data),
  update: (id, data) => api.patch(`/benefits/${id}`, data),
  remove: (id) => api.delete(`/benefits/${id}`),
  validate: (id) => api.post(`/benefits/${id}/validate`),
};

// Wall API
export const wallAPI = {
  getPosts: (category) => api.get('/wall', { params: { category } }),
  getPending: () => api.get('/wall/pending'),
  create: (data) => api.post('/wall', data),
  approve: (postId) => api.patch(`/wall/${postId}/approve`),
  delete: (postId) => api.delete(`/wall/${postId}`),
  pin: (postId) => api.patch(`/wall/${postId}/pin`),
  like: (postId) => api.patch(`/wall/${postId}/like`),
  getComments: (postId) => api.get(`/wall/${postId}/comments`),
  createComment: (postId, data) => api.post(`/wall/${postId}/comments`, data),
  deleteComment: (postId, commentId) => api.delete(`/wall/${postId}/comments/${commentId}`),
};

// Validator API
export const validatorAPI = {
  validate: (qrHash) => api.get(`/validate/${qrHash}`),
};

// Audit Logs API
export const auditAPI = {
  getLogs: (params = {}) => api.get('/audit-logs', { params }),
};

// Statistics API
export const statsAPI = {
  get: () => api.get('/stats'),
};

// Activity Feed API
export const activityAPI = {
  getRecent: (limit = 15) => api.get('/activity/recent', { params: { limit } }),
};
export const notificationsAPI = {
  getAll: (params) => api.get('/notifications', { params }),
  getUnreadCount: () => api.get('/notifications/unread/count'),
  markRead: (notificationId) => api.patch(`/notifications/${notificationId}/read`),
  markAllRead: () => api.patch('/notifications/mark-all-read'),
  delete: (notificationId) => api.delete(`/notifications/${notificationId}`),
  clearRead: () => api.delete('/notifications/clear/all'),
  broadcast: (data) => api.post('/notifications/broadcast', data),
  create: (data) => api.post('/notifications', data),
  getTypes: () => api.get('/notifications/types'),
};

// Events API
export const eventsAPI = {
  getAll: (visibility) => api.get('/events', { params: { visibility } }),
  getPublic: () => api.get('/events/public'),
  getUpcoming: () => api.get('/events/upcoming'),
  getFeatured: () => api.get('/events/featured'),
  getById: (eventId) => api.get(`/events/${eventId}`),
  create: (data) => api.post('/events', data),
  update: (eventId, data) => api.patch(`/events/${eventId}`, data),
  delete: (eventId) => api.delete(`/events/${eventId}`),
  register: (eventId) => api.post(`/events/${eventId}/register`),
  unregister: (eventId) => api.delete(`/events/${eventId}/register`),
  getAttendees: (eventId) => api.get(`/events/${eventId}/attendees`),
};

// Gallery API
export const galleryAPI = {
  // Public (no auth)
  getPublicAlbums: () => api.get('/gallery/public/albums'),
  getPublicPhotos: (albumId) => api.get('/gallery/public/photos', { params: albumId ? { album_id: albumId } : {} }),
  // Authenticated
  getAlbums: () => api.get('/gallery/albums'),
  getAlbum: (albumId) => api.get(`/gallery/albums/${albumId}`),
  createAlbum: (data) => api.post('/gallery/albums', data),
  updateAlbum: (albumId, data) => api.patch(`/gallery/albums/${albumId}`, data),
  deleteAlbum: (albumId) => api.delete(`/gallery/albums/${albumId}`),
  getPhotos: (albumId, status) => api.get('/gallery/photos', { params: { ...(albumId && { album_id: albumId }), ...(status && { status }) } }),
  getPending: () => api.get('/gallery/photos/pending'),
  uploadPhoto: (albumId, file, caption) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/gallery/photos/upload?album_id=${albumId}&caption=${encodeURIComponent(caption || '')}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  approvePhoto: (photoId) => api.patch(`/gallery/photos/${photoId}/approve`),
  rejectPhoto: (photoId) => api.patch(`/gallery/photos/${photoId}/reject`),
  deletePhoto: (photoId) => api.delete(`/gallery/photos/${photoId}`),
};

// Projects API
export const projectsAPI = {
  getAll: (params) => api.get('/projects', { params }),
  getOne: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.patch(`/projects/${id}`, data),
  approve: (id) => api.patch(`/projects/${id}/approve`),
  delete: (id) => api.delete(`/projects/${id}`),
  // Tasks
  createTask: (projectId, data) => api.post(`/projects/${projectId}/tasks`, data),
  updateTask: (projectId, taskId, data) => api.patch(`/projects/${projectId}/tasks/${taskId}`, data),
  deleteTask: (projectId, taskId) => api.delete(`/projects/${projectId}/tasks/${taskId}`),
  // Comments
  addComment: (projectId, content) => api.post(`/projects/${projectId}/comments`, { content }),
  deleteComment: (projectId, commentId) => api.delete(`/projects/${projectId}/comments/${commentId}`),
  // Expenses
  addExpense: (projectId, data) => api.post(`/projects/${projectId}/expenses`, data),
  deleteExpense: (projectId, expenseId) => api.delete(`/projects/${projectId}/expenses/${expenseId}`),
  // Milestones
  addMilestone: (projectId, data) => api.post(`/projects/${projectId}/milestones`, data),
  updateMilestone: (projectId, milestoneId, data) => api.patch(`/projects/${projectId}/milestones/${milestoneId}`, data),
  deleteMilestone: (projectId, milestoneId) => api.delete(`/projects/${projectId}/milestones/${milestoneId}`),
  // Meta
  getMembers: () => api.get('/projects/meta/members'),
};


// Personal Report API
export const reportAPI = {
  getPersonal: () => api.get('/report/personal'),
};
