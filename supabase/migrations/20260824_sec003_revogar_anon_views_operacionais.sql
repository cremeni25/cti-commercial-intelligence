-- SEC-003 — reduzir exposição anônima das views operacionais do CRM.
-- Esta migration não altera dados, não altera filtros de arquivamento e
-- preserva explicitamente os acessos de authenticated e service_role.
-- Aplicação somente após homologação do PR e validação funcional.

revoke all privileges on table public.cti_atividades from anon;
revoke all privileges on table public.cti_oportunidades from anon;
revoke all privileges on table public.cti_pipeline from anon;
revoke all privileges on table public.cti_propostas from anon;
revoke all privileges on table public.cti_pedidos from anon;
revoke all privileges on table public.vendas from anon;

grant select, insert, update, delete, truncate, references, trigger on table public.cti_atividades to authenticated, service_role;
grant select, insert, update, delete, truncate, references, trigger on table public.cti_oportunidades to authenticated, service_role;
grant select, insert, update, delete, truncate, references, trigger on table public.cti_pipeline to authenticated, service_role;
grant select, insert, update, delete, truncate, references, trigger on table public.cti_propostas to authenticated, service_role;
grant select, insert, update, delete, truncate, references, trigger on table public.cti_pedidos to authenticated, service_role;
grant select, insert, update, delete, truncate, references, trigger on table public.vendas to authenticated, service_role;
