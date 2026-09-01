-- Corrige a semântica temporal de cti_atividades.created_at.
-- A view public.cti_atividades expõe dados de public.cti_atividades_registros.
-- O campo histórico created_at foi gravado em UTC como timestamp sem timezone;
-- concluida_em já é timestamptz. O navegador interpretava created_at como hora
-- local e exibia a criação +3h no Brasil.
--
-- A migração é idempotente: só converte quando a tabela-base ainda usa
-- timestamp without time zone. O instante real registrado é preservado.

do $$
begin
  if exists (
    select 1
      from information_schema.columns
     where table_schema = 'public'
       and table_name = 'cti_atividades_registros'
       and column_name = 'created_at'
       and data_type = 'timestamp without time zone'
  ) then
    drop view public.cti_atividades;

    alter table public.cti_atividades_registros
      alter column created_at type timestamptz
      using created_at at time zone 'UTC';

    create view public.cti_atividades as
    select id,
           cliente_id,
           oportunidade_id,
           usuario_id,
           tipo,
           descricao,
           status,
           data_atividade,
           created_at,
           proposta_id,
           pedido_id,
           titulo,
           data,
           horario,
           updated_at,
           concluida_em,
           registro_teste,
           arquivado_em,
           arquivado_por,
           motivo_arquivamento,
           lote_arquivamento_id,
           parceiro_nome,
           parceiro_tipo,
           parceiro_organizacao
      from public.cti_atividades_registros
     where arquivado_em is null;
  end if;
end
$$;

grant all privileges on table public.cti_atividades to anon;
grant all privileges on table public.cti_atividades to authenticated;
grant all privileges on table public.cti_atividades to service_role;
