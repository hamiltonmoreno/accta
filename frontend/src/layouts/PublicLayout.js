import React from 'react';
import { Link } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { ACCTALogoHorizontal } from '../components/ACCTALogo';

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
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md shadow-sm">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="group">
              <ACCTALogoHorizontal />
            </Link>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center gap-8">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className="text-sm font-medium text-grafite hover:text-carmesim transition-colors"
                  data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  {item.label}
                </Link>
              ))}
              <Link
                to="/login"
                className="bg-carmesim text-white hover:bg-carmesim-dark h-10 px-6 rounded-md uppercase tracking-wider font-bold text-sm transition-all flex items-center"
                data-testid="nav-login-button"
              >
                Entrar
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
              data-testid="mobile-menu-button"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6 text-grafite" />
              ) : (
                <Menu className="w-6 h-6 text-grafite" />
              )}
            </button>
          </div>
        </nav>

        {/* Mobile Menu */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden bg-white border-t border-gray-100"
            >
              <div className="px-4 py-4 space-y-2">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className="block py-3 px-4 rounded-lg text-grafite hover:bg-gray-50 hover:text-carmesim transition-colors font-medium"
                  >
                    {item.label}
                  </Link>
                ))}
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block py-3 px-4 bg-carmesim text-white rounded-lg text-center font-bold uppercase tracking-wider"
                >
                  Entrar
                </Link>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Page Content */}
      <main className="flex-grow pt-20">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-grafite text-white mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <ACCTALogoHorizontal dark className="mb-4" />
              <p className="text-sm text-gray-300 mb-4">
                Associação dos Controladores de Tráfego Aéreo de Cabo Verde
              </p>
              <p className="text-carmesim font-semibold italic">
                "Segurança no céu, união em terra."
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Links Rápidos</h3>
              <ul className="space-y-2 text-sm text-gray-300">
                <li><Link to="/sobre" className="hover:text-carmesim transition-colors">Sobre</Link></li>
                <li><Link to="/profissao" className="hover:text-carmesim transition-colors">A Profissão</Link></li>
                <li><Link to="/transparencia" className="hover:text-carmesim transition-colors">Transparência</Link></li>
                <li><Link to="/beneficios-publico" className="hover:text-carmesim transition-colors">Benefícios</Link></li>
                <li><Link to="/contactos" className="hover:text-carmesim transition-colors">Contactos</Link></li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Área Reservada</h3>
              <ul className="space-y-2 text-sm text-gray-300">
                <li><Link to="/login" className="hover:text-carmesim transition-colors">Login Associados</Link></li>
                <li><Link to="/validador" className="hover:text-carmesim transition-colors">Validador QR</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/10 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-gray-400">
            <p>&copy; {new Date().getFullYear()} ACCTA - Todos os direitos reservados</p>
            <Link to="/privacidade" className="hover:text-carmesim transition-colors">Política de Privacidade</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};
