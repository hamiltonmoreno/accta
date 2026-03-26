import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LogIn } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { ACCTALogoHorizontal } from '../../components/ACCTALogo';

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const user = await login(formData);
      toast.success(`Bem-vindo, ${user.name}!`);
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-gray-50">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex justify-center mb-6">
            <ACCTALogoHorizontal />
          </Link>
          <h1 className="font-bold text-3xl text-grafite mb-2" data-testid="login-title">Portal do Associado</h1>
          <p className="text-gray-600">Acesse sua conta de sócio</p>
        </div>

        {/* Form */}
        <div className="card-technical rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-xs uppercase tracking-widest text-gray-500 mb-2 font-semibold">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim focus:border-transparent transition-all"
                placeholder="seu@email.cv"
                data-testid="login-email"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-xs uppercase tracking-widest text-gray-500 mb-2 font-semibold">
                Senha
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-carmesim focus:border-transparent transition-all"
                placeholder="••••••••"
                data-testid="login-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-carmesim text-white hover:bg-carmesim-dark h-12 px-6 rounded-lg uppercase tracking-wider font-bold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              data-testid="login-submit"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <LogIn className="w-5 h-5" />
                  Entrar
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link to="/" className="text-sm text-gray-500 hover:text-carmesim transition-colors">
              Voltar ao início
            </Link>
          </div>
        </div>

        {/* Demo Info */}
        <div className="mt-6 p-4 bg-carmesim/10 border border-carmesim/20 rounded-lg">
          <p className="text-sm text-gray-600 text-center">
            <strong className="text-grafite">Demo:</strong> socio1@accta.cv / socio123
          </p>
        </div>
      </motion.div>
    </div>
  );
};
