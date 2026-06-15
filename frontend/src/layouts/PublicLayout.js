import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight } from 'lucide-react';
import { BrandLogo } from '../components/BrandLogo';
import { ASSOCIACAO_NOME } from '../content/cta';

export const PublicLayout = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const location = useLocation();
  const currentPath = location.pathname;

  const navItems = [
    { label: 'Início', path: '/' },
    { label: 'Sobre', path: '/sobre' },
    { label: 'A Profissão', path: '/profissao' },
    { label: 'Benefícios', path: '/beneficios-publico' },
    { label: 'Transparência', path: '/transparencia' },
    { label: 'Publicações', path: '/publicacoes-publico' },
    { label: 'Contactos', path: '/contactos' },
    { label: 'Galeria', path: '/galeria' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[60] focus:px-4 focus:py-2 focus:bg-white focus:text-grafite focus:rounded-lg focus:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
      >
        Saltar para o conteúdo
      </a>
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-100">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex-shrink-0">
              <BrandLogo />
            </Link>

            {/* Desktop Nav */}
            <div className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = item.path === '/' ? currentPath === '/' : currentPath.startsWith(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'text-carmesim bg-carmesim/5'
                        : 'text-grafite/80 hover:text-grafite hover:bg-gray-50'
                    }`}
                    data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    {item.label}
                  </Link>
                );
              })}
              <Link
                to="/login"
                className="ml-3 bg-grafite text-white hover:bg-grafite/90 h-9 px-5 rounded-lg font-semibold text-xs transition-colors flex items-center gap-2"
                data-testid="nav-login-button"
              >
                Login
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2.5 -mr-2.5 rounded-lg hover:bg-gray-100 transition-colors touch-target"
              data-testid="mobile-menu-button"
              aria-label={mobileMenuOpen ? 'Fechar menu' : 'Abrir menu'}
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? (
                <X className="w-5 h-5 text-grafite" aria-hidden="true" />
              ) : (
                <Menu className="w-5 h-5 text-grafite" aria-hidden="true" />
              )}
            </button>
          </div>
        </nav>

        {/* Mobile Menu — CSS transitions (max-height + opacity), sem framer.
            grid-rows-[0fr/1fr] truque permite height auto sem max-height
            magico. Quando fechado: pointer-events-none para nao capturar clicks. */}
        <div
          className={`lg:hidden bg-white border-t border-gray-100 overflow-hidden grid transition-all duration-[240ms] ease-spring ${
            mobileMenuOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0 pointer-events-none'
          }`}
        >
          <div className="overflow-hidden">
            <div className="px-4 py-3 space-y-1">
              {navItems.map((item) => {
                const isActive = item.path === '/' ? currentPath === '/' : currentPath.startsWith(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center justify-between py-3 px-4 rounded-lg font-medium transition-colors ${
                      isActive
                        ? 'text-carmesim bg-carmesim/5'
                        : 'text-grafite hover:bg-gray-50'
                    }`}
                  >
                    <span className="text-sm">{item.label}</span>
                    {isActive && <div className="w-1.5 h-1.5 bg-carmesim rounded-full" />}
                  </Link>
                );
              })}
              <div className="pt-2">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center gap-2 py-3 px-4 bg-grafite text-white hover:bg-grafite/90 transition-colors rounded-lg font-semibold text-sm"
                >
                  Login
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Page Content */}
      <main id="main-content" tabIndex={-1} className="flex-grow pt-16 lg:pt-navbar outline-none">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-grafite text-white mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-12">
          <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-8">
            <div className="col-span-2 sm:col-span-2 md:col-span-2">
              <BrandLogo dark className="mb-4" />
              <p className="text-sm text-white/70 mb-3 max-w-sm">
                {ASSOCIACAO_NOME}
              </p>
              <p className="text-white font-semibold italic text-sm">
                "Segurança no céu, união em terra."
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-sm uppercase tracking-wider mb-4 text-white/90">Links Rápidos</h3>
              <ul className="space-y-2.5 text-sm text-white/60">
                <li><Link to="/sobre" className="hover:text-white transition-colors">Sobre</Link></li>
                <li><Link to="/profissao" className="hover:text-white transition-colors">A Profissão</Link></li>
                <li><Link to="/transparencia" className="hover:text-white transition-colors">Transparência</Link></li>
                <li><Link to="/beneficios-publico" className="hover:text-white transition-colors">Benefícios</Link></li>
                <li><Link to="/contactos" className="hover:text-white transition-colors">Contactos</Link></li>
                <li><Link to="/galeria" className="hover:text-white transition-colors">Galeria</Link></li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-sm uppercase tracking-wider mb-4 text-white/90">Área Reservada</h3>
              <ul className="space-y-2.5 text-sm text-white/60">
                <li><Link to="/login" className="hover:text-white transition-colors">Login Associados</Link></li>
                <li><Link to="/validador" className="hover:text-white transition-colors">Validador QR</Link></li>
                <li><Link to="/eventos-publico" className="hover:text-white transition-colors">Eventos</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/10 mt-8 pt-6 flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-white/50">
            <p>&copy; {new Date().getFullYear()} ACCTA - Todos os direitos reservados</p>
            <Link to="/privacidade" className="hover:text-white transition-colors">Política de Privacidade</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};
