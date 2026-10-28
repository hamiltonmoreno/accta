import React from 'react';
import { Languages } from 'lucide-react';
import { useI18n } from '../i18n';
import { cn } from '../lib/utils';

// Aviso discreto para conteúdo administrado (só em PT) quando o shell está em EN/FR.
export function PortugueseContentNotice({ className }) {
  const { locale, t } = useI18n();
  if (locale === 'pt') return null;
  return (
    <p
      className={cn('inline-flex items-center gap-2 rounded-md bg-[#F5F5F5] px-3 py-1.5 text-xs text-grafite/80', className)}
      data-testid="pt-content-notice"
    >
      <Languages className="w-3.5 h-3.5" aria-hidden="true" />
      {t('contentNotice.text')}
    </p>
  );
}
