import { buildNavContext, isNavItemVisible } from '../visibility';

const ctxFrom = (over = {}) =>
  buildNavContext({
    isAdmin: false,
    isFinanceiro: false,
    isModerador: false,
    isDirecao: false,
    isMesaAG: false,
    user: { role: 'socio', privileges: [] },
    ...over,
  });

describe('buildNavContext', () => {
  test('mapeia flags e o user', () => {
    const ctx = buildNavContext({ isAdmin: true, user: { role: 'admin', privileges: ['manage_users'] } });
    expect(ctx).toMatchObject({ isAdmin: true, role: 'admin', privileges: ['manage_users'] });
    expect(ctx.isFinanceiro).toBe(false);
  });
  test('privileges default a []', () => {
    expect(buildNavContext({}).privileges).toEqual([]);
  });
});

describe('isNavItemVisible', () => {
  test("roles 'all' é visível a qualquer um", () => {
    expect(isNavItemVisible({ roles: ['all'] }, ctxFrom())).toBe(true);
  });

  test('subheader passa sempre', () => {
    expect(isNavItemVisible({ subheader: 'X' }, ctxFrom())).toBe(true);
  });

  test('roles admin só para admin', () => {
    expect(isNavItemVisible({ roles: ['admin'] }, ctxFrom())).toBe(false);
    expect(isNavItemVisible({ roles: ['admin'] }, ctxFrom({ isAdmin: true }))).toBe(true);
  });

  test('financeiro: financeiro ou admin', () => {
    expect(isNavItemVisible({ roles: ['financeiro'] }, ctxFrom({ isFinanceiro: true }))).toBe(true);
    expect(isNavItemVisible({ roles: ['financeiro'] }, ctxFrom({ isAdmin: true }))).toBe(true);
    expect(isNavItemVisible({ roles: ['financeiro'] }, ctxFrom())).toBe(false);
  });

  test('privilégio concede acesso EXTRA mesmo sem o role', () => {
    const item = { roles: ['admin'], privileges: ['view_finances_readonly'] };
    expect(isNavItemVisible(item, ctxFrom())).toBe(false);
    const ctx = ctxFrom({ user: { role: 'socio', privileges: ['view_finances_readonly'] } });
    expect(isNavItemVisible(item, ctx)).toBe(true);
  });

  test("match 'direcao' requer admin ou Direção", () => {
    const item = { roles: ['admin'], match: 'direcao' };
    expect(isNavItemVisible(item, ctxFrom())).toBe(false);
    expect(isNavItemVisible(item, ctxFrom({ isDirecao: true }))).toBe(true);
  });

  test("match 'governanca' requer admin, Direção ou Mesa da AG", () => {
    const item = { roles: ['admin'], match: 'governanca' };
    expect(isNavItemVisible(item, ctxFrom({ isMesaAG: true }))).toBe(true);
    expect(isNavItemVisible(item, ctxFrom())).toBe(false);
  });

  test('item nulo é invisível', () => {
    expect(isNavItemVisible(null, ctxFrom())).toBe(false);
  });
});
