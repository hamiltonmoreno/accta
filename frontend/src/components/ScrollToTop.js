import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Repõe a posição de scroll no topo da página sempre que se muda de rota.
 *
 * O react-router (BrowserRouter) preserva a posição de scroll anterior ao
 * navegar — o que faz uma página nova abrir "a meio". Este componente corrige
 * isso: por defeito, cada navegação começa no topo.
 *
 * Exceção: links que apontam para uma secção específica (`/pagina#seccao`).
 * Nesse caso fazemos scroll até à âncora em vez do topo. Como o conteúdo pode
 * montar de forma assíncrona (rotas lazy / Suspense), tentamos algumas vezes
 * até o elemento existir.
 *
 * Não renderiza nada — tem de viver dentro do <BrowserRouter> para poder usar
 * useLocation().
 */
export const ScrollToTop = () => {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    if (hash) {
      // Link para uma secção: faz scroll até à âncora (#id).
      let frame;
      let tries = 0;
      const raw = hash.slice(1);
      // Hash pode vir com escapes inválidos (#%, #foo%zz) — decodeURIComponent
      // rebentaria; nesse caso usamos o valor cru em vez de quebrar o efeito.
      let id;
      try {
        id = decodeURIComponent(raw);
      } catch {
        id = raw;
      }
      const scrollToAnchor = () => {
        const el = document.getElementById(id);
        if (el) {
          el.scrollIntoView();
        } else if (tries < 20) {
          tries += 1;
          frame = requestAnimationFrame(scrollToAnchor);
        }
      };
      frame = requestAnimationFrame(scrollToAnchor);
      return () => cancelAnimationFrame(frame);
    }

    // Navegação normal: começa sempre do topo.
    window.scrollTo(0, 0);
    return undefined;
  }, [pathname, hash]);

  return null;
};
