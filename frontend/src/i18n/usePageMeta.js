import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { HREFLANG, SUPPORTED_LOCALES, DEFAULT_LOCALE, stripLocale, withLocale, useI18n } from './index';

const ALT_ATTR = 'data-i18n-alternate';

// Título, descrição e alternativas hreflang da página pública ativa.
// `ns` aponta para `<ns>.meta.title` / `<ns>.meta.description` nos dicionários.
export function usePageMeta(ns, vars) {
  const { t, locale } = useI18n();
  const { pathname } = useLocation();
  const title = t(`${ns}.meta.title`, vars);
  const description = t(`${ns}.meta.description`, vars);

  useEffect(() => {
    const previousTitle = document.title;
    document.title = title;

    let meta = document.querySelector('meta[name="description"]');
    const previousDescription = meta ? meta.getAttribute('content') : null;
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute('name', 'description');
      document.head.appendChild(meta);
    }
    meta.setAttribute('content', description);

    const base = stripLocale(pathname);
    const origin = window.location.origin;
    const links = [...SUPPORTED_LOCALES.map((l) => [HREFLANG[l], withLocale(base, l)]), ['x-default', withLocale(base, DEFAULT_LOCALE)]].map(
      ([hreflang, path]) => {
        const link = document.createElement('link');
        link.setAttribute('rel', 'alternate');
        link.setAttribute('hreflang', hreflang);
        link.setAttribute('href', `${origin}${path}`);
        link.setAttribute(ALT_ATTR, '');
        document.head.appendChild(link);
        return link;
      },
    );

    return () => {
      document.title = previousTitle;
      if (previousDescription !== null) meta.setAttribute('content', previousDescription);
      links.forEach((link) => link.remove());
    };
  }, [title, description, pathname, locale]);
}
