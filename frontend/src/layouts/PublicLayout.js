import React from 'react';
import { Link } from 'react-router-dom';
import { Plane, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const PublicLayout = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const navItems = [
    { label: 'Início', path: '/' },
    { label: 'Sobre a Profissão', path: '/profissao' },
    { label: 'Notícias', path: '/noticias' },
    { label: 'Transparência', path: '/transparencia' },
    { label: 'Validador', path: '/validador' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass-effect">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center group-hover:bg-primary/90 transition-colors">
                <Plane className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="font-outfit font-bold text-xl text-primary">ACCTA</div>
                <div className="font-mono text-xs text-slate-500 uppercase tracking-wider">Cabo Verde</div>
              </div>
            </Link>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center gap-8">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className="font-manrope text-sm font-medium text-slate-700 hover:text-primary transition-colors"
                  data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  {item.label}
                </Link>
              ))}
              <Link
                to="/login"
                className="bg-primary text-white hover:bg-primary/90 h-10 px-6 rounded-md uppercase tracking-wider font-bold text-sm transition-all"
                data-testid="nav-login-button"
              >
                Entrar
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-slate-100 transition-colors"
              data-testid="mobile-menu-button"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Menu */}
          <AnimatePresence>
            {mobileMenuOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="md:hidden mt-4 pt-4 border-t border-slate-200"
              >
                <div className="flex flex-col gap-4">
                  {navItems.map((item) => (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className="font-manrope text-sm font-medium text-slate-700 hover:text-primary transition-colors"
                    >
                      {item.label}
                    </Link>
                  ))}
                  <Link
                    to="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="bg-primary text-white hover:bg-primary/90 h-10 px-6 rounded-md uppercase tracking-wider font-bold text-sm transition-all text-center flex items-center justify-center"
                  >
                    Entrar
                  </Link>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </nav>
      </header>

      {/* Main Content */}
      <main className="flex-1 pt-20">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-primary text-white mt-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <Plane className="w-8 h-8" />
                <div>
                  <div className="font-outfit font-bold text-xl">ACCTA</div>
                  <div className="font-mono text-xs text-accent uppercase tracking-wider">Cabo Verde</div>
                </div>
              </div>
              <p className="text-sm text-slate-300">
                Associação de Controladores de Tráfego Aéreo de Cabo Verde
              </p>
            </div>

            <div>
              <h3 className="font-outfit font-semibold mb-4">Links Rápidos</h3>
              <ul className="space-y-2 text-sm text-slate-300">
                <li><Link to="/" className="hover:text-accent transition-colors">Início</Link></li>
                <li><Link to="/profissao" className="hover:text-accent transition-colors">Sobre a Profissão</Link></li>
                <li><Link to="/noticias" className="hover:text-accent transition-colors">Notícias</Link></li>
              </ul>
            </div>

            <div>
              <h3 className="font-outfit font-semibold mb-4">Contato</h3>
              <ul className="space-y-2 text-sm text-slate-300">
                <li>Email: info@accta.cv</li>
                <li>Tel: +238 XXX XXXX</li>
                <li>Cabo Verde</li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/10 mt-8 pt-8 text-center text-sm text-slate-400">
            <p>&copy; {new Date().getFullYear()} ACCTA - Todos os direitos reservados</p>
          </div>
        </div>
      </footer>
    </div>
  );
};
