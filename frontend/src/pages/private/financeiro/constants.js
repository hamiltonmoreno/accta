// Categorias de receita estatutárias (Art. 5). Em lockstep com
// backend/models.py INCOME_CATEGORIES. Keys legadas mantidas só no mapa de
// labels para renderizar transacções ainda não migradas.
// TODO (F4): consumir GET /finances/meta/categories em vez de hard-codear.
export const CATEGORY_LABELS = {
  quotas: 'Quotas', joias: 'Jóias', subvencoes: 'Subvenções',
  donativos: 'Donativos', venda_publicacoes: 'Venda de Publicações',
  juros: 'Juros', extraordinarias: 'Receitas Extraordinárias',
  // legadas (até à migração)
  patrocinios: 'Patrocínios', doacoes: 'Doações', outros_receita: 'Outras Receitas',
  operacional: 'Operacional', juridico: 'Jurídico',
  comunicacao: 'Comunicação', viagens: 'Viagens', eventos: 'Eventos', outros_despesa: 'Outras Despesas',
};

export const MONTH_NAMES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

export const PAGE_SIZE = 20;

export const INCOME_CATEGORIES = [
  { value: 'quotas', label: 'Quotas' },
  { value: 'joias', label: 'Jóias' },
  { value: 'subvencoes', label: 'Subvenções' },
  { value: 'donativos', label: 'Donativos' },
  { value: 'venda_publicacoes', label: 'Venda de Publicações' },
  { value: 'juros', label: 'Juros' },
  { value: 'extraordinarias', label: 'Receitas Extraordinárias' },
];

export const EXPENSE_CATEGORIES = [
  { value: 'operacional', label: 'Operacional' },
  { value: 'eventos', label: 'Eventos' },
  { value: 'juridico', label: 'Jurídico' },
  { value: 'comunicacao', label: 'Comunicação' },
  { value: 'viagens', label: 'Viagens' },
  { value: 'outros_despesa', label: 'Outras Despesas' },
];
