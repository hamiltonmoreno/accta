import ptLogin from './locales/pt/login';
import { useI18n } from './index';

// As mensagens zod de utils/authSchemas.js estão em PT; traduz por correspondência
// exata com `login.validation` (PT). Mensagem desconhecida passa inalterada.
export function useValidationMessage() {
  const { t } = useI18n();
  return (message) => {
    const key = Object.keys(ptLogin.validation).find((k) => ptLogin.validation[k] === message);
    return key ? t(`login.validation.${key}`) : message;
  };
}
