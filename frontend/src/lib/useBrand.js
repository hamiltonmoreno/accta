import { useQuery } from '@tanstack/react-query';
import { brandAPI } from '../utils/api';
import { queryKeys } from './queryClient';

const LS_KEY = 'accta:brand';

const readCache = () => {
  try {
    return JSON.parse(localStorage.getItem(LS_KEY)) || undefined;
  } catch {
    return undefined; // SSR / JSON inválido / storage indisponível
  }
};

/**
 * Hook único da marca pública (logo, ícone, favicon). Partilhado por BrandLogo,
 * BrandIcon e FaviconManager — antes cada um tinha a sua própria query igual.
 *
 * Semeia o primeiro render (sobretudo pós-refresh, com a cache do React Query
 * vazia) com a última marca conhecida em localStorage. Sem isto, `data` arranca
 * `undefined` e os componentes piscam o vetor por defeito antes de a query
 * resolver com a logo configurada. `initialDataUpdatedAt: 0` marca a semente
 * como stale → revalida já em background e reescreve a cache, pelo que uma troca
 * de logo no admin reflete-se no refresh seguinte.
 */
export const useBrand = () =>
  useQuery({
    queryKey: queryKeys.brand.public(),
    queryFn: async () => {
      const data = (await brandAPI.getPublic()).data;
      try {
        localStorage.setItem(LS_KEY, JSON.stringify(data));
      } catch {
        /* quota / storage indisponível — não é crítico */
      }
      return data;
    },
    initialData: readCache,
    initialDataUpdatedAt: 0,
    staleTime: 30 * 60 * 1000, // marca é quase-estática
  });

export default useBrand;
