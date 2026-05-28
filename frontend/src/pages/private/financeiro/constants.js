// Labels APENAS para display historico de transaccoes (Cat 4 §5.4). Mantem
// as keys estatutarias canonicas (Art. 5) + as legadas (`patrocinios`,
// `doacoes`, `outros_receita`) para que rows antigas continuem a render um
// label legivel enquanto `scripts/migrate_income_categories.py --apply` nao
// corre. NAO usar para construir o dropdown de seleccao — esse vem do hook
// `useFinanceCategories` (endpoint GET /finances/meta/categories).
export const CATEGORY_LABELS = {
  // Receitas estatutarias (Art. 5)
  quotas: 'Quotas', joias: 'Jóias', subvencoes: 'Subvenções',
  donativos: 'Donativos', venda_publicacoes: 'Venda de Publicações',
  juros: 'Juros', extraordinarias: 'Receitas Extraordinárias',
  // Receitas legadas (ate a migracao --apply)
  patrocinios: 'Patrocínios', doacoes: 'Doações', outros_receita: 'Outras Receitas',
  // Despesas
  operacional: 'Operacional', juridico: 'Jurídico',
  comunicacao: 'Comunicação', viagens: 'Viagens', eventos: 'Eventos', outros_despesa: 'Outras Despesas',
};

export const MONTH_NAMES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

export const PAGE_SIZE = 20;
