import { z } from 'zod';

// Schemas de validação partilhados pelos forms de autenticação.
// Mensagens em PT — alinham com o resto da UI.

const passwordRule = z
  .string()
  .min(6, 'A palavra-passe deve ter pelo menos 6 caracteres')
  .max(72, 'A palavra-passe não pode ter mais de 72 caracteres'); // bcrypt max

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
    confirmPassword: z.string().min(1, 'Confirme a palavra-passe'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'As palavras-passe não coincidem',
  });

export const setupAccountSchema = passwordPairSchema;
export const resetPasswordSchema = passwordPairSchema;

// Auto-registo público de sócio (spec-auto-registo). Sem password — esta só é
// definida depois de o admin aprovar, via o fluxo setup-account. O campo
// `website` é um honeypot anti-bot (escondido no form; deve ficar vazio).
export const registrationSchema = z.object({
  name: z
    .string()
    .min(2, 'O nome deve ter pelo menos 2 caracteres')
    .max(100, 'O nome não pode ter mais de 100 caracteres'),
  email: z.string().min(1, 'Email obrigatório').email('Email inválido'),
  phone_number: z.string().max(30, 'Telefone demasiado longo').optional().or(z.literal('')),
  department: z.string().max(80, 'Departamento demasiado longo').optional().or(z.literal('')),
  cargo_declarado: z.string().min(1, 'Selecione um cargo'),
  // Patrocínio de admissão (Art. 8.3): 2 padrinhos sócios activos (member_id ou email).
  sponsor1: z.string().min(1, 'Indique o 1.º padrinho (nº de sócio ou email)'),
  sponsor2: z.string().min(1, 'Indique o 2.º padrinho (nº de sócio ou email)'),
  consent_data: z.boolean().refine((v) => v === true, {
    message: 'É necessário consentir o tratamento dos seus dados',
  }),
  website: z.string().optional().or(z.literal('')), // honeypot
}).refine((d) => !d.sponsor1 || !d.sponsor2 || d.sponsor1.trim() !== d.sponsor2.trim(), {
  path: ['sponsor2'],
  message: 'Os 2 padrinhos têm de ser distintos',
});
