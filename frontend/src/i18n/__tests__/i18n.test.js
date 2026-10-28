jest.mock('react-router-dom', () => ({ useLocation: () => ({ pathname: '/' }) }), { virtual: true });

import {
  localeFromPath,
  stripLocale,
  withLocale,
  preferredLocale,
  translate,
  STORAGE_KEY,
} from '../index';

describe('caminhos com locale', () => {
  test('localeFromPath', () => {
    expect(localeFromPath('/')).toBe('pt');
    expect(localeFromPath('/sobre')).toBe('pt');
    expect(localeFromPath('/en')).toBe('en');
    expect(localeFromPath('/fr/sobre')).toBe('fr');
    expect(localeFromPath('/entrar')).toBe('pt');
  });

  test('stripLocale / withLocale', () => {
    expect(stripLocale('/en/sobre')).toBe('/sobre');
    expect(stripLocale('/fr')).toBe('/');
    expect(stripLocale('/sobre')).toBe('/sobre');
    expect(withLocale('/', 'en')).toBe('/en');
    expect(withLocale('/sobre', 'fr')).toBe('/fr/sobre');
    expect(withLocale('/sobre', 'pt')).toBe('/sobre');
  });
});

describe('preferredLocale', () => {
  const nav = (languages, userAgent = 'Mozilla/5.0') => ({ languages, userAgent });
  beforeEach(() => window.localStorage.clear());

  test('usa o navegador quando não há escolha guardada', () => {
    expect(preferredLocale(nav(['fr-FR', 'en']))).toBe('fr');
    expect(preferredLocale(nav(['en-US']))).toBe('en');
    expect(preferredLocale(nav(['pt-PT', 'en']))).toBe('pt');
    expect(preferredLocale(nav(['es-ES', 'de']))).toBe('pt');
  });

  test('escolha guardada prevalece sobre o navegador', () => {
    window.localStorage.setItem(STORAGE_KEY, 'pt');
    expect(preferredLocale(nav(['en-US']))).toBe('pt');
    window.localStorage.setItem(STORAGE_KEY, 'fr');
    expect(preferredLocale(nav(['en-US']))).toBe('fr');
  });

  test('valor guardado inválido é ignorado', () => {
    window.localStorage.setItem(STORAGE_KEY, 'xx');
    expect(preferredLocale(nav(['en-US']))).toBe('en');
  });

  test('crawlers ficam sempre em PT', () => {
    window.localStorage.setItem(STORAGE_KEY, 'en');
    expect(preferredLocale(nav(['en-US'], 'Mozilla/5.0 (compatible; Googlebot/2.1)'))).toBe('pt');
  });
});

describe('translate', () => {
  test('devolve PT e interpola', () => {
    expect(translate('pt', 'layout.nav.home')).toBe('Início');
  });

  test('chave inexistente devolve a própria chave', () => {
    const warn = jest.spyOn(console, 'warn').mockImplementation(() => {});
    expect(translate('pt', 'nao.existe')).toBe('nao.existe');
    warn.mockRestore();
  });
});
