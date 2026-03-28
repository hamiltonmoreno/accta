import React, { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Lock, ArrowLeft, CheckCircle, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';
import { ACCTALogoHorizontal } from '../../components/ACCTALogo';
import api from '../../utils/api';

export const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (password.length < 6) {
      toast.error('A senha deve ter pelo menos 6 caracteres');
      return;
    }
    if (password !== confirmPassword) {
      toast.error('As senhas não coincidem');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/reset-password', { token, new_password: password });
      setSuccess(true);
      toast.success('Senha alterada com sucesso!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao redefinir senha');
    } finally {
      setLoading(false);
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
            className="inline-flex items-center gap-2 bg-carmesim text-white px-6 py-3 rounded-lg font-bold text-sm hover:bg-carmesim-dark transition-colors"
          >
            Solicitar novo link
          </Link>
        </div>
      </div>
    );
  }

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
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label htmlFor="password" className="block text-xs uppercase tracking-widest text-gray-400 mb-2 font-semibold">
                    Nova senha
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      minLength={6}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-4 py-2.5 pr-11 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 transition-all"
                      placeholder="Mínimo 6 caracteres"
                      data-testid="reset-password-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-grafite"
                      data-testid="toggle-password-visibility"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-xs uppercase tracking-widest text-gray-400 mb-2 font-semibold">
                    Confirmar senha
                  </label>
                  <input
                    id="confirmPassword"
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={6}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 transition-all"
                    placeholder="Repita a senha"
                    data-testid="reset-confirm-password-input"
                  />
                </div>

                {password && confirmPassword && password !== confirmPassword && (
                  <p className="text-xs text-red-500" data-testid="password-mismatch-error">As senhas não coincidem</p>
                )}

                <button
                  type="submit"
                  disabled={loading || !password || !confirmPassword}
                  className="w-full bg-carmesim text-white hover:bg-carmesim-dark h-11 rounded-lg uppercase tracking-wider font-bold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  data-testid="reset-submit"
                >
                  {loading ? (
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
            <div className="w-16 h-16 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-5">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="font-bold text-xl text-grafite mb-2" data-testid="reset-success-title">
              Senha alterada!
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              A sua senha foi redefinida com sucesso. Já pode fazer login com a nova senha.
            </p>
            <button
              onClick={() => navigate('/login')}
              className="w-full bg-carmesim text-white hover:bg-carmesim-dark h-11 rounded-lg uppercase tracking-wider font-bold text-sm transition-colors flex items-center justify-center gap-2"
              data-testid="go-to-login-after-reset"
            >
              Ir para o login
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
};
