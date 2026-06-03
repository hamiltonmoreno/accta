import React, { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Lock, ArrowLeft, CheckCircle, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';
import { BrandLogo } from '../../components/BrandLogo';
import api from '../../utils/api';
import { resetPasswordSchema } from '../../utils/authSchemas';

export const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [showPassword, setShowPassword] = useState(false);
  const [success, setSuccess] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(resetPasswordSchema), mode: 'onBlur' });

  const onSubmit = async ({ password }) => {
    try {
      await api.post('/auth/reset-password', { token, new_password: password });
      setSuccess(true);
      toast.success('Senha alterada com sucesso!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao redefinir senha');
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-5">
        <div className="text-center">
          <h1 className="font-bold text-2xl text-grafite mb-3">Token em falta</h1>
          <p className="text-gray-500 mb-6">O link de recuperação é inválido ou não contém um token.</p>
          <Link
            to="/forgot-password"
            className="inline-flex items-center gap-2 bg-floresta text-white px-6 py-3 rounded-lg font-bold text-sm hover:bg-floresta-dark transition-colors"
          >
            Solicitar novo link
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-5 py-8">
      <div className="w-full max-w-md animate-fade-up">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex justify-center mb-5">
            <BrandLogo />
          </Link>
        </div>

        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-sm text-[#6B7280] hover:text-grafite transition-colors mb-6"
          data-testid="back-to-login-reset"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar ao login
        </Link>

        {!success ? (
          <>
            <div className="mb-6">
              <h1 className="font-bold text-2xl text-grafite mb-1" data-testid="reset-title">
                Nova senha
              </h1>
              <p className="text-sm text-gray-500">
                Defina a sua nova senha de acesso ao portal.
              </p>
            </div>

            <div className="card-technical p-6 sm:p-7">
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
                <div>
                  <label htmlFor="password" className="block text-xs uppercase tracking-widest text-[#6B7280] mb-2 font-semibold">
                    Nova senha
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="new-password"
                      aria-invalid={errors.password ? 'true' : 'false'}
                      {...register('password')}
                      className="w-full px-4 py-3 pr-11 border border-gray-200 rounded-lg text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 transition-all aria-[invalid=true]:border-carmesim/60"
                      placeholder="Mínimo 6 caracteres"
                      data-testid="reset-password-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-grafite"
                      data-testid="toggle-password-visibility"
                      aria-label={showPassword ? 'Esconder senha' : 'Mostrar senha'}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="mt-1 text-xs text-[#B91C1C]" role="alert">{errors.password.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-xs uppercase tracking-widest text-[#6B7280] mb-2 font-semibold">
                    Confirmar senha
                  </label>
                  <input
                    id="confirmPassword"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    aria-invalid={errors.confirmPassword ? 'true' : 'false'}
                    {...register('confirmPassword')}
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 transition-all aria-[invalid=true]:border-carmesim/60"
                    placeholder="Repita a senha"
                    data-testid="reset-confirm-password-input"
                  />
                  {errors.confirmPassword && (
                    <p className="mt-1 text-xs text-[#B91C1C]" role="alert" data-testid="password-mismatch-error">{errors.confirmPassword.message}</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full bg-floresta text-white hover:bg-floresta-dark h-11 rounded-lg font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  data-testid="reset-submit"
                >
                  {isSubmitting ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <Lock className="w-4 h-4" />
                      Redefinir senha
                    </>
                  )}
                </button>
              </form>
            </div>
          </>
        ) : (
          <div className="card-technical p-6 sm:p-7 text-center">
            <div className="w-16 h-16 bg-[#F0FDF4] rounded-xl flex items-center justify-center mx-auto mb-5">
              <CheckCircle className="w-8 h-8 text-[#15803D]" />
            </div>
            <h2 className="font-bold text-xl text-grafite mb-2" data-testid="reset-success-title">
              Senha alterada!
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              A sua senha foi redefinida com sucesso. Já pode fazer login com a nova senha.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-floresta text-white hover:bg-floresta-dark h-11 rounded-lg font-semibold text-sm transition-colors flex items-center justify-center gap-2"
              data-testid="go-to-login-after-reset"
            >
              Ir para o login
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
