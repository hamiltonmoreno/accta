import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accta_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      // Don't redirect if already on login or public pages
      if (!currentPath.startsWith('/login') && !currentPath.startsWith('/validador') && !currentPath.startsWith('/profissao') && !currentPath.startsWith('/noticias') && !currentPath.startsWith('/transparencia') && currentPath !== '/') {
        localStorage.removeItem('accta_token');
        localStorage.removeItem('accta_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
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
  getAll: (visibility) => api.get('/posts', { params: { visibility } }),
  create: (data) => api.post('/posts', data),
};

// Documents API
export const documentsAPI = {
  getAll: () => api.get('/documents'),
  create: (data) => api.post('/documents', data),
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
  create: (data) => api.post('/benefits', data),
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
  getLogs: () => api.get('/audit-logs'),
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
  getAlbums: () => api.get('/gallery/albums'),
  getAlbum: (albumId) => api.get(`/gallery/albums/${albumId}`),
  createAlbum: (data) => api.post('/gallery/albums', data),
  updateAlbum: (albumId, data) => api.patch(`/gallery/albums/${albumId}`, data),
  deleteAlbum: (albumId) => api.delete(`/gallery/albums/${albumId}`),
  getPhotos: (albumId) => api.get('/gallery/photos', { params: { album_id: albumId } }),
  uploadPhoto: (albumId, file, caption) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('album_id', albumId);
    if (caption) formData.append('caption', caption);
    return api.post(`/gallery/photos/upload?album_id=${albumId}&caption=${encodeURIComponent(caption || '')}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
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

