import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, ArrowLeft, Copy, ExternalLink, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { ACCTALogoHorizontal } from '../../components/ACCTALogo';
import api from '../../utils/api';

export const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [resetToken, setResetToken] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await api.post('/auth/forgot-password', { email });
      setResetToken(res.data.demo_token);
      toast.success('Token de recuperação gerado!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao processar pedido');
    } finally {
      setLoading(false);
    }
  };

  const resetLink = resetToken ? `${window.location.origin}/reset-password?token=${resetToken}` : '';

  const handleCopy = () => {
    navigator.clipboard.writeText(resetLink);
    setCopied(true);
    toast.success('Link copiado!');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-5 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex justify-center mb-5">
            <ACCTALogoHorizontal />
          </Link>
        </div>

        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-grafite transition-colors mb-6"
          data-testid="back-to-login"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar ao login
        </Link>

        {!resetToken ? (
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
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label htmlFor="email" className="block text-xs uppercase tracking-widest text-gray-400 mb-2 font-semibold">
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 transition-all"
                    placeholder="seu@email.cv"
                    data-testid="forgot-email-input"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-carmesim text-white hover:bg-carmesim-dark h-11 rounded-lg uppercase tracking-wider font-bold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  data-testid="forgot-submit"
                >
                  {loading ? (
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
              <div className="w-14 h-14 bg-green-100 rounded-xl flex items-center justify-center mb-4">
                <CheckCircle className="w-7 h-7 text-green-600" />
              </div>
              <h1 className="font-bold text-2xl text-grafite mb-1" data-testid="forgot-success-title">
                Token gerado!
              </h1>
              <p className="text-sm text-gray-500">
                Em produção, um email seria enviado para <strong className="text-grafite">{email}</strong>. Para demonstração, use o link abaixo:
              </p>
            </div>

            <div className="card-technical p-5">
              <label className="block text-xs uppercase tracking-widest text-gray-400 mb-2 font-semibold">
                Link de recuperação
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
                to={`/reset-password?token=${resetToken}`}
                className="mt-4 w-full bg-carmesim text-white hover:bg-carmesim-dark h-11 rounded-lg uppercase tracking-wider font-bold text-sm transition-colors flex items-center justify-center gap-2"
                data-testid="go-to-reset-btn"
              >
                <ExternalLink className="w-4 h-4" />
                Redefinir senha agora
              </Link>
            </div>

            <button
              onClick={() => { setResetToken(null); setEmail(''); }}
              className="mt-4 text-sm text-gray-400 hover:text-grafite transition-colors"
              data-testid="try-another-email"
            >
              Tentar com outro email
            </button>
          </>
        )}
      </motion.div>
    </div>
  );
};
