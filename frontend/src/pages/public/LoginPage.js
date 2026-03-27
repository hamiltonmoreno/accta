import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LogIn, Shield, Plane, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { toast } from 'sonner';
import { ACCTALogoHorizontal } from '../../components/ACCTALogo';

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({ email: '', password: '' });
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
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen flex">
      {/* Left: Visual Panel (hidden on mobile) */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-grafite overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=2074&auto=format&fit=crop"
          alt="Aviação"
          className="absolute inset-0 w-full h-full object-cover opacity-30"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-grafite via-grafite/80 to-grafite/40" />

        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <Link to="/" className="inline-flex">
            <ACCTALogoHorizontal dark />
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
              <span className="text-carmesim">Associado</span>
            </h2>
            <p className="text-white/60 text-lg max-w-sm leading-relaxed">
              Aceda a sua carteira digital, votacoes, documentos e muito mais.
            </p>
          </div>

          <p className="text-white/30 text-xs">
            &copy; {new Date().getFullYear()} ACCTA - Cabo Verde
          </p>
        </div>
      </div>

      {/* Right: Login Form */}
      <div className="flex-1 flex items-center justify-center px-5 py-8 bg-gray-50">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-sm"
        >
          {/* Mobile Logo */}
          <div className="lg:hidden text-center mb-8">
            <Link to="/" className="inline-flex justify-center mb-5">
              <ACCTALogoHorizontal />
            </Link>
          </div>

          {/* Back Link */}
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-sm text-gray-400 hover:text-grafite transition-colors mb-6"
            data-testid="back-to-home"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar ao inicio
          </Link>

          <div className="mb-6">
            <h1 className="font-bold text-2xl text-grafite mb-1" data-testid="login-title">Entrar na conta</h1>
            <p className="text-sm text-gray-500">Acesse o portal com as suas credenciais</p>
          </div>

          {/* Form */}
          <div className="card-technical p-6 sm:p-7">
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="email" className="block text-xs uppercase tracking-widest text-gray-400 mb-2 font-semibold">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 transition-all"
                  placeholder="seu@email.cv"
                  data-testid="login-email"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-xs uppercase tracking-widest text-gray-400 mb-2 font-semibold">
                  Senha
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-carmesim/40 focus:border-carmesim/40 transition-all"
                  placeholder="********"
                  data-testid="login-password"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-carmesim text-white hover:bg-carmesim-dark h-11 rounded-lg uppercase tracking-wider font-bold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                data-testid="login-submit"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <LogIn className="w-4 h-4" />
                    Entrar
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Demo Info */}
          <div className="mt-5 p-3 bg-grafite/5 border border-grafite/10 rounded-lg">
            <p className="text-xs text-gray-500 text-center">
              <span className="font-semibold text-grafite">Demo:</span> socio1@accta.cv / socio123
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
