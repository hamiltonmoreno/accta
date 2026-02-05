import React from 'react';
import { Link } from 'react-router-dom';
import { Plane, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const PublicLayout = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const navItems = [
    { label: 'Início', path: '/' },
    { label: 'Sobre', path: '/sobre' },
    { label: 'A Profissão', path: '/profissao' },
    { label: 'Benefícios', path: '/beneficios-publico' },
    { label: 'Transparência', path: '/transparencia' },
    { label: 'Contactos', path: '/contactos' },
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
      <footer className="bg-primary text-white mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-accent rounded-lg flex items-center justify-center">
                  <Plane className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <div className="font-outfit font-bold text-xl">ACCTA</div>
                  <div className="font-mono text-xs text-accent uppercase tracking-wider">Cabo Verde</div>
                </div>
              </div>
              <p className="text-sm text-slate-300 mb-4">
                Associação dos Controladores de Tráfego Aéreo de Cabo Verde
              </p>
              <p className="text-accent font-semibold italic">
                "Segurança no céu, união em terra."
              </p>
            </div>

            <div>
              <h3 className="font-outfit font-semibold mb-4">Links Rápidos</h3>
              <ul className="space-y-2 text-sm text-slate-300">
                <li><Link to="/sobre" className="hover:text-accent transition-colors">Sobre</Link></li>
                <li><Link to="/profissao" className="hover:text-accent transition-colors">A Profissão</Link></li>
                <li><Link to="/transparencia" className="hover:text-accent transition-colors">Transparência</Link></li>
                <li><Link to="/beneficios-publico" className="hover:text-accent transition-colors">Benefícios</Link></li>
                <li><Link to="/contactos" className="hover:text-accent transition-colors">Contactos</Link></li>
              </ul>
            </div>

            <div>
              <h3 className="font-outfit font-semibold mb-4">Área Reservada</h3>
              <ul className="space-y-2 text-sm text-slate-300">
                <li><Link to="/login" className="hover:text-accent transition-colors">Login Associados</Link></li>
                <li><Link to="/validador" className="hover:text-accent transition-colors">Validador QR</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/10 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-slate-400">
            <p>&copy; {new Date().getFullYear()} ACCTA - Todos os direitos reservados</p>
            <Link to="/privacidade" className="hover:text-accent transition-colors">Política de Privacidade</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};
