import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { Toaster } from './components/ui/sonner';
import { ErrorBoundary } from './components/ErrorBoundary';
import { PublicLayout } from './layouts/PublicLayout';
import { PrivateLayout } from './layouts/PrivateLayout';
import { queryClient } from './lib/queryClient';
// Public pages — kept eager: small, fast TTI matters for landing pages.
import { HomePage } from './pages/public/HomePage';
import { LoginPage } from './pages/public/LoginPage';
import './App.css';

// Public pages that aren't needed on first paint — lazy.
const SobrePage = lazy(() => import('./pages/public/SobrePage').then((m) => ({ default: m.SobrePage })));
const ProfissaoPage = lazy(() => import('./pages/public/ProfissaoPage').then((m) => ({ default: m.ProfissaoPage })));
const NoticiasPage = lazy(() => import('./pages/public/NoticiasPage').then((m) => ({ default: m.NoticiasPage })));
const ValidadorPage = lazy(() => import('./pages/public/ValidadorPage').then((m) => ({ default: m.ValidadorPage })));
const ForgotPasswordPage = lazy(() => import('./pages/public/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage })));
const SetupAccountPage = lazy(() => import('./pages/public/SetupAccountPage').then((m) => ({ default: m.SetupAccountPage })));
const ResetPasswordPage = lazy(() => import('./pages/public/ResetPasswordPage').then((m) => ({ default: m.ResetPasswordPage })));
const TransparenciaPage = lazy(() => import('./pages/public/TransparenciaPage').then((m) => ({ default: m.TransparenciaPage })));
const BeneficiosPublicoPage = lazy(() => import('./pages/public/BeneficiosPublicoPage').then((m) => ({ default: m.BeneficiosPublicoPage })));
const ContactosPage = lazy(() => import('./pages/public/ContactosPage').then((m) => ({ default: m.ContactosPage })));
const EventosPublicoPage = lazy(() => import('./pages/public/EventosPublicoPage').then((m) => ({ default: m.EventosPublicoPage })));
const GaleriaPage = lazy(() => import('./pages/public/GaleriaPage').then((m) => ({ default: m.GaleriaPage })));
const CriarContaPage = lazy(() => import('./pages/public/CriarContaPage').then((m) => ({ default: m.CriarContaPage })));

// Private pages — lazy. They're only loaded after a user logs in, so we
// don't want their bundle weight on the public landing page.
const NotificacoesPage = lazy(() => import('./pages/private/NotificacoesPage').then((m) => ({ default: m.NotificacoesPage })));
const DashboardPage = lazy(() => import('./pages/private/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const CarteiraPage = lazy(() => import('./pages/private/CarteiraPage').then((m) => ({ default: m.CarteiraPage })));
const FinanceiroPage = lazy(() => import('./pages/private/FinanceiroPage').then((m) => ({ default: m.FinanceiroPage })));
const ProjectsPage = lazy(() => import('./pages/private/ProjectsPage'));
const ProjectDetailPage = lazy(() => import('./pages/private/ProjectDetailPage'));
const VotacoesPage = lazy(() => import('./pages/private/VotacoesPage').then((m) => ({ default: m.VotacoesPage })));
const DocumentosPage = lazy(() => import('./pages/private/DocumentosPage').then((m) => ({ default: m.DocumentosPage })));
const MuralPage = lazy(() => import('./pages/private/MuralPage').then((m) => ({ default: m.MuralPage })));
const BeneficiosPage = lazy(() => import('./pages/private/BeneficiosPage').then((m) => ({ default: m.BeneficiosPage })));
const EventosPage = lazy(() => import('./pages/private/EventosPage').then((m) => ({ default: m.EventosPage })));
const GaleriaAdminPage = lazy(() => import('./pages/private/GaleriaAdminPage').then((m) => ({ default: m.GaleriaAdminPage })));
const AdminUsuariosPage = lazy(() => import('./pages/private/AdminUsuariosPage').then((m) => ({ default: m.AdminUsuariosPage })));
const PerfilPage = lazy(() => import('./pages/private/PerfilPage').then((m) => ({ default: m.PerfilPage })));
const AdminLogsPage = lazy(() => import('./pages/private/AdminLogsPage').then((m) => ({ default: m.AdminLogsPage })));
const AdminPedidosInscricaoPage = lazy(() => import('./pages/private/AdminPedidosInscricaoPage').then((m) => ({ default: m.AdminPedidosInscricaoPage })));

const RouteSpinner = () => (
  <div className="min-h-[60vh] flex items-center justify-center" role="status" aria-live="polite">
    <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
    <span className="sr-only">A carregar página...</span>
  </div>
);

const ProtectedRoute = ({ children, requireAdmin = false, allowedRoles = [], allowedPrivileges = [] }) => {
  const { isAuthenticated, isAdmin, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" role="status" aria-live="polite">
        <div className="inline-block w-8 h-8 border-4 border-carmesim border-t-transparent rounded-full animate-spin" />
        <span className="sr-only">A verificar sessão...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  if (allowedRoles.length > 0) {
    // RBAC aditivo: passa por role OU por privilégio granular (ex.: Conselho
    // Fiscal com view_finances_readonly acede ao /financeiro em modo leitura).
    const roleOk = allowedRoles.includes(user?.role);
    const privOk = allowedPrivileges.some((p) => (user?.privileges || []).includes(p));
    if (!roleOk && !privOk) {
      return <Navigate to="/dashboard" replace />;
    }
  }

  return children;
};

function AppRoutes() {
  return (
    <Suspense fallback={<RouteSpinner />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<PublicLayout><HomePage /></PublicLayout>} />
        <Route path="/sobre" element={<PublicLayout><SobrePage /></PublicLayout>} />
        <Route path="/profissao" element={<PublicLayout><ProfissaoPage /></PublicLayout>} />
        <Route path="/noticias" element={<PublicLayout><NoticiasPage /></PublicLayout>} />
        <Route path="/transparencia" element={<PublicLayout><TransparenciaPage /></PublicLayout>} />
        <Route path="/beneficios-publico" element={<PublicLayout><BeneficiosPublicoPage /></PublicLayout>} />
        <Route path="/contactos" element={<PublicLayout><ContactosPage /></PublicLayout>} />
        <Route path="/eventos-publico" element={<PublicLayout><EventosPublicoPage /></PublicLayout>} />
        <Route path="/galeria" element={<PublicLayout><GaleriaPage /></PublicLayout>} />
        <Route path="/validador" element={<PublicLayout><ValidadorPage /></PublicLayout>} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/setup-account" element={<SetupAccountPage />} />
        <Route path="/criar-conta" element={<PublicLayout><CriarContaPage /></PublicLayout>} />

        {/* Private Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <PrivateLayout><DashboardPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/carteira"
          element={
            <ProtectedRoute>
              <PrivateLayout><CarteiraPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/financeiro"
          element={
            <ProtectedRoute allowedRoles={['admin', 'financeiro']} allowedPrivileges={['view_finances_readonly', 'manage_finances']}>
              <PrivateLayout><FinanceiroPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/votacoes"
          element={
            <ProtectedRoute>
              <PrivateLayout><VotacoesPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/documentos"
          element={
            <ProtectedRoute>
              <PrivateLayout><DocumentosPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projetos"
          element={
            <ProtectedRoute>
              <PrivateLayout><ProjectsPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/projetos/:id"
          element={
            <ProtectedRoute>
              <PrivateLayout><ProjectDetailPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/mural"
          element={
            <ProtectedRoute>
              <PrivateLayout><MuralPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/beneficios"
          element={
            <ProtectedRoute>
              <PrivateLayout><BeneficiosPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/notificacoes"
          element={
            <ProtectedRoute>
              <PrivateLayout><NotificacoesPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/eventos"
          element={
            <ProtectedRoute>
              <PrivateLayout><EventosPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/galeria-admin"
          element={
            <ProtectedRoute>
              <PrivateLayout><GaleriaAdminPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />

        {/* Admin Routes */}
        <Route
          path="/perfil"
          element={
            <ProtectedRoute>
              <PrivateLayout><PerfilPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/usuarios"
          element={
            <ProtectedRoute requireAdmin>
              <PrivateLayout><AdminUsuariosPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/logs"
          element={
            <ProtectedRoute requireAdmin>
              <PrivateLayout><AdminLogsPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/pedidos-inscricao"
          element={
            <ProtectedRoute requireAdmin>
              <PrivateLayout><AdminPedidosInscricaoPage /></PrivateLayout>
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

function App() {
  // QueryClientProvider envolve tudo: AuthContext.useEffect (validateSession)
  // pode usar useQuery no futuro; NotificationContext idem.
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <NotificationProvider>
            <BrowserRouter>
              <div className="App">
                <AppRoutes />
                <Toaster position="top-right" richColors />
                <Analytics />
                <SpeedInsights />
              </div>
            </BrowserRouter>
          </NotificationProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
