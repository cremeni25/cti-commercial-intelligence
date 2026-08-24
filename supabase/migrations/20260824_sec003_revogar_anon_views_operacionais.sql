-- SEC-003 — reduzir exposição anônima das views operacionais do CRM.
-- Esta migration não altera dados, não altera filtros de arquivamento e
-- não modifica os privilégios já existentes de authenticated ou service_role.
-- Aplicação somente após homologação do PR e validação funcional.

revoke all privileges on table public.cti_atividades from anon;
revoke all privileges on table public.cti_oportunidades from anon;
revoke all privileges on table public.cti_pipeline from anon;
revoke all privileges on table public.cti_propostas from anon;
revoke all privileges on table public.cti_pedidos from anon;
revoke all privileges on table public.vendas from anon;
