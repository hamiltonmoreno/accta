import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { BrandLogo } from '../components/BrandLogo';
import { SetupMFA } from '../components/SetupMFA';

// Enrolment obrigatório de MFA (spec-mfa-frontend-pr2 §8). Página bloqueante para
// admin/financeiro sem MFA: o backend recusa (403 mfa_setup_required) tudo fora do
// enrolment, e a guarda no ProtectedRoute redireciona para cá. Sem sidebar e sem
// links para outras rotas — a única saída sem configurar é o logout.
export const MfaSetupPage = () => {
  const navigate = useNavigate();
  const { logout, refreshUser } = useAuth();

  const handleComplete = async () => {
    // Após verify, o backend faz upgrade do cookie de sessão (sem mfa_pending).
    // refreshUser() traz mfa_enabled=true → a guarda deixa passar para o dashboard.
    await refreshUser();
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-5 py-10 bg-gray-50">
      <div className="w-full max-w-md animate-fade-up">
        <div className="flex justify-center mb-8">
          <BrandLogo />
        </div>

        <div className="card-technical p-6 sm:p-7">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-11 h-11 bg-carmesim/10 border border-carmesim/20 rounded-xl flex items-center justify-center shrink-0">
              <ShieldCheck className="w-5 h-5 text-carmesim" aria-hidden="true" />
            </div>
            <div>
              <h1 className="font-bold text-xl text-grafite leading-tight">
                Configure a autenticação de dois fatores
              </h1>
              <p className="text-sm text-[#6B7280] mt-0.5">
                Obrigatório para o seu cargo antes de continuar.
              </p>
            </div>
          </div>

          <SetupMFA onComplete={handleComplete} />
        </div>

        <div className="text-center mt-6">
          <button
            type="button"
            onClick={() => { logout(); navigate('/login'); }}
            className="inline-flex items-center gap-1.5 text-sm text-[#6B7280] hover:text-grafite transition-colors"
            data-testid="mfa-setup-logout"
          >
            <LogOut className="w-4 h-4" />
            Sair
          </button>
        </div>
      </div>
    </div>
  );
};

export default MfaSetupPage;
