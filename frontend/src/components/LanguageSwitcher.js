import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Globe, Check } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from './ui/dropdown-menu';
import { SUPPORTED_LOCALES, stripLocale, withLocale, storeLocale, useI18n } from '../i18n';
import { cn } from '../lib/utils';

// Rótulos nativos — nunca bandeiras (FR-012).
export const LOCALE_LABELS = { pt: 'Português', en: 'English', fr: 'Français' };
const ACTIVE_LABEL = { pt: 'ativo', en: 'active', fr: 'actif' };

export function LanguageSwitcher({ className, onChange }) {
  const { locale, t } = useI18n();
  const location = useLocation();
  const navigate = useNavigate();

  const choose = (target) => {
    storeLocale(target);
    if (target !== locale) {
      const path = withLocale(stripLocale(location.pathname), target);
      navigate(`${path}${location.search}${location.hash}`);
    }
    if (onChange) onChange(target);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className={cn(
          'inline-flex items-center gap-1.5 h-9 px-3 rounded-lg text-sm font-medium text-grafite/80 hover:text-grafite hover:bg-gray-50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[#C7202F]/40 focus-visible:ring-offset-2',
          className,
        )}
        aria-label={`${t('languageSwitcher.label')}: ${LOCALE_LABELS[locale]}`}
        data-testid="language-switcher"
      >
        <Globe className="w-4 h-4" aria-hidden="true" />
        <span>{locale.toUpperCase()}</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[10rem]">
        {SUPPORTED_LOCALES.map((l) => {
          const active = l === locale;
          return (
            <DropdownMenuItem
              key={l}
              lang={l === 'pt' ? 'pt' : l}
              aria-current={active ? 'true' : undefined}
              onSelect={() => choose(l)}
              className={cn('flex items-center justify-between gap-3 cursor-pointer', active && 'font-semibold text-carmesim')}
              data-testid={`language-option-${l}`}
            >
              <span>{LOCALE_LABELS[l]}</span>
              {active && (
                <>
                  <Check className="w-4 h-4" aria-hidden="true" />
                  <span className="sr-only">, {ACTIVE_LABEL[l]}</span>
                </>
              )}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
