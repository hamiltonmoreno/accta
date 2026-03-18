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
  getAll: () => api.get('/users'),
  updateStatus: (userId, status) => api.patch(`/users/${userId}/status`, null, { params: { status } }),
};

// Invoices API
export const invoicesAPI = {
  getAll: () => api.get('/invoices'),
  create: (data) => api.post('/invoices', data),
  confirm: (invoiceId) => api.patch(`/invoices/${invoiceId}/confirm`),
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
  getPosts: () => api.get('/wall'),
  create: (data) => api.post('/wall', data),
  approve: (postId) => api.patch(`/wall/${postId}/approve`),
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

// Notifications API
export const notificationsAPI = {
  getAll: () => api.get('/notifications'),
  getUnreadCount: () => api.get('/notifications/unread/count'),
  markRead: (notificationId) => api.patch(`/notifications/${notificationId}/read`),
  markAllRead: () => api.patch('/notifications/mark-all-read'),
  create: (data) => api.post('/notifications', data),
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
