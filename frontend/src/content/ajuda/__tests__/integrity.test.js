import { ajudaSections } from '../index';

// Rotas privadas registadas em App.js que o manual pode referenciar.
const ROTAS_VALIDAS = new Set([
  '/dashboard', '/perfil', '/ajuda', '/carteira', '/ranking', '/notificacoes',
  '/votacoes', '/eventos', '/projetos', '/documentos', '/mural', '/galeria-admin',
  '/beneficios', '/regulamentos', '/formacoes', '/publicacoes', '/defesa-profissional',
  '/relacoes-externas', '/admin/assembleias', '/admin/eleicoes', '/admin/disciplinar',
  '/admin/pedidos-inscricao', '/admin/usuarios', '/admin/cargos', '/admin/comunicados',
  '/admin/logs', '/admin/aparencia', '/admin/noticias', '/financeiro', '/financeiro/co-aprovacoes',
  '/governanca/honorarios', '/participacao/peticoes',
  '/participacao/propostas', '/participacao/esclarecimentos', '/participacao/reclamacoes',
]);

describe('content/ajuda — integridade', () => {
  test('há secções e os ids são únicos', () => {
    expect(ajudaSections.length).toBeGreaterThan(0);
    const ids = ajudaSections.map((s) => s.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  test.each(ajudaSections.map((s) => [s.id, s]))('secção %s tem título, ícone e ≥1 artigo', (_id, s) => {
    expect(typeof s.titulo).toBe('string');
    expect(s.titulo.length).toBeGreaterThan(0);
    expect(s.icon).toBeTruthy();
    expect(Array.isArray(s.artigos)).toBe(true);
    expect(s.artigos.length).toBeGreaterThan(0);
  });

  test('artigos: ids únicos por secção, têm título e passos', () => {
    ajudaSections.forEach((s) => {
      const ids = s.artigos.map((a) => a.id);
      expect(new Set(ids).size).toBe(ids.length);
      s.artigos.forEach((a) => {
        expect(typeof a.titulo).toBe('string');
        expect(a.titulo.length).toBeGreaterThan(0);
        expect(Array.isArray(a.passos)).toBe(true);
        expect(a.passos.length).toBeGreaterThan(0);
      });
    });
  });

  test('todas as rotas referidas existem', () => {
    ajudaSections.forEach((s) => {
      s.artigos.forEach((a) => {
        if (a.rota) expect(ROTAS_VALIDAS.has(a.rota)).toBe(true);
      });
    });
  });
});
