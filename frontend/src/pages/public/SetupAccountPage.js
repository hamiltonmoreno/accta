import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Shield, Lock, Eye, EyeOff, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { authAPI } from '../../utils/api';
import { toast } from 'sonner';
import { BrandLogo } from '../../components/BrandLogo';
import { setupAccountSchema } from '../../utils/authSchemas';
import { LanguageSwitcher } from '../../components/LanguageSwitcher';
import { useI18n } from '../../i18n';
import { usePageMeta } from '../../i18n/usePageMeta';
import { useValidationMessage } from '../../i18n/validation';

export const SetupAccountPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const { t, lp } = useI18n();
  const tv = useValidationMessage();
  usePageMeta('setupAccount');

  const [inviteData, setInviteData] = useState(null);
  const [validating, setValidating] = useState(true);
  const [invalid, setInvalid] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [success, setSuccess] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(setupAccountSchema), mode: 'onBlur' });

  useEffect(() => {
    if (!token) {
      setInvalid(true);
      setValidating(false);
      return;
    }
    authAPI.validateInvite(token)
      .then(res => setInviteData(res.data))
      .catch(() => setInvalid(true))
      .finally(() => setValidating(false));
  }, [token]);

  const onSubmit = async ({ password }) => {
    try {
      await authAPI.setupAccount({ token, password });
      setSuccess(true);
      toast.success(t('setupAccount.successToast'));
      // Sprint 10 — backend setou cookie httpOnly via Set-Cookie. JS nao
      // precisa de guardar nada. Hard reload para AuthContext re-bootstrap
      // via /auth/me e descobrir a sessao.
      setTimeout(() => { window.location.href = '/dashboard'; }, 1500);
    } catch (err) {
      toast.error(err.response?.data?.detail || t('setupAccount.errorGeneric'));
    }
  };

  if (validating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-8 h-8 text-carmesim animate-spin" />
      </div>
    );
  }

  if (invalid) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="fixed top-4 right-4 z-20">
          <LanguageSwitcher className="bg-white/90 border border-gray-200" />
        </div>
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 max-w-md w-full text-center animate-fade-up">
          <div className="w-14 h-14 bg-[#FEF2F2] rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7 text-carmesim" />
          </div>
          <h1 className="text-xl font-bold text-grafite mb-2">{t('setupAccount.invalidTitle')}</h1>
          <p className="text-sm text-gray-500 mb-6">
            {t('setupAccount.invalidBody')}
          </p>
          <button
            onClick={() => navigate(lp('/login'))}
            className="text-sm text-carmesim hover:underline font-medium"
            data-testid="back-to-login"
          >
            {t('setupAccount.backToLogin')}
          </button>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="fixed top-4 right-4 z-20">
          <LanguageSwitcher className="bg-white/90 border border-gray-200" />
        </div>
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 max-w-md w-full text-center animate-fade-up">
          <div className="w-14 h-14 bg-[#F0FDF4] rounded-2xl flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-7 h-7 text-[#16A34A]" />
          </div>
          <h1 className="text-xl font-bold text-grafite mb-2" data-testid="setup-success">{t('setupAccount.successTitle')}</h1>
          <p className="text-sm text-gray-500">
            {t('setupAccount.redirecting')}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="fixed top-4 right-4 z-20">
        <LanguageSwitcher className="bg-white/90 border border-gray-200" />
      </div>
      <div
        className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 max-w-md w-full animate-fade-up"
        data-testid="setup-account-form"
      >
        <div className="flex justify-center mb-6">
          <BrandLogo className="h-8" />
        </div>

        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-carmesim/10 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <Shield className="w-6 h-6 text-carmesim" />
          </div>
          <h1 className="text-xl font-bold text-grafite mb-1">{t('setupAccount.welcome')}</h1>
          <p className="text-sm text-gray-500">
            {t('setupAccount.intro', { name: inviteData?.name || '' })}
          </p>
          <p className="text-xs text-[#6B7280] mt-1">{inviteData?.email}</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div>
            <label htmlFor="setup-password" className="block text-xs font-medium text-gray-600 mb-1.5">{t('setupAccount.passwordLabel')}</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
              <input
                id="setup-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                aria-invalid={errors.password ? 'true' : 'false'}
                {...register('password')}
                placeholder={t('setupAccount.passwordPlaceholder')}
                className="w-full pl-9 pr-10 py-3 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none aria-[invalid=true]:border-carmesim/60"
                data-testid="setup-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label={showPassword ? t('setupAccount.hidePassword') : t('setupAccount.showPassword')}
              >
                {showPassword ? <EyeOff className="w-4 h-4" aria-hidden="true" /> : <Eye className="w-4 h-4" aria-hidden="true" />}
              </button>
            </div>
            {errors.password && (
              <p className="text-xs text-[#B91C1C] mt-1" role="alert">{tv(errors.password.message)}</p>
            )}
          </div>

          <div>
            <label htmlFor="setup-confirm-password" className="block text-xs font-medium text-gray-600 mb-1.5">{t('setupAccount.confirmLabel')}</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" aria-hidden="true" />
              <input
                id="setup-confirm-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                aria-invalid={errors.confirmPassword ? 'true' : 'false'}
                {...register('confirmPassword')}
                placeholder={t('setupAccount.confirmPlaceholder')}
                className="w-full pl-9 pr-3 py-3 border border-gray-200 rounded-lg text-sm focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2 focus:border-carmesim/40 outline-none aria-[invalid=true]:border-carmesim/60"
                data-testid="setup-confirm-password"
              />
            </div>
            {errors.confirmPassword && (
              <p className="text-xs text-[#B91C1C] mt-1" role="alert">{tv(errors.confirmPassword.message)}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 bg-floresta hover:bg-floresta-dark text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="setup-submit"
          >
            {isSubmitting ? t('setupAccount.activating') : t('setupAccount.submit')}
          </button>
        </form>
      </div>
    </div>
  );
};
