import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, Lock, Eye, EyeOff, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { authAPI } from '../../utils/api';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { ACCTALogoHorizontal } from '../../components/ACCTALogo';

export const SetupAccountPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login: authLogin } = useAuth();
  const token = searchParams.get('token');

  const [inviteData, setInviteData] = useState(null);
  const [validating, setValidating] = useState(true);
  const [invalid, setInvalid] = useState(false);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password.length < 6) {
      toast.error('A senha deve ter pelo menos 6 caracteres');
      return;
    }
    if (password !== confirmPassword) {
      toast.error('As senhas nao coincidem');
      return;
    }

    setSubmitting(true);
    try {
      const res = await authAPI.setupAccount({ token, password });
      setSuccess(true);
      toast.success('Conta ativada com sucesso!');

      // Auto-login
      localStorage.setItem('accta_token', res.data.access_token);
      localStorage.setItem('accta_user', JSON.stringify(res.data.user));
      setTimeout(() => navigate('/dashboard'), 1500);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao ativar conta');
    } finally {
      setSubmitting(false);
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
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 max-w-md w-full text-center"
        >
          <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7 text-carmesim" />
          </div>
          <h1 className="text-xl font-bold text-grafite mb-2">Convite Invalido</h1>
          <p className="text-sm text-gray-500 mb-6">
            Este link de convite e invalido ou ja foi utilizado. Contacte o administrador da ACCTA.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="text-sm text-carmesim hover:underline font-medium"
            data-testid="back-to-login"
          >
            Voltar ao Login
          </button>
        </motion.div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 max-w-md w-full text-center"
        >
          <div className="w-14 h-14 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-7 h-7 text-green-500" />
          </div>
          <h1 className="text-xl font-bold text-grafite mb-2" data-testid="setup-success">Conta Ativada!</h1>
          <p className="text-sm text-gray-500">
            A redirecionar para o painel...
          </p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8 max-w-md w-full"
        data-testid="setup-account-form"
      >
        <div className="flex justify-center mb-6">
          <ACCTALogoHorizontal className="h-8" />
        </div>

        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-carmesim/10 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <Shield className="w-6 h-6 text-carmesim" />
          </div>
          <h1 className="text-xl font-bold text-grafite mb-1">Bem-vindo a ACCTA</h1>
          <p className="text-sm text-gray-500">
            {inviteData?.name}, defina a sua senha para ativar a conta.
          </p>
          <p className="text-xs text-gray-400 mt-1">{inviteData?.email}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">Senha</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimo 6 caracteres"
                className="w-full pl-9 pr-10 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 focus:border-carmesim/30 outline-none"
                required
                minLength={6}
                data-testid="setup-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">Confirmar Senha</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repetir a senha"
                className="w-full pl-9 pr-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-carmesim/30 focus:border-carmesim/30 outline-none"
                required
                minLength={6}
                data-testid="setup-confirm-password"
              />
            </div>
            {confirmPassword && password !== confirmPassword && (
              <p className="text-xs text-carmesim mt-1">As senhas nao coincidem</p>
            )}
          </div>

          <button
            type="submit"
            disabled={submitting || password.length < 6 || password !== confirmPassword}
            className="w-full py-2.5 bg-carmesim hover:bg-carmesim/90 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="setup-submit"
          >
            {submitting ? 'A ativar...' : 'Ativar Conta'}
          </button>
        </form>
      </motion.div>
    </div>
  );
};
