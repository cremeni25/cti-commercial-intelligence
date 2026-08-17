-- Arquivamento coordenado e reversível do histórico de homologação do CRM App.
-- Registros permanecem fisicamente preservados em *_registros; as views operacionais
-- exibem apenas linhas com arquivado_em IS NULL.

begin;

-- Oportunidades já seguem o padrão view + tabela física.
alter table public.cti_oportunidades_registros
  add column if not exists lote_arquivamento_id uuid;

-- Converte as demais fontes operacionais em view ativa sobre tabela física preservada.
do $$
begin
  if to_regclass('public.cti_oportunidade_itens_registros') is null then
    alter table public.cti_oportunidade_itens rename to cti_oportunidade_itens_registros;
  end if;
  if to_regclass('public.cti_pipeline_registros') is null then
    alter table public.cti_pipeline rename to cti_pipeline_registros;
  end if;
  if to_regclass('public.cti_atividades_registros') is null then
    alter table public.cti_atividades rename to cti_atividades_registros;
  end if;
  if to_regclass('public.cti_propostas_registros') is null then
    alter table public.cti_propostas rename to cti_propostas_registros;
  end if;
  if to_regclass('public.cti_proposta_aceites_registros') is null then
    alter table public.cti_proposta_aceites rename to cti_proposta_aceites_registros;
  end if;
  if to_regclass('public.cti_pedidos_registros') is null then
    alter table public.cti_pedidos rename to cti_pedidos_registros;
  end if;
  if to_regclass('public.cti_envios_carrier_registros') is null then
    alter table public.cti_envios_carrier rename to cti_envios_carrier_registros;
  end if;
  if to_regclass('public.vendas_registros') is null then
    alter table public.vendas rename to vendas_registros;
  end if;
end $$;

alter table public.cti_oportunidade_itens_registros
  add column if not exists registro_teste boolean not null default false,
  add column if not exists arquivado_em timestamptz,
  add column if not exists arquivado_por uuid,
  add column if not exists motivo_arquivamento text,
  add column if not exists lote_arquivamento_id uuid;

alter table public.cti_pipeline_registros
  add column if not exists registro_teste boolean not null default false,
  add column if not exists arquivado_em timestamptz,
  add column if not exists arquivado_por uuid,
  add column if not exists motivo_arquivamento text,
  add column if not exists lote_arquivamento_id uuid;

alter table public.cti_atividades_registros
  add column if not exists registro_teste boolean not null default false,
  add column if not exists arquivado_em timestamptz,
  add column if not exists arquivado_por uuid,
  add column if not exists motivo_arquivamento text,
  add column if not exists lote_arquivamento_id uuid;

alter table public.cti_propostas_registros
  add column if not exists registro_teste boolean not null default false,
  add column if not exists arquivado_em timestamptz,
  add column if not exists arquivado_por uuid,
  add column if not exists motivo_arquivamento text,
  add column if not exists lote_arquivamento_id uuid;

alter table public.cti_proposta_aceites_registros
  add column if not exists registro_teste boolean not null default false,
  add column if not exists arquivado_em timestamptz,
  add column if not exists arquivado_por uuid,
  add column if not exists motivo_arquivamento text,
  add column if not exists lote_arquivamento_id uuid;

alter table public.cti_pedidos_registros
  add column if not exists registro_teste boolean not null default false,
  add column if not exists arquivado_em timestamptz,
  add column if not exists arquivado_por uuid,
  add column if not exists motivo_arquivamento text,
  add column if not exists lote_arquivamento_id uuid;

alter table public.cti_envios_carrier_registros
  add column if not exists registro_teste boolean not null default false,
  add column if not exists arquivado_em timestamptz,
  add column if not exists arquivado_por uuid,
  add column if not exists motivo_arquivamento text,
  add column if not exists lote_arquivamento_id uuid;

alter table public.vendas_registros
  add column if not exists registro_teste boolean not null default false,
  add column if not exists arquivado_em timestamptz,
  add column if not exists arquivado_por uuid,
  add column if not exists motivo_arquivamento text,
  add column if not exists lote_arquivamento_id uuid;

create or replace view public.cti_oportunidade_itens as
select * from public.cti_oportunidade_itens_registros where arquivado_em is null
with local check option;

create or replace view public.cti_pipeline as
select * from public.cti_pipeline_registros where arquivado_em is null
with local check option;

create or replace view public.cti_atividades as
select * from public.cti_atividades_registros where arquivado_em is null
with local check option;

create or replace view public.cti_propostas as
select * from public.cti_propostas_registros where arquivado_em is null
with local check option;

create or replace view public.cti_proposta_aceites as
select * from public.cti_proposta_aceites_registros where arquivado_em is null
with local check option;

create or replace view public.cti_pedidos as
select * from public.cti_pedidos_registros where arquivado_em is null
with local check option;

create or replace view public.cti_envios_carrier as
select * from public.cti_envios_carrier_registros where arquivado_em is null
with local check option;

-- A view legada de envios passa a respeitar o filtro operacional.
create or replace view public.cti_envios_comerciais as
select id, pedido_id, proposta_id, destinatarios, documentos, assunto, corpo, status,
       tentativas, erro, enviado_por, created_at, enviado_em
from public.cti_envios_carrier;

create or replace view public.vendas as
select * from public.vendas_registros where arquivado_em is null
with local check option;

-- Preserva o contrato REST/PostgREST das fontes que antes eram tabelas.
grant select, insert, update, delete on public.cti_oportunidade_itens to anon, authenticated, service_role;
grant select, insert, update, delete on public.cti_pipeline to anon, authenticated, service_role;
grant select, insert, update, delete on public.cti_atividades to anon, authenticated, service_role;
grant select, insert, update, delete on public.cti_propostas to anon, authenticated, service_role;
grant select, insert, update, delete on public.cti_proposta_aceites to anon, authenticated, service_role;
grant select, insert, update, delete on public.cti_pedidos to anon, authenticated, service_role;
grant select, insert, update, delete on public.cti_envios_carrier to anon, authenticated, service_role;
grant select on public.cti_envios_comerciais to anon, authenticated, service_role;
grant select, insert, update, delete on public.vendas to anon, authenticated, service_role;

create table if not exists public.cti_crm_homologacao_auditoria (
  id uuid primary key default gen_random_uuid(),
  lote_id uuid not null,
  acao text not null check (acao in ('ARQUIVAR_HOMOLOGACAO','RESTAURAR_HOMOLOGACAO')),
  usuario_id uuid,
  motivo text,
  oportunidade_ids uuid[] not null default '{}',
  resumo jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  revertido_em timestamptz,
  revertido_por uuid
);

create index if not exists idx_cti_crm_homologacao_auditoria_lote
  on public.cti_crm_homologacao_auditoria(lote_id, created_at desc);

grant select, insert, update on public.cti_crm_homologacao_auditoria to service_role;

create or replace function public.cti_arquivar_homologacao_crm(
  p_oportunidade_ids uuid[],
  p_usuario_id uuid,
  p_motivo text default 'Registros criados para teste/homologação'
) returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_lote uuid := gen_random_uuid();
  v_agora timestamptz := now();
  v_ops uuid[];
  v_itens uuid[] := '{}'::uuid[];
  v_propostas uuid[] := '{}'::uuid[];
  v_aceites uuid[] := '{}'::uuid[];
  v_pedidos uuid[] := '{}'::uuid[];
  v_pipeline uuid[] := '{}'::uuid[];
  v_atividades uuid[] := '{}'::uuid[];
  v_envios uuid[] := '{}'::uuid[];
  v_vendas uuid[] := '{}'::uuid[];
  v_solicitadas integer;
  v_encontradas integer;
  v_resumo jsonb;
begin
  select coalesce(array_agg(distinct x), '{}'::uuid[]), count(distinct x)
    into v_ops, v_solicitadas
  from unnest(coalesce(p_oportunidade_ids, '{}'::uuid[])) x;

  if v_solicitadas = 0 then
    raise exception 'Nenhuma oportunidade foi selecionada para arquivamento.';
  end if;

  select count(*) into v_encontradas
  from public.cti_oportunidades_registros
  where id = any(v_ops) and arquivado_em is null;

  if v_encontradas <> v_solicitadas then
    raise exception 'O conjunto ativo mudou desde a prévia. Atualize a prévia antes de arquivar.';
  end if;

  select coalesce(array_agg(id), '{}'::uuid[]) into v_itens
  from public.cti_oportunidade_itens_registros
  where oportunidade_id = any(v_ops) and arquivado_em is null;

  select coalesce(array_agg(id), '{}'::uuid[]) into v_propostas
  from public.cti_propostas_registros
  where arquivado_em is null
    and (oportunidade_id = any(v_ops) or item_oportunidade_id = any(v_itens));

  select coalesce(array_agg(id), '{}'::uuid[]) into v_aceites
  from public.cti_proposta_aceites_registros
  where arquivado_em is null and proposta_id = any(v_propostas);

  select coalesce(array_agg(id), '{}'::uuid[]) into v_pedidos
  from public.cti_pedidos_registros
  where arquivado_em is null
    and (proposta_id = any(v_propostas)
      or proposta_aceita_id = any(v_propostas)
      or item_oportunidade_id = any(v_itens)
      or aceite_id = any(v_aceites));

  select coalesce(array_agg(id), '{}'::uuid[]) into v_pipeline
  from public.cti_pipeline_registros
  where arquivado_em is null and oportunidade_id = any(v_ops);

  select coalesce(array_agg(id), '{}'::uuid[]) into v_atividades
  from public.cti_atividades_registros
  where arquivado_em is null
    and (oportunidade_id = any(v_ops) or proposta_id = any(v_propostas) or pedido_id = any(v_pedidos));

  select coalesce(array_agg(id), '{}'::uuid[]) into v_envios
  from public.cti_envios_carrier_registros
  where arquivado_em is null and (proposta_id = any(v_propostas) or pedido_id = any(v_pedidos));

  select coalesce(array_agg(id), '{}'::uuid[]) into v_vendas
  from public.vendas_registros
  where arquivado_em is null
    and (oportunidade_id = any(v_ops) or pedido_id = any(v_pedidos) or item_oportunidade_id = any(v_itens));

  insert into public.cti_oportunidades_arquivo_auditoria
    (oportunidade_id, acao, usuario_id, motivo, status_anterior, status_resultante, snapshot)
  select id, 'ARQUIVAR_HOMOLOGACAO', p_usuario_id, p_motivo, status, 'ARQUIVADO_TESTE', to_jsonb(o)
  from public.cti_oportunidades_registros o
  where id = any(v_ops) and arquivado_em is null;

  update public.cti_envios_carrier_registros set registro_teste=true, arquivado_em=v_agora, arquivado_por=p_usuario_id, motivo_arquivamento=p_motivo, lote_arquivamento_id=v_lote where id = any(v_envios);
  update public.cti_atividades_registros set registro_teste=true, arquivado_em=v_agora, arquivado_por=p_usuario_id, motivo_arquivamento=p_motivo, lote_arquivamento_id=v_lote where id = any(v_atividades);
  update public.vendas_registros set registro_teste=true, arquivado_em=v_agora, arquivado_por=p_usuario_id, motivo_arquivamento=p_motivo, lote_arquivamento_id=v_lote where id = any(v_vendas);
  update public.cti_pedidos_registros set registro_teste=true, arquivado_em=v_agora, arquivado_por=p_usuario_id, motivo_arquivamento=p_motivo, lote_arquivamento_id=v_lote where id = any(v_pedidos);
  update public.cti_proposta_aceites_registros set registro_teste=true, arquivado_em=v_agora, arquivado_por=p_usuario_id, motivo_arquivamento=p_motivo, lote_arquivamento_id=v_lote where id = any(v_aceites);
  update public.cti_propostas_registros set registro_teste=true, arquivado_em=v_agora, arquivado_por=p_usuario_id, motivo_arquivamento=p_motivo, lote_arquivamento_id=v_lote where id = any(v_propostas);
  update public.cti_pipeline_registros set registro_teste=true, arquivado_em=v_agora, arquivado_por=p_usuario_id, motivo_arquivamento=p_motivo, lote_arquivamento_id=v_lote where id = any(v_pipeline);
  update public.cti_oportunidade_itens_registros set registro_teste=true, arquivado_em=v_agora, arquivado_por=p_usuario_id, motivo_arquivamento=p_motivo, lote_arquivamento_id=v_lote where id = any(v_itens);
  update public.cti_oportunidades_registros
     set registro_teste=true,
         arquivado_em=v_agora,
         arquivado_por=p_usuario_id,
         motivo_arquivamento=p_motivo,
         lote_arquivamento_id=v_lote,
         status_antes_arquivamento=status,
         status='ARQUIVADO_TESTE',
         updated_at=v_agora
   where id = any(v_ops) and arquivado_em is null;

  v_resumo := jsonb_build_object(
    'oportunidades', cardinality(v_ops),
    'itens', cardinality(v_itens),
    'pipeline', cardinality(v_pipeline),
    'atividades', cardinality(v_atividades),
    'propostas', cardinality(v_propostas),
    'aceites', cardinality(v_aceites),
    'pedidos', cardinality(v_pedidos),
    'envios', cardinality(v_envios),
    'vendas', cardinality(v_vendas)
  );

  insert into public.cti_crm_homologacao_auditoria
    (lote_id, acao, usuario_id, motivo, oportunidade_ids, resumo)
  values (v_lote, 'ARQUIVAR_HOMOLOGACAO', p_usuario_id, p_motivo, v_ops, v_resumo);

  return jsonb_build_object('success', true, 'lote_id', v_lote, 'resumo', v_resumo);
end;
$$;

create or replace function public.cti_restaurar_homologacao_crm(
  p_lote_id uuid,
  p_usuario_id uuid
) returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_agora timestamptz := now();
  v_ops uuid[] := '{}'::uuid[];
  v_resumo jsonb;
begin
  select coalesce(oportunidade_ids, '{}'::uuid[]) into v_ops
  from public.cti_crm_homologacao_auditoria
  where lote_id=p_lote_id and acao='ARQUIVAR_HOMOLOGACAO' and revertido_em is null
  order by created_at desc limit 1;

  if cardinality(v_ops)=0 then
    raise exception 'Lote de homologação ativo não encontrado.';
  end if;

  insert into public.cti_oportunidades_arquivo_auditoria
    (oportunidade_id, acao, usuario_id, motivo, status_anterior, status_resultante, snapshot)
  select id, 'RESTAURAR_HOMOLOGACAO', p_usuario_id, 'Restauração administrativa do lote de homologação', status,
         coalesce(status_antes_arquivamento,'OPORTUNIDADE'), to_jsonb(o)
  from public.cti_oportunidades_registros o
  where lote_arquivamento_id=p_lote_id;

  v_resumo := jsonb_build_object(
    'oportunidades', (select count(*) from public.cti_oportunidades_registros where lote_arquivamento_id=p_lote_id),
    'itens', (select count(*) from public.cti_oportunidade_itens_registros where lote_arquivamento_id=p_lote_id),
    'pipeline', (select count(*) from public.cti_pipeline_registros where lote_arquivamento_id=p_lote_id),
    'atividades', (select count(*) from public.cti_atividades_registros where lote_arquivamento_id=p_lote_id),
    'propostas', (select count(*) from public.cti_propostas_registros where lote_arquivamento_id=p_lote_id),
    'aceites', (select count(*) from public.cti_proposta_aceites_registros where lote_arquivamento_id=p_lote_id),
    'pedidos', (select count(*) from public.cti_pedidos_registros where lote_arquivamento_id=p_lote_id),
    'envios', (select count(*) from public.cti_envios_carrier_registros where lote_arquivamento_id=p_lote_id),
    'vendas', (select count(*) from public.vendas_registros where lote_arquivamento_id=p_lote_id)
  );

  update public.cti_envios_carrier_registros set registro_teste=false, arquivado_em=null, arquivado_por=null, motivo_arquivamento=null, lote_arquivamento_id=null where lote_arquivamento_id=p_lote_id;
  update public.cti_atividades_registros set registro_teste=false, arquivado_em=null, arquivado_por=null, motivo_arquivamento=null, lote_arquivamento_id=null where lote_arquivamento_id=p_lote_id;
  update public.vendas_registros set registro_teste=false, arquivado_em=null, arquivado_por=null, motivo_arquivamento=null, lote_arquivamento_id=null where lote_arquivamento_id=p_lote_id;
  update public.cti_pedidos_registros set registro_teste=false, arquivado_em=null, arquivado_por=null, motivo_arquivamento=null, lote_arquivamento_id=null where lote_arquivamento_id=p_lote_id;
  update public.cti_proposta_aceites_registros set registro_teste=false, arquivado_em=null, arquivado_por=null, motivo_arquivamento=null, lote_arquivamento_id=null where lote_arquivamento_id=p_lote_id;
  update public.cti_propostas_registros set registro_teste=false, arquivado_em=null, arquivado_por=null, motivo_arquivamento=null, lote_arquivamento_id=null where lote_arquivamento_id=p_lote_id;
  update public.cti_pipeline_registros set registro_teste=false, arquivado_em=null, arquivado_por=null, motivo_arquivamento=null, lote_arquivamento_id=null where lote_arquivamento_id=p_lote_id;
  update public.cti_oportunidade_itens_registros set registro_teste=false, arquivado_em=null, arquivado_por=null, motivo_arquivamento=null, lote_arquivamento_id=null where lote_arquivamento_id=p_lote_id;
  update public.cti_oportunidades_registros
     set registro_teste=false,
         arquivado_em=null,
         arquivado_por=null,
         motivo_arquivamento=null,
         lote_arquivamento_id=null,
         status=coalesce(status_antes_arquivamento,'OPORTUNIDADE'),
         status_antes_arquivamento=null,
         updated_at=v_agora
   where lote_arquivamento_id=p_lote_id;

  update public.cti_crm_homologacao_auditoria
     set revertido_em=v_agora, revertido_por=p_usuario_id
   where lote_id=p_lote_id and acao='ARQUIVAR_HOMOLOGACAO' and revertido_em is null;

  insert into public.cti_crm_homologacao_auditoria
    (lote_id, acao, usuario_id, motivo, oportunidade_ids, resumo)
  values (p_lote_id, 'RESTAURAR_HOMOLOGACAO', p_usuario_id, 'Restauração administrativa', v_ops, v_resumo);

  return jsonb_build_object('success', true, 'lote_id', p_lote_id, 'resumo', v_resumo);
end;
$$;

grant execute on function public.cti_arquivar_homologacao_crm(uuid[],uuid,text) to service_role;
grant execute on function public.cti_restaurar_homologacao_crm(uuid,uuid) to service_role;

commit;
