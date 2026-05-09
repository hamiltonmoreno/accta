/**
 * Unit tests para os zod schemas dos forms de auth.
 * Sem render — só validação pura.
 */

import {
  loginSchema,
  forgotPasswordSchema,
  setupAccountSchema,
  resetPasswordSchema,
} from '../authSchemas';

const expectError = (result, path, message) => {
  expect(result.success).toBe(false);
  if (!result.success) {
    const issue = result.error.issues.find((i) => i.path[0] === path);
    expect(issue).toBeDefined();
    if (message) expect(issue.message).toBe(message);
  }
};

// ---------- loginSchema ----------

describe('loginSchema', () => {
  test('aceita email + password validos', () => {
    const r = loginSchema.safeParse({ email: 'user@x.com', password: 'abc' });
    expect(r.success).toBe(true);
  });

  test('rejeita email vazio', () => {
    const r = loginSchema.safeParse({ email: '', password: 'abc' });
    expectError(r, 'email');
  });

  test('rejeita email malformado', () => {
    const r = loginSchema.safeParse({ email: 'not-an-email', password: 'abc' });
    expectError(r, 'email', 'Email inválido');
  });

  test('rejeita password vazia', () => {
    const r = loginSchema.safeParse({ email: 'user@x.com', password: '' });
    expectError(r, 'password');
  });
});

// ---------- forgotPasswordSchema ----------

describe('forgotPasswordSchema', () => {
  test('aceita email valido', () => {
    expect(forgotPasswordSchema.safeParse({ email: 'a@b.cv' }).success).toBe(true);
  });

  test('rejeita email vazio', () => {
    expectError(forgotPasswordSchema.safeParse({ email: '' }), 'email');
  });

  test('rejeita email sem dominio', () => {
    expectError(forgotPasswordSchema.safeParse({ email: 'foo@' }), 'email');
  });
});

// ---------- setupAccountSchema / resetPasswordSchema ----------

describe('setupAccountSchema (= resetPasswordSchema)', () => {
  test('aceita passwords validas e iguais', () => {
    const r = setupAccountSchema.safeParse({
      password: 'secret123',
      confirmPassword: 'secret123',
    });
    expect(r.success).toBe(true);
  });

  test('rejeita password com menos de 6 caracteres', () => {
    const r = setupAccountSchema.safeParse({
      password: 'abc',
      confirmPassword: 'abc',
    });
    expectError(r, 'password', 'A senha deve ter pelo menos 6 caracteres');
  });

  test('rejeita password com mais de 72 caracteres (limite bcrypt)', () => {
    const long = 'a'.repeat(73);
    const r = setupAccountSchema.safeParse({
      password: long,
      confirmPassword: long,
    });
    expectError(r, 'password');
  });

  test('rejeita confirmPassword vazia', () => {
    const r = setupAccountSchema.safeParse({
      password: 'secret123',
      confirmPassword: '',
    });
    expectError(r, 'confirmPassword');
  });

  test('rejeita passwords diferentes (refine match)', () => {
    const r = setupAccountSchema.safeParse({
      password: 'secret123',
      confirmPassword: 'secret124',
    });
    expectError(r, 'confirmPassword', 'As senhas não coincidem');
  });

  test('resetPasswordSchema partilha o mesmo schema', () => {
    expect(resetPasswordSchema).toBe(setupAccountSchema);
  });
});
