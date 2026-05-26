import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { LogIn, Shield, Plane, ArrowLeft, Lock, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { BrandLogo } from '../../components/BrandLogo';
import { unsplashSrcSet } from '../../utils/unsplash';
import { loginSchema } from '../../utils/authSchemas';

// Helper: parse Retry-After header (segundos) e devolve estado de lock.
// Backend devolve 423 + Retry-After quando 5+ falhas dentro de 15min (Sprint 4).
const parseLockedUntil = (error) => {
  if (error.response?.status !== 423) return null;
  const retry = parseInt(error.response.headers['retry-after'], 10);
  const seconds = Number.isFinite(retry) && retry > 0 ? retry : 900; // 15min fallback
  return Date.now() + seconds * 1000;
};

const formatRemaining = (ms) => {
  const total = Math.max(0, Math.ceil(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
};

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [lockedUntil, setLockedUntil] = useState(null); // ms epoch
  const [now, setNow] = useState(Date.now());
  // MFA (spec-mfa-frontend-pr2 §6): 2.º fator inline. A password fica no estado do
  // form (react-hook-form) e não viaja entre rotas. `otp` aceita TOTP (6 dígitos)
  // OU um código de recuperação (formato xxxx-xxxx-…), por isso é texto livre.
  const [mfaStep, setMfaStep] = useState(false);
  const [otp, setOtp] = useState('');
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(loginSchema), mode: 'onBlur' });

  // Tick 1s para countdown do lock. Para de correr quando lockedUntil=null.
  useEffect(() => {
    if (!lockedUntil) return;
    const id = setInterval(() => {
      const t = Date.now();
      setNow(t);
      if (t >= lockedUntil) {
        setLockedUntil(null);
        clearInterval(id);
      }
    }, 1000);
    return () => clearInterval(id);
  }, [lockedUntil]);

  const isLocked = lockedUntil !== null && now < lockedUntil;
  const remainingMs = lockedUntil ? lockedUntil - now : 0;

  const onSubmit = async (data) => {
    try {
      const user = await login({ ...data, otp: otp.trim() || undefined });
      toast.success(`Bem-vindo, ${user.name}!`);
      // admin/financeiro sem MFA → enrolment bloqueante; restantes → dashboard.
      const needsSetup = ['admin', 'financeiro'].includes(user.role) && !user.mfa_enabled;
      navigate(needsSetup ? '/mfa-setup' : '/dashboard');
    } catch (error) {
      const lockedUntilTs = parseLockedUntil(error);
      if (lockedUntilTs) {
        setLockedUntil(lockedUntilTs);
        toast.error('Conta temporariamente bloqueada por excesso de tentativas');
        return;
      }
      const detail = error.response?.data?.detail;
      if (error.response?.status === 401 && detail === 'mfa_required') {
        // Password OK, falta o 2.º fator — revela o campo OTP (sem nova rota).
        setMfaStep(true);
        return;
      }
      if (error.response?.status === 401 && detail === 'mfa_invalido') {
        toast.error('Código de verificação inválido');
        setOtp('');
        return;
      }
      toast.error(detail || 'Erro ao fazer login');
    }
  };

  const backToCredentials = () => {
    setMfaStep(false);
    setOtp('');
  };

  return (
    <div className="min-h-screen flex">
      {/* Left: Visual Panel (hidden on mobile) */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-grafite overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=1280&auto=format&fit=crop"
          srcSet={unsplashSrcSet('https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&auto=format&fit=crop')}
          sizes="100vw"
          alt=""
          aria-hidden="true"
          loading="lazy"
          decoding="async"
          className="absolute inset-0 w-full h-full object-cover opacity-30"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-grafite via-grafite/80 to-grafite/40" />

        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <Link to="/" className="inline-flex">
            <BrandLogo dark />
          </Link>

          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-carmesim/20 border border-carmesim/40 rounded-xl flex items-center justify-center">
                <Shield className="w-6 h-6 text-carmesim" />
              </div>
              <div className="w-12 h-12 bg-white/10 border border-white/20 rounded-xl flex items-center justify-center">
                <Plane className="w-6 h-6 text-white/80" />
              </div>
            </div>
            <h2 className="font-bold text-4xl text-white mb-4 leading-tight">
              Portal do<br />
              <span className="text-white">Associado</span>
            </h2>
            <p className="text-white/60 text-lg max-w-sm leading-relaxed">
              Aceda à sua carteira digital, votações, documentos e muito mais.
            </p>
          </div>

          <p className="text-white/30 text-xs">
            &copy; {new Date().getFullYear()} ACCTA - Cabo Verde
          </p>
        </div>
      </div>

      {/* Right: Login Form */}
      <div className="flex-1 flex items-center justify-center px-5 py-8 bg-gray-50">
        <div className="w-full max-w-sm animate-fade-up">
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <Link to="/" className="inline-flex justify-center mb-5">
              <BrandLogo />
            </Link>
          </div>

          {/* Back Link */}
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-sm text-[#6B7280] hover:text-grafite transition-colors mb-6"
            data-testid="back-to-home"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar ao inicio
          </Link>

          <div className="mb-6">
            <h1 className="font-bold text-2xl text-grafite mb-1" data-testid="login-title">Entrar na conta</h1>
            <p className="text-sm text-gray-500">Acesse o portal com as suas credenciais</p>
          </div>

          {/* Lockout banner — visivel quando backend devolve 423 (5 falhas em 15min).
              Form fica desactivado ate o countdown chegar a zero. */}
          {isLocked && (
            <div
              role="alert"
              className="mb-4 flex items-start gap-3 p-4 rounded-lg bg-carmesim/5 border border-carmesim/20"
              data-testid="login-locked-banner"
            >
              <Lock className="w-5 h-5 text-carmesim shrink-0 mt-0.5" aria-hidden="true" />
              <div className="text-sm">
                <p className="font-semibold text-grafite mb-0.5">Conta temporariamente bloqueada</p>
                <p className="text-gray-500">
                  Demasiadas tentativas falhadas. Tente novamente em{' '}
                  <strong className="text-carmesim font-mono" data-testid="login-locked-countdown">
                    {formatRemaining(remainingMs)}
                  </strong>.
                </p>
              </div>
            </div>
          )}

          {/* Form */}
          <div className="card-technical p-6 sm:p-7">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
              <div>
                <label htmlFor="email" className="block text-xs uppercase tracking-widest text-[#6B7280] mb-2 font-semibold">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  inputMode="email"
                  autoComplete="email"
                  readOnly={mfaStep}
                  aria-invalid={errors.email ? 'true' : 'false'}
                  {...register('email')}
                  className={`w-full px-4 py-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 transition-all aria-[invalid=true]:border-carmesim/60 ${mfaStep ? 'bg-gray-50 text-gray-500' : ''}`}
                  placeholder="seu@email.cv"
                  data-testid="login-email"
                />
                {errors.email && (
                  <p className="mt-1 text-xs text-[#B91C1C]" role="alert">{errors.email.message}</p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label htmlFor="password" className="block text-xs uppercase tracking-widest text-[#6B7280] font-semibold">
                    Senha
                  </label>
                  <Link
                    to="/forgot-password"
                    className="text-xs text-carmesim hover:text-carmesim-dark transition-colors font-medium"
                    data-testid="forgot-password-link"
                  >
                    Esqueceu a senha?
                  </Link>
                </div>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  readOnly={mfaStep}
                  aria-invalid={errors.password ? 'true' : 'false'}
                  {...register('password')}
                  className={`w-full px-4 py-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 transition-all aria-[invalid=true]:border-carmesim/60 ${mfaStep ? 'bg-gray-50 text-gray-500' : ''}`}
                  placeholder="********"
                  data-testid="login-password"
                />
                {errors.password && (
                  <p className="mt-1 text-xs text-[#B91C1C]" role="alert">{errors.password.message}</p>
                )}
              </div>

              {/* 2.º fator — revelado quando o backend devolve 401 mfa_required */}
              {mfaStep && (
                <div data-testid="login-mfa-step">
                  <label htmlFor="otp" className="block text-xs uppercase tracking-widest text-[#6B7280] mb-2 font-semibold">
                    Código de verificação
                  </label>
                  {/* Texto livre (inputMode text): aceita TOTP de 6 dígitos OU um
                      código de recuperação alfanumérico (xxxx-xxxx-…); 'numeric'
                      esconderia as letras a-f no teclado móvel. */}
                  <input
                    id="otp"
                    type="text"
                    inputMode="text"
                    autoComplete="one-time-code"
                    autoCapitalize="none"
                    autoCorrect="off"
                    spellCheck={false}
                    autoFocus
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm font-mono tracking-widest focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 transition-all"
                    placeholder="000000 ou código de recuperação"
                    data-testid="login-otp"
                  />
                  <p className="mt-2 text-xs text-[#6B7280]">
                    Introduza o código da sua app de autenticação (ou um código de recuperação).
                  </p>
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting || isLocked || (mfaStep && otp.trim().length < 6)}
                className="w-full bg-carmesim text-white hover:bg-carmesim-dark h-11 rounded-lg font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                data-testid="login-submit"
              >
                {isSubmitting ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : isLocked ? (
                  <>
                    <Lock className="w-4 h-4" />
                    Bloqueado · {formatRemaining(remainingMs)}
                  </>
                ) : mfaStep ? (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    Verificar
                  </>
                ) : (
                  <>
                    <LogIn className="w-4 h-4" />
                    Entrar
                  </>
                )}
              </button>

              {mfaStep && (
                <button
                  type="button"
                  onClick={backToCredentials}
                  className="w-full inline-flex items-center justify-center gap-1.5 text-sm text-[#6B7280] hover:text-grafite transition-colors"
                  data-testid="login-mfa-back"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Voltar
                </button>
              )}

              <p className="text-center text-sm text-[#6B7280] mt-4">
                Ainda não é sócio?{' '}
                <Link
                  to="/criar-conta"
                  className="text-carmesim hover:text-carmesim-dark font-medium transition-colors"
                  data-testid="criar-conta-link"
                >
                  Criar conta
                </Link>
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
