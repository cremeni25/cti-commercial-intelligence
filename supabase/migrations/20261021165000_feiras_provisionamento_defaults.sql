-- Preserve required CTI fields when populating complete records from JSON.
begin;
create or replace function public.cti_feira_provisionar(p_user_id uuid, p_perfil jsonb, p_permissoes jsonb,
  p_autorizada_id uuid, p_papel text)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare r public.cti_users; perms jsonb; externo boolean;
begin
  externo=p_papel in ('PROFISSIONAL','GESTOR');
  if p_papel is null or p_papel not in ('INTERNO','PROFISSIONAL','GESTOR') then raise exception 'Papel inválido' using errcode='22023'; end if;
  if externo then
    perform 1 from public.cti_feira_autorizadas where id=p_autorizada_id and ativa for share;
    if not found then raise exception 'Autorizada inativa ou inexistente' using errcode='23503'; end if;
    p_perfil=p_perfil || jsonb_build_object('tipo_usuario',case when p_papel='GESTOR' then 'GESTOR_AUTORIZADO_CARRIER' else 'AUTORIZADO_CARRIER' end);
    -- Strip every commercial/admin capability even if a caller sends them.
    select jsonb_object_agg(key,false) into perms from jsonb_each(p_permissoes) where key not in ('user_id','updated_at');
    p_permissoes=coalesce(perms,'{}') || jsonb_build_object('acesso_crm',true,'acesso_portal',false,'feiras_eventos',coalesce((p_permissoes->>'feiras_eventos')::boolean,true));
  end if;
  if p_user_id is null then
    r=jsonb_populate_record(null::public.cti_users,
      jsonb_build_object('ativo',true,'primeiro_acesso_pendente',true,'cadastro_completo',false,'ddds','[]'::jsonb,
        'status_acesso','PRIMEIRO_ACESSO_PENDENTE') || p_perfil ||
      jsonb_build_object('id',gen_random_uuid(),'created_at',now(),'updated_at',now()));
    insert into public.cti_users select r.* returning * into r;
  else
    select * into strict r from public.cti_users where id=p_user_id for update;
    -- An external account cannot be silently promoted by an omitted form field.
    if r.tipo_usuario in ('AUTORIZADO_CARRIER','GESTOR_AUTORIZADO_CARRIER') and not externo then
      raise exception 'Mudança para interno exige governança específica' using errcode='42501';
    end if;
    if r.tipo_usuario='ADMIN_MASTER' and externo then raise exception 'Master protegido' using errcode='42501'; end if;
    r=jsonb_populate_record(r,p_perfil - 'id' - 'auth_id' - 'email');
    update public.cti_users set nome=r.nome,empresa=r.empresa,cargo=r.cargo,funcao=r.funcao,
      territorio=r.territorio,ddds=r.ddds,gestor_responsavel=r.gestor_responsavel,tipo_usuario=r.tipo_usuario,updated_at=now()
      where id=r.id;
  end if;
  delete from public.cti_user_permissions where user_id=r.id;
  insert into public.cti_user_permissions select (jsonb_populate_record(null::public.cti_user_permissions,
    jsonb_build_object(
      'acesso_portal',false,'acesso_crm',false,'dashboard_executivo',false,
      'clientes_visualizar',false,'clientes_editar',false,'oportunidades_visualizar',false,
      'oportunidades_editar',false,'propostas_visualizar',false,'propostas_emitir',false,
      'pedidos_visualizar',false,'pedidos_converter',false,'pedidos_enviar',false,
      'financeiro_visualizar',false,'usuarios_administrar',false,'configuracoes_administrar',false,
      'acesso_total',false,'feiras_eventos',false) ||
    p_permissoes || jsonb_build_object('user_id',r.id,'created_at',now(),'updated_at',now()))).*;
  if externo then
    insert into public.cti_feira_profissionais(user_id,autorizada_id,papel,ativo) values(r.id,p_autorizada_id,p_papel,true)
      on conflict(user_id) do update set autorizada_id=excluded.autorizada_id,papel=excluded.papel,ativo=true;
  end if;
  return to_jsonb(r) || jsonb_build_object('permissoes',p_permissoes,'autorizada_id',p_autorizada_id,'papel_feira',p_papel);
end $$;
revoke all on function public.cti_feira_provisionar(uuid,jsonb,jsonb,uuid,text) from public,anon,authenticated;
grant execute on function public.cti_feira_provisionar(uuid,jsonb,jsonb,uuid,text) to service_role;
create or replace function public.cti_feira_registrar(p_user_id uuid, p_payload jsonb, p_itens jsonb)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare
  anterior public.cti_feira_atendimentos;
  novo_id uuid;
  perfil public.cti_users;
  empresa_id uuid;
  conteudo jsonb;
begin
  select * into strict perfil from public.cti_users where id=p_user_id and ativo=true for share;
  if perfil.tipo_usuario in ('AUTORIZADO_CARRIER','GESTOR_AUTORIZADO_CARRIER') then
    select v.autorizada_id into empresa_id from public.cti_feira_profissionais v
      join public.cti_feira_autorizadas a on a.id=v.autorizada_id
      join public.cti_user_permissions p on p.user_id=v.user_id
      where v.user_id=p_user_id and v.ativo and a.ativa and p.feiras_eventos for share of v,a,p;
    if empresa_id is null then raise exception 'Vínculo ou permissão revogados' using errcode='42501'; end if;
  elsif coalesce(perfil.tipo_usuario,'') not in ('ADMIN_MASTER','DIRETOR_VIENA_SP','ADMIN_COMERCIAL_VIENA_SP') and
    not exists (select 1 from public.cti_user_permissions where user_id=p_user_id and (feiras_eventos or acesso_total)) then
    raise exception 'Sem permissão' using errcode='42501';
  end if;
  if nullif(p_payload->>'client_request_id','') is null then
    raise exception 'Chave de sincronização obrigatória' using errcode='22023';
  end if;
  -- Serialize the same author/key before checking a receipt: no partial success.
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_user_id::text || ':' || (p_payload->>'client_request_id'),0));
  conteudo = jsonb_build_object('atendimento',p_payload - 'autorizada_id' - 'criado_por','itens',p_itens);
  select * into anterior from public.cti_feira_atendimentos
    where criado_por=p_user_id::text and client_request_id=p_payload->>'client_request_id';
  if found then
    if anterior.autorizada_id is distinct from empresa_id then
      raise exception 'Vínculo institucional alterado' using errcode='42501';
    end if;
    if anterior.request_payload is distinct from conteudo then
      raise exception 'Chave já utilizada com conteúdo diferente' using errcode='23505';
    end if;
    return jsonb_build_object('id',anterior.id,'status','REGISTRADO','reutilizado',true);
  end if;
  if jsonb_array_length(p_itens)=0 then raise exception 'Informe equipamentos' using errcode='22023'; end if;
  novo_id=gen_random_uuid();
  insert into public.cti_feira_atendimentos
    (id,feira_id,empresa,cnpj,visitante,contato,email,cidade,uf,regiao,autorizado_destino,interesse,
     observacoes,moeda,valor_referencia,criado_por,autorizada_id,client_request_id,request_payload)
  values (novo_id,(p_payload->>'feira_id')::uuid,p_payload->>'empresa',p_payload->>'cnpj',p_payload->>'visitante',
    p_payload->>'contato',p_payload->>'email',p_payload->>'cidade',p_payload->>'uf',p_payload->>'regiao',
    p_payload->>'autorizado_destino',p_payload->>'interesse',p_payload->>'observacoes',p_payload->>'moeda',
    (p_payload->>'valor_referencia')::numeric,p_user_id::text,empresa_id,p_payload->>'client_request_id',conteudo);
  insert into public.cti_feira_itens
    (atendimento_id,codigo_produto,linha_produto,nome_produto,quantidade,lancamento_feira,descricao_lancamento)
    select novo_id,x.codigo_produto,x.linha_produto,x.nome_produto,x.quantidade,x.lancamento_feira,x.descricao_lancamento
    from jsonb_to_recordset(p_itens) x(codigo_produto text,linha_produto text,nome_produto text,
      quantidade integer,lancamento_feira boolean,descricao_lancamento text);
  return jsonb_build_object('id',novo_id,'status','REGISTRADO','reutilizado',false);
end $$;
revoke all on function public.cti_feira_registrar(uuid,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.cti_feira_registrar(uuid,jsonb,jsonb) to service_role;

commit;
