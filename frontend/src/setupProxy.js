// Dev-only (carregado automaticamente pelo dev server CRA/craco).
// Proxy /api e /uploads → backend em :8001, na MESMA origem do frontend (:3000).
// Assim o cookie de sessão httpOnly (SameSite=Lax em dev) é first-party e é
// enviado nos pedidos — evita o problema de cookies cross-origin + CORS.
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  const target = 'http://localhost:8001';
  app.use('/api', createProxyMiddleware({ target, changeOrigin: true }));
  app.use('/uploads', createProxyMiddleware({ target, changeOrigin: true }));
};
