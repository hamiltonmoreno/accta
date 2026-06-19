-- ============================================================================
-- DROP da tabela órfã `invoices` — issue #281 (pós-PR #276)
-- ----------------------------------------------------------------------------
-- O subsistema `invoices` foi removido por completo no PR #276 (rotas, modelos,
-- índices e `"invoices"` saiu de database.COLLECTIONS). A tabela física ficou
-- vazia e órfã em produção. Este script remove-a com um gate de segurança que
-- ABORTA se a tabela tiver linhas (não se dropa dados).
--
-- Para correr no Supabase SQL Editor (web console) ou via psql contra a DB de
-- produção. É idempotente: se a tabela já não existir, não faz nada.
--
-- PRÉ-CONDIÇÃO: o backend em produção tem de já correr a release que inclui o
-- PR #276 (sem "invoices" em COLLECTIONS). Senão, ensure_schema() recria a
-- tabela no próximo arranque. Ver docs/runbook-drop-invoices-prod.md.
-- ============================================================================

DO $$
DECLARE
    n bigint;
BEGIN
    IF to_regclass('public.invoices') IS NULL THEN
        RAISE NOTICE 'Tabela invoices nao existe — nada a fazer.';
        RETURN;
    END IF;

    SELECT count(*) INTO n FROM public.invoices;

    IF n <> 0 THEN
        RAISE EXCEPTION 'ABORTADO: invoices tem % linha(s); esperado 0. Investigar antes de dropar.', n;
    END IF;

    RAISE NOTICE 'invoices vazia (0 linhas) — a remover.';
    DROP TABLE public.invoices;
    RAISE NOTICE 'invoices removida.';
END $$;

-- Verificação pós-execução (deve devolver NULL):
--   SELECT to_regclass('public.invoices');
