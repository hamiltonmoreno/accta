// Fonte unica das categorias de transaccao seleccionaveis hoje (Cat 4 §5.4).
// Le do endpoint `GET /api/finances/meta/categories` (o backend e em lockstep
// com models.INCOME_CATEGORIES / EXPENSE_CATEGORIES) e devolve listas prontas
// para dropdowns. Categorias legadas (`patrocinios`, `doacoes`, ...) NAO entram
// — usar `CATEGORY_LABELS` em `financeiro/constants` para display historico.

import { useQuery } from '@tanstack/react-query';
import { financesAPI } from '../utils/api';
import { queryKeys } from '../lib/queryClient';

// Fallback offline (mesmo que models.INCOME_CATEGORIES). Usado enquanto o
// fetch nao resolve OU em testes que nao mockam a rede — evita render vazio.
const FALLBACK = {
  income: ['quotas', 'joias', 'subvencoes', 'donativos', 'venda_publicacoes', 'juros', 'extraordinarias'],
  expense: ['operacional', 'eventos', 'juridico', 'comunicacao', 'viagens', 'outros_despesa'],
  types: ['receita', 'despesa'],
  labels: {
    quotas: 'Quotas', joias: 'Jóias', subvencoes: 'Subvenções', donativos: 'Donativos',
    venda_publicacoes: 'Venda de Publicações', juros: 'Juros', extraordinarias: 'Receitas Extraordinárias',
    operacional: 'Operacional', eventos: 'Eventos', juridico: 'Jurídico',
    comunicacao: 'Comunicação', viagens: 'Viagens', outros_despesa: 'Outras Despesas',
  },
};

const _toOptions = (keys, labels) =>
  (keys || []).map((value) => ({ value, label: labels?.[value] || value }));

/**
 * Hook que devolve as categorias seleccionaveis para receitas/despesas, com
 * fallback offline. Cache longo (categorias mudam por release).
 *
 * @returns {{
 *   income: Array<{value: string, label: string}>,
 *   expense: Array<{value: string, label: string}>,
 *   types: string[],
 *   labels: Record<string, string>,
 *   isLoading: boolean,
 * }}
 */
export const useFinanceCategories = () => {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.finances.metaCategories(),
    queryFn: async () => (await financesAPI.getCategories()).data,
    staleTime: 10 * 60 * 1000, // 10 min — meta muda raramente
  });
  const src = data || FALLBACK;
  return {
    income: _toOptions(src.income, src.labels),
    expense: _toOptions(src.expense, src.labels),
    types: src.types || FALLBACK.types,
    labels: src.labels || FALLBACK.labels,
    isLoading,
  };
};

export default useFinanceCategories;
