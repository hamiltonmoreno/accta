import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Mail, ArrowLeft, Copy, ExternalLink, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { ACCTALogoHorizontal } from '../../components/ACCTALogo';
import api from '../../utils/api';
import { forgotPasswordSchema } from '../../utils/authSchemas';

export const ForgotPasswordPage = () => {
  // Captura o email submetido para mostrar na branch de sucesso (mesmo
  // depois do form ser limpo). resetToken so vem populado em dev (legacy
  // demo flow); em prod a resposta e generica e mostra-se mensagem neutra.
  const [submitted, setSubmitted] = useState(null); // {email, token}
  const [copied, setCopied] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(forgotPasswordSchema), mode: 'onBlur' });

  const onSubmit = async ({ email }) => {
    try {
      const res = await api.post('/auth/forgot-password', { email });
      setSubmitted({ email, token: res.data.demo_token || null });
      toast.success('Pedido enviado!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao processar pedido');
    }
  };

  const resetLink = submitted?.token
    ? `${window.location.origin}/reset-password?token=${submitted.token}`
    : '';

  const handleCopy = () => {
    navigator.clipboard.writeText(resetLink);
    setCopied(true);
    toast.success('Link copiado!');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-5 py-8">
      <div className="w-full max-w-md animate-fade-up">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex justify-center mb-5">
            <ACCTALogoHorizontal />
          </Link>
        </div>

        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-sm text-[#6B7280] hover:text-grafite transition-colors mb-6"
          data-testid="back-to-login"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar ao login
        </Link>

        {!submitted ? (
          <>
            <div className="mb-6">
              <h1 className="font-bold text-2xl text-grafite mb-1" data-testid="forgot-title">
                Recuperar senha
              </h1>
              <p className="text-sm text-gray-500">
                Introduza o email associado à sua conta para receber instruções de recuperação.
              </p>
            </div>

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
                    aria-invalid={errors.email ? 'true' : 'false'}
                    {...register('email')}
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 transition-all aria-[invalid=true]:border-carmesim/60"
                    placeholder="seu@email.cv"
                    data-testid="forgot-email-input"
                  />
                  {errors.email && (
                    <p className="mt-1 text-xs text-[#B91C1C]" role="alert">{errors.email.message}</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full bg-carmesim text-white hover:bg-carmesim-dark h-11 rounded-lg font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  data-testid="forgot-submit"
                >
                  {isSubmitting ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <Mail className="w-4 h-4" />
                      Enviar
                    </>
                  )}
                </button>
              </form>
            </div>
          </>
        ) : (
          <>
            <div className="mb-6">
              <div className="w-14 h-14 bg-[#F0FDF4] rounded-xl flex items-center justify-center mb-4">
                <CheckCircle className="w-7 h-7 text-[#15803D]" />
              </div>
              <h1 className="font-bold text-2xl text-grafite mb-1" data-testid="forgot-success-title">
                Pedido recebido
              </h1>
              <p className="text-sm text-gray-500">
                Se a conta <strong className="text-grafite">{submitted.email}</strong> existir, um email com instruções de recuperação será enviado em breve.
              </p>
            </div>

            {submitted.token && (
              <div className="card-technical p-5">
                <label className="block text-xs uppercase tracking-widest text-[#6B7280] mb-2 font-semibold">
                  Link de recuperação (modo demo)
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={resetLink}
                    className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-600 font-mono truncate"
                    data-testid="reset-link-display"
                  />
                  <button
                    onClick={handleCopy}
                    className="px-3 py-2 bg-grafite text-white rounded-lg hover:bg-grafite/90 transition-colors flex items-center gap-1.5 text-xs font-semibold shrink-0"
                    data-testid="copy-link-btn"
                  >
                    {copied ? <CheckCircle className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? 'Copiado' : 'Copiar'}
                  </button>
                </div>

                <Link
                  to={`/reset-password?token=${submitted.token}`}
                  className="mt-4 w-full bg-carmesim text-white hover:bg-carmesim-dark h-11 rounded-lg font-semibold text-sm transition-colors flex items-center justify-center gap-2"
                  data-testid="go-to-reset-btn"
                >
                  <ExternalLink className="w-4 h-4" />
                  Redefinir senha agora
                </Link>
              </div>
            )}

            <button
              onClick={() => setSubmitted(null)}
              className="mt-4 text-sm text-[#6B7280] hover:text-grafite transition-colors"
              data-testid="try-another-email"
            >
              Tentar com outro email
            </button>
          </>
        )}
      </div>
    </div>
  );
};
