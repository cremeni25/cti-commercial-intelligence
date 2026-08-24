-- SEC-001 — blindagem sem impacto operacional
-- Objetivo: impedir execução anônima das RPCs administrativas de homologação,
-- preservando integralmente ADMIN_MASTER autenticado e backend/service_role.

revoke execute on function public.cti_arquivar_homologacao_crm(uuid[], uuid, text) from public;
revoke execute on function public.cti_restaurar_homologacao_crm(uuid, uuid) from public;
revoke execute on function public.cti_registrar_teste_campo_automatico() from public;

grant execute on function public.cti_arquivar_homologacao_crm(uuid[], uuid, text) to authenticated, service_role;
grant execute on function public.cti_restaurar_homologacao_crm(uuid, uuid) to authenticated, service_role;
grant execute on function public.cti_registrar_teste_campo_automatico() to authenticated, service_role;
