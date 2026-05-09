import { z } from 'zod';

// Schemas de validação partilhados pelos forms de autenticação.
// Mensagens em PT — alinham com o resto da UI.

const passwordRule = z
  .string()
  .min(6, 'A senha deve ter pelo menos 6 caracteres')
  .max(72, 'A senha não pode ter mais de 72 caracteres'); // bcrypt max

export const loginSchema = z.object({
  email: z.string().min(1, 'Email obrigatório').email('Email inválido'),
  password: z.string().min(1, 'Senha obrigatória'),
});

export const forgotPasswordSchema = z.object({
  email: z.string().min(1, 'Email obrigatório').email('Email inválido'),
});

// Setup de conta + reset de senha partilham a mesma estrutura
// (password + confirmPassword com match check).
const passwordPairSchema = z
  .object({
    password: passwordRule,
    confirmPassword: z.string().min(1, 'Confirme a senha'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'As senhas não coincidem',
  });

export const setupAccountSchema = passwordPairSchema;
export const resetPasswordSchema = passwordPairSchema;
