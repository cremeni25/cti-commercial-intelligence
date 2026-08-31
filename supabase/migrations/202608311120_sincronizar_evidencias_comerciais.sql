-- Mantém a camada ANFIR de evidências atualizada para novas cargas.
-- CRM, Funil e Vendas são views no esquema atual e são lidos dinamicamente pelo motor transversal.
-- Nenhum gatilho altera a tabela de origem.

create or replace function public.cti_resolver_cliente_anfir(p_cnpj text,p_nome text,p_cidade text)
returns table(cliente_id uuid, metodo text, confianca numeric)
language plpgsql stable as $$
declare
  v_doc text := nullif(regexp_replace(coalesce(p_cnpj,''),'\D','','g'),'');
  v_nome text := upper(trim(regexp_replace(translate(coalesce(p_nome,''),'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç','AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'),'\s+',' ','g')));
  v_cidade text := upper(trim(regexp_replace(translate(coalesce(p_cidade,''),'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç','AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'),'\s+',' ','g')));
  v_ids uuid[];
begin
  if v_doc is not null then
    select array_agg(id) into v_ids from public.clientes where regexp_replace(coalesce(cnpj,''),'\D','','g')=v_doc;
    if coalesce(array_length(v_ids,1),0)=1 then
      return query select v_ids[1],'CNPJ_EXATO'::text,1::numeric; return;
    end if;
  end if;
  if v_nome<>'' and v_cidade<>'' then
    select array_agg(id) into v_ids from public.clientes
    where upper(trim(regexp_replace(translate(coalesce(nome,''),'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç','AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'),'\s+',' ','g')))=v_nome
      and upper(trim(regexp_replace(translate(coalesce(cidade,''),'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç','AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'),'\s+',' ','g')))=v_cidade;
    if coalesce(array_length(v_ids,1),0)=1 then
      return query select v_ids[1],'NOME_CIDADE_EXATOS_UNICOS'::text,0.90::numeric; return;
    end if;
  end if;
  return query select null::uuid,'SEM_RECONCILIACAO'::text,0::numeric;
end $$;

create or replace function public.cti_sync_anfir_evidencia()
returns trigger language plpgsql security definer set search_path=public as $$
declare r record;
begin
  if coalesce(new.ativo,true)=false then
    delete from public.cti_evidencias_comerciais where fonte='ANFIR' and fonte_registro_id=new.id::text and evento='RESULTADO_MERCADO';
    return new;
  end if;
  select * into r from public.cti_resolver_cliente_anfir(new.cnpj,new.cliente,new.cidade) limit 1;
  insert into public.cti_evidencias_comerciais
    (fonte,fonte_registro_id,cliente_id,cnpj_normalizado,cliente_nome,temporalidade,evento,estado_comercial,data_evento,segmento,equipamento,quantidade,valor,metodo_reconciliacao,confianca,metadata)
  values ('ANFIR',new.id::text,r.cliente_id,nullif(regexp_replace(coalesce(new.cnpj,''),'\D','','g'),''),new.cliente,'PASSADO_CONFIRMADO','RESULTADO_MERCADO',upper(coalesce(nullif(trim(new.status),''),nullif(trim(new.categoria),''),'NAO_CLASSIFICADO')),case when new.ano is not null and new.mes between 1 and 12 then make_date(new.ano,new.mes,1) else null end,new.linha,coalesce(new.equipamento,new.modelo),coalesce(new.quantidade,1),new.valor,r.metodo,r.confianca,jsonb_build_object('arquivo_origem',new.arquivo_origem,'categoria_fonte',new.categoria,'status_fonte',new.status,'chassi',new.chassi,'placa',new.placa))
  on conflict (fonte,fonte_registro_id,evento) do update set cliente_id=excluded.cliente_id,cnpj_normalizado=excluded.cnpj_normalizado,cliente_nome=excluded.cliente_nome,temporalidade=excluded.temporalidade,estado_comercial=excluded.estado_comercial,data_evento=excluded.data_evento,segmento=excluded.segmento,equipamento=excluded.equipamento,quantidade=excluded.quantidade,valor=excluded.valor,metodo_reconciliacao=excluded.metodo_reconciliacao,confianca=excluded.confianca,metadata=excluded.metadata,updated_at=now();
  return new;
end $$;

drop trigger if exists trg_cti_sync_anfir_evidencia on public.cti_anfir;
create trigger trg_cti_sync_anfir_evidencia after insert or update on public.cti_anfir for each row execute function public.cti_sync_anfir_evidencia();
