import { format } from 'date-fns';
import { ptBR, enUS, fr } from 'date-fns/locale';
import { useI18n } from './index';

const DATE_LOCALES = { pt: ptBR, en: enUS, fr };

// Formata datas com o locale date-fns do idioma ativo (FR-023).
export function useFormatDate() {
  const { locale } = useI18n();
  return (date, pattern) => format(date, pattern, { locale: DATE_LOCALES[locale] });
}
