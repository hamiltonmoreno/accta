import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { Toaster } from './components/ui/sonner';
import { PublicLayout } from './layouts/PublicLayout';
import { PrivateLayout } from './layouts/PrivateLayout';
import { HomePage } from './pages/public/HomePage';
import { ProfissaoPage } from './pages/public/ProfissaoPage';
import { NoticiasPage } from './pages/public/NoticiasPage';
import { ValidadorPage } from './pages/public/ValidadorPage';
import { LoginPage } from './pages/public/LoginPage';
import { TransparenciaPage } from './pages/public/TransparenciaPage';
import { NotificacoesPage } from './pages/private/NotificacoesPage';
import { DashboardPage } from './pages/private/DashboardPage';
import { CarteiraPage } from './pages/private/CarteiraPage';
import { FinanceiroPage } from './pages/private/FinanceiroPage';
import { VotacoesPage } from './pages/private/VotacoesPage';
import { DocumentosPage } from './pages/private/DocumentosPage';
import { MuralPage } from './pages/private/MuralPage';
import { BeneficiosPage } from './pages/private/BeneficiosPage';
import { AdminUsuariosPage } from './pages/private/AdminUsuariosPage';
import { AdminLogsPage } from './pages/private/AdminLogsPage';
import './App.css';

const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<PublicLayout><HomePage /></PublicLayout>} />
      <Route path="/profissao" element={<PublicLayout><ProfissaoPage /></PublicLayout>} />
      <Route path="/noticias" element={<PublicLayout><NoticiasPage /></PublicLayout>} />
      <Route path="/transparencia" element={<PublicLayout><TransparenciaPage /></PublicLayout>} />
      <Route path="/validador" element={<PublicLayout><ValidadorPage /></PublicLayout>} />
      <Route path="/login" element={<LoginPage />} />

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
          <ProtectedRoute>
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

      {/* Admin Routes */}
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

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <BrowserRouter>
          <div className="App">
            <AppRoutes />
            <Toaster position="top-right" richColors />
          </div>
        </BrowserRouter>
      </NotificationProvider>
    </AuthProvider>
  );
}

export default App;
