// i18n do site público (spec 021). PT é a fonte canónica; EN/FR são projeções
// carregadas em lazy. A área privada nunca usa este módulo (fica PT).
import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import * as ctaPt from '../content/cta';
import pt from './locales/pt';

export const SUPPORTED_LOCALES = ['pt', 'en', 'fr'];
export const DEFAULT_LOCALE = 'pt';
export const STORAGE_KEY = 'accta.locale';
export const HTML_LANG = { pt: 'pt-CV', en: 'en', fr: 'fr' };
export const HREFLANG = { pt: 'pt-PT', en: 'en', fr: 'fr' };

const LOADERS = {
  en: () => import(/* webpackChunkName: "i18n-en" */ './locales/en'),
  fr: () => import(/* webpackChunkName: "i18n-fr" */ './locales/fr'),
};
const dictionaries = { pt };

const CRAWLER_RE = /bot|crawl|spider|slurp|bingpreview|facebookexternalhit|whatsapp|linkedin|embedly|preview/i;

export function localeFromPath(pathname = '/') {
  const seg = pathname.split('/')[1];
  return seg === 'en' || seg === 'fr' ? seg : DEFAULT_LOCALE;
}

export function stripLocale(pathname = '/') {
  const locale = localeFromPath(pathname);
  if (locale === DEFAULT_LOCALE) return pathname;
  return pathname.slice(locale.length + 1) || '/';
}

export function withLocale(path, locale) {
  if (locale === DEFAULT_LOCALE) return path;
  return path === '/' ? `/${locale}` : `/${locale}${path}`;
}

export function readStoredLocale() {
  try {
    const v = window.localStorage.getItem(STORAGE_KEY);
    return SUPPORTED_LOCALES.includes(v) ? v : null;
  } catch {
    return null;
  }
}

export function storeLocale(locale) {
  try {
    window.localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // janela privada / storage bloqueado: a escolha vale só para esta navegação
  }
}

// Idioma a usar numa rota pública SEM prefixo: escolha guardada → navegador → PT.
// Crawlers ficam sempre em PT para o canónico continuar indexado.
export function preferredLocale(nav = typeof navigator !== 'undefined' ? navigator : null) {
  if (!nav || CRAWLER_RE.test(nav.userAgent || '')) return DEFAULT_LOCALE;
  const stored = readStoredLocale();
  if (stored) return stored;
  const langs = nav.languages && nav.languages.length ? nav.languages : [nav.language || ''];
  for (const lang of langs) {
    const base = String(lang || '').toLowerCase().slice(0, 2);
    if (SUPPORTED_LOCALES.includes(base)) return base;
  }
  return DEFAULT_LOCALE;
}

function lookup(dict, key) {
  return key.split('.').reduce((node, part) => (node == null ? undefined : node[part]), dict);
}

function interpolate(value, vars) {
  if (!vars || typeof value !== 'string') return value;
  return value.replace(/\{(\w+)\}/g, (match, name) => (name in vars ? String(vars[name]) : match));
}

export function translate(locale, key, vars) {
  let value = lookup(dictionaries[locale], key);
  if (value === undefined && locale !== DEFAULT_LOCALE) {
    if (process.env.NODE_ENV !== 'production') console.warn(`[i18n] falta ${locale}:${key}`);
    value = lookup(dictionaries[DEFAULT_LOCALE], key);
  }
  if (value === undefined) {
    if (process.env.NODE_ENV !== 'production') console.warn(`[i18n] chave inexistente: ${key}`);
    return key;
  }
  return interpolate(value, vars);
}

const I18nContext = createContext(null);

export function I18nProvider({ children, fallback = null }) {
  const { pathname } = useLocation();
  const locale = localeFromPath(pathname);
  const [, setLoaded] = useState(0);
  const ready = Boolean(dictionaries[locale]);

  useEffect(() => {
    if (ready) return undefined;
    let alive = true;
    LOADERS[locale]().then((mod) => {
      dictionaries[locale] = mod.default;
      if (alive) setLoaded((n) => n + 1);
    });
    return () => {
      alive = false;
    };
  }, [locale, ready]);

  useEffect(() => {
    document.documentElement.lang = HTML_LANG[locale];
  }, [locale]);

  const value = useMemo(
    () => ({
      locale,
      t: (key, vars) => translate(locale, key, vars),
      lp: (path) => withLocale(path, locale),
      cta: locale === DEFAULT_LOCALE ? ctaPt : (dictionaries[locale] && dictionaries[locale].cta) || ctaPt,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [locale, ready],
  );

  if (!ready) return fallback;
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

const FALLBACK_CONTEXT = {
  locale: DEFAULT_LOCALE,
  t: (key, vars) => translate(DEFAULT_LOCALE, key, vars),
  lp: (path) => path,
  cta: ctaPt,
};

// Fora do provider (ex.: testes que montam uma página isolada) comporta-se como PT.
export function useI18n() {
  return useContext(I18nContext) || FALLBACK_CONTEXT;
}

export function useCta() {
  return useI18n().cta;
}
