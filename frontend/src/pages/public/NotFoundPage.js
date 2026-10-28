import React from 'react';
import { Link } from 'react-router-dom';
import { useI18n } from '../../i18n';
import { usePageMeta } from '../../i18n/usePageMeta';

export function NotFoundPage() {
  const { t, lp } = useI18n();
  usePageMeta('notFound');
  return (
    <section className="min-h-[60vh] flex items-center justify-center px-4 py-16">
      <div className="max-w-md text-center">
        <p className="text-sm font-semibold text-carmesim mb-2">404</p>
        <h1 className="text-3xl font-bold text-grafite mb-3">{t('notFound.title')}</h1>
        <p className="text-grafite/70 mb-8">{t('notFound.body')}</p>
        <Link
          to={lp('/')}
          className="inline-flex items-center justify-center h-10 px-5 rounded-lg border border-[#D1D5DB] bg-white text-sm font-semibold text-grafite hover:bg-gray-50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2"
          data-testid="not-found-home"
        >
          {t('notFound.cta')}
        </Link>
      </div>
    </section>
  );
}
