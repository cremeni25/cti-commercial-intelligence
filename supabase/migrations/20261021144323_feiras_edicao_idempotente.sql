begin;
alter table public.cti_feira_atendimentos add column if not exists versao integer not null default 0;
create table if not exists public.cti_feira_edicoes (
  user_id uuid not null references public.cti_users(id),
  client_request_id text not null,
  atendimento_id uuid not null references public.cti_feira_atendimentos(id) on delete cascade,
  conteudo jsonb not null,
  recibo jsonb not null,
  criado_em timestamptz not null default now(),
  primary key(user_id, client_request_id)
);
alter table public.cti_feira_edicoes enable row level security;
revoke all on public.cti_feira_edicoes from anon, authenticated;
grant all on public.cti_feira_edicoes to service_role;

create or replace function public.cti_feira_editar(p_user_id uuid, p_atendimento_id uuid, p_payload jsonb, p_itens jsonb)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare
  perfil public.cti_users;
  registro public.cti_feira_atendimentos;
  anterior public.cti_feira_edicoes;
  empresa_id uuid;
  global_permitido boolean := false;
  conteudo jsonb;
  recibo jsonb;
begin
  select * into strict perfil from public.cti_users where id=p_user_id and ativo=true for share;
  if perfil.tipo_usuario in ('AUTORIZADO_CARRIER','GESTOR_AUTORIZADO_CARRIER') then
    select v.autorizada_id into empresa_id from public.cti_feira_profissionais v
      join public.cti_feira_autorizadas a on a.id=v.autorizada_id
      join public.cti_user_permissions p on p.user_id=v.user_id
      where v.user_id=p_user_id and v.ativo and a.ativa and p.feiras_eventos for share of v,a,p;
    if empresa_id is null then raise exception 'Vínculo ou permissão revogados' using errcode='42501'; end if;
    if empresa_id::text is distinct from p_payload->>'autorizada_id' then
      raise exception 'Vínculo institucional alterado' using errcode='42501';
    end if;
  else
    global_permitido := coalesce(perfil.tipo_usuario in ('ADMIN_MASTER','DIRETOR_VIENA_SP','ADMIN_COMERCIAL_VIENA_SP'),false) or
      exists(select 1 from public.cti_user_permissions where user_id=p_user_id and acesso_total);
    if not global_permitido and not exists(select 1 from public.cti_user_permissions where user_id=p_user_id and feiras_eventos) then
      raise exception 'Sem permissão' using errcode='42501';
    end if;
  end if;
  if nullif(p_payload->>'client_request_id','') is null or coalesce((p_payload->>'versao_esperada')::integer,-1)<0 then
    raise exception 'Chave e versão obrigatórias' using errcode='22023';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('edicao:' || p_user_id::text || ':' || (p_payload->>'client_request_id'),0));
  select * into registro from public.cti_feira_atendimentos
    where id=p_atendimento_id and feira_id=(p_payload->>'feira_id')::uuid for update;
  if not found or (not global_permitido and registro.criado_por is distinct from p_user_id::text) or
    (empresa_id is not null and registro.autorizada_id is distinct from empresa_id) then
    raise exception 'Atendimento não localizado' using errcode='P0002';
  end if;
  conteudo := jsonb_build_object('id',p_atendimento_id,'payload',p_payload,'itens',p_itens);
  select * into anterior from public.cti_feira_edicoes where user_id=p_user_id and client_request_id=p_payload->>'client_request_id';
  if found then
    if anterior.conteudo is distinct from conteudo then raise exception 'Chave de edição reutilizada com conteúdo diferente' using errcode='23505'; end if;
    return anterior.recibo || jsonb_build_object('reutilizado',true);
  end if;
  if registro.oportunidade_id is not null or registro.status='CONVERTIDO' then
    raise exception 'Atendimento convertido' using errcode='55000';
  end if;
  if registro.versao <> (p_payload->>'versao_esperada')::integer then
    raise exception 'Atendimento alterado por outra operação' using errcode='40001';
  end if;
  if jsonb_array_length(p_itens)=0 then raise exception 'Informe equipamentos' using errcode='22023'; end if;
  update public.cti_feira_atendimentos set
    empresa=p_payload->>'empresa',cnpj=p_payload->>'cnpj',visitante=p_payload->>'visitante',
    contato=p_payload->>'contato',email=p_payload->>'email',cidade=p_payload->>'cidade',uf=p_payload->>'uf',
    regiao=p_payload->>'regiao',autorizado_destino=p_payload->>'autorizado_destino',interesse=p_payload->>'interesse',
    observacoes=p_payload->>'observacoes',moeda=p_payload->>'moeda',valor_referencia=(p_payload->>'valor_referencia')::numeric,
    versao=versao+1 where id=p_atendimento_id;
  delete from public.cti_feira_itens where atendimento_id=p_atendimento_id;
  insert into public.cti_feira_itens
    (atendimento_id,codigo_produto,linha_produto,nome_produto,quantidade,lancamento_feira,descricao_lancamento)
    select p_atendimento_id,x.codigo_produto,x.linha_produto,x.nome_produto,x.quantidade,x.lancamento_feira,x.descricao_lancamento
    from jsonb_to_recordset(p_itens) x(codigo_produto text,linha_produto text,nome_produto text,
      quantidade integer,lancamento_feira boolean,descricao_lancamento text);
  recibo := jsonb_build_object('id',p_atendimento_id,'versao',registro.versao+1,'reutilizado',false);
  insert into public.cti_feira_edicoes(user_id,client_request_id,atendimento_id,conteudo,recibo)
    values(p_user_id,p_payload->>'client_request_id',p_atendimento_id,conteudo,recibo);
  return recibo;
end $$;
revoke all on function public.cti_feira_editar(uuid,uuid,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.cti_feira_editar(uuid,uuid,jsonb,jsonb) to service_role;
commit;
