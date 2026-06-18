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

  test('campos opcionais (quandoUsar/quandoNaoUsar/campos) têm o shape esperado', () => {
    ajudaSections.forEach((s) => {
      s.artigos.forEach((a) => {
        ['quandoUsar', 'quandoNaoUsar'].forEach((k) => {
          if (a[k] !== undefined) {
            expect(Array.isArray(a[k])).toBe(true);
            a[k].forEach((line) => {
              expect(typeof line).toBe('string');
              expect(line.length).toBeGreaterThan(0);
            });
          }
        });
        if (a.campos !== undefined) {
          expect(Array.isArray(a.campos)).toBe(true);
          a.campos.forEach((c) => {
            // `campo` é obrigatório; `ajuda`/`exemplo` são opcionais mas, se
            // existirem, são strings não-vazias (o "como preencher").
            expect(typeof c.campo).toBe('string');
            expect(c.campo.length).toBeGreaterThan(0);
            ['ajuda', 'exemplo'].forEach((k) => {
              if (c[k] !== undefined) {
                expect(typeof c[k]).toBe('string');
                expect(c[k].length).toBeGreaterThan(0);
              }
            });
          });
        }
      });
    });
  });

  test('Governança tem o guia de decisão "Qual canal de voz devo usar?"', () => {
    const gov = ajudaSections.find((s) => s.id === 'governanca');
    expect(gov).toBeTruthy();
    expect(gov.artigos.some((a) => a.id === 'qual-canal')).toBe(true);
  });
});
