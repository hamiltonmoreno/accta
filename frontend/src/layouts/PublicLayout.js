import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight } from 'lucide-react';
import { BrandLogo } from '../components/BrandLogo';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import { stripLocale, useI18n, useCta } from '../i18n';

export const PublicLayout = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const location = useLocation();
  const { t, lp } = useI18n();
  const { ASSOCIACAO_NOME } = useCta();
  const currentPath = stripLocale(location.pathname);

  const navItems = [
    { id: 'início', label: t('layout.nav.home'), path: '/' },
    { id: 'sobre', label: t('layout.nav.about'), path: '/sobre' },
    { id: 'a-profissão', label: t('layout.nav.profession'), path: '/profissao' },
    { id: 'publicações', label: t('layout.nav.publications'), path: '/publicacoes-publico' },
    { id: 'contactos', label: t('layout.nav.contacts'), path: '/contactos' },
    { id: 'galeria', label: t('layout.nav.gallery'), path: '/galeria' },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[60] focus:px-4 focus:py-2 focus:bg-white focus:text-grafite focus:rounded-lg focus:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40"
      >
        {t('layout.skipToContent')}
      </a>
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-100">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between">
            <Link to={lp('/')} className="flex-shrink-0">
              <BrandLogo />
            </Link>

            {/* Desktop Nav */}
            <div className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => {
                const isActive = item.path === '/' ? currentPath === '/' : currentPath.startsWith(item.path);
                return (
                  <Link
                    key={item.path}
                    to={lp(item.path)}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'text-carmesim bg-carmesim/5'
                        : 'text-grafite/80 hover:text-grafite hover:bg-gray-50'
                    }`}
                    data-testid={`nav-${item.id}`}
                  >
                    {item.label}
                  </Link>
                );
              })}
              <LanguageSwitcher className="ml-1" />
              <Link
                to={lp('/login')}
                className="ml-2 bg-grafite text-white hover:bg-grafite/90 h-9 px-5 rounded-lg font-semibold text-xs transition-colors flex items-center gap-2"
                data-testid="nav-login-button"
              >
                {t('layout.login')}
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {/* Mobile: seletor sempre visível + botão de menu */}
            <div className="lg:hidden flex items-center gap-1">
              <LanguageSwitcher />
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2.5 -mr-2.5 rounded-lg hover:bg-gray-100 transition-colors touch-target"
                data-testid="mobile-menu-button"
                aria-label={mobileMenuOpen ? t('layout.closeMenu') : t('layout.openMenu')}
                aria-expanded={mobileMenuOpen}
              >
                {mobileMenuOpen ? (
                  <X className="w-5 h-5 text-grafite" aria-hidden="true" />
                ) : (
                  <Menu className="w-5 h-5 text-grafite" aria-hidden="true" />
                )}
              </button>
            </div>
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
                    to={lp(item.path)}
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
                  to={lp('/login')}
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center gap-2 py-3 px-4 bg-grafite text-white hover:bg-grafite/90 transition-colors rounded-lg font-semibold text-sm"
                >
                  {t('layout.login')}
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
                {t('layout.tagline')}
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-sm uppercase tracking-wider mb-4 text-white/90">{t('layout.footer.quickLinks')}</h3>
              <ul className="space-y-2.5 text-sm text-white/60">
                <li><Link to={lp('/sobre')} className="hover:text-white transition-colors">{t('layout.footer.about')}</Link></li>
                <li><Link to={lp('/profissao')} className="hover:text-white transition-colors">{t('layout.footer.profession')}</Link></li>
                <li><Link to={lp('/beneficios-publico')} className="hover:text-white transition-colors">{t('layout.footer.benefits')}</Link></li>
                <li><Link to={lp('/contactos')} className="hover:text-white transition-colors">{t('layout.footer.contacts')}</Link></li>
                <li><Link to={lp('/galeria')} className="hover:text-white transition-colors">{t('layout.footer.gallery')}</Link></li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold text-sm uppercase tracking-wider mb-4 text-white/90">{t('layout.footer.reservedArea')}</h3>
              <ul className="space-y-2.5 text-sm text-white/60">
                <li><Link to={lp('/login')} className="hover:text-white transition-colors">{t('layout.footer.memberLogin')}</Link></li>
                <li><Link to={lp('/validador')} className="hover:text-white transition-colors">{t('layout.footer.qrValidator')}</Link></li>
                <li><Link to={lp('/eventos-publico')} className="hover:text-white transition-colors">{t('layout.footer.events')}</Link></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-white/10 mt-8 pt-6 flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-white/50">
            <p>&copy; {new Date().getFullYear()} {t('layout.footer.rights')}</p>
            <div className="flex items-center gap-4">
              <Link to={lp('/plataforma')} className="hover:text-white transition-colors">{t('layout.footer.platform')}</Link>
              <Link to="/privacidade" className="hover:text-white transition-colors">{t('layout.footer.privacy')}</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
