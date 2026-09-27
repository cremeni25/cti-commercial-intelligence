create or replace function public.cti_sync_encerramento_oportunidade()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_motivo_tipo text;
  v_descricao text;
  v_motivo_real text;
  v_status_final text;
begin
  if upper(coalesce(new.tipo,'')) <> 'ENCERRAMENTO' then return new; end if;
  v_motivo_tipo := upper(coalesce(new.payload->>'motivo_tipo',''));
  v_descricao := nullif(trim(coalesce(new.payload->>'motivo_descricao','')), '');
  v_motivo_real := v_motivo_tipo;
  if v_motivo_tipo = 'OUTRO' and v_descricao ~ '^\[[A-Z0-9_]+\]' then
    v_motivo_real := substring(v_descricao from '^\[([A-Z0-9_]+)\]');
    v_descricao := nullif(trim(regexp_replace(v_descricao, '^\[[A-Z0-9_]+\]\s*[-–—:]?\s*', '')), '');
  end if;
  v_status_final := upper(coalesce(new.payload->>'status_final','PERDIDO'));
  if v_motivo_real = 'VENDA_CONCLUIDA' then v_status_final := 'GANHO';
  elsif v_motivo_real in ('COMPRA_INDIRETA','PROJETO_ADIADO','SEM_CONTINUIDADE','OUTRO') then v_status_final := 'ENCERRADO'; end if;
  update public.cti_oportunidades_registros set status=v_status_final,data_fechamento_real=coalesce(data_fechamento_real,new.created_at::timestamp),motivo_encerramento=nullif(v_motivo_real,''),observacao_encerramento=v_descricao,encerrado_por=new.usuario_id,updated_at=new.created_at::timestamp where id=new.oportunidade_id;
  update public.cti_pipeline set etapa=v_status_final where id=(select id from public.cti_pipeline where oportunidade_id=new.oportunidade_id order by created_at desc nulls last limit 1);
  return new;
end;
$$;

create or replace function public.cti_encerrar_negociacao(p_oportunidade_id uuid,p_usuario_id uuid,p_motivo text,p_observacao text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_opp public.cti_oportunidades_registros%rowtype;
  v_usuario record;
  v_motivo text := upper(trim(coalesce(p_motivo,'')));
  v_obs text := trim(coalesce(p_observacao,''));
  v_status_final text;
  v_agora timestamptz := now();
  v_ids uuid[];
begin
  select id,nome,email,tipo_usuario into v_usuario from public.cti_users where id=p_usuario_id limit 1;
  if v_usuario.id is null then raise exception 'Usuário não reconhecido.'; end if;
  select * into v_opp from public.cti_oportunidades_registros where id=p_oportunidade_id and arquivado_em is null;
  if v_opp.id is null then raise exception 'Negociação não encontrada.'; end if;
  if upper(coalesce(v_usuario.tipo_usuario,'')) <> 'ADMIN_MASTER' and v_opp.responsavel_id is distinct from p_usuario_id then raise exception 'Você só pode encerrar negociações sob sua responsabilidade.'; end if;
  if v_motivo not in ('VENDA_CONCLUIDA','PERDA_CONCORRENCIA','COMPRA_INDIRETA','DESISTENCIA_CLIENTE','SEM_CONTINUIDADE','SOLUCAO_GARANTIA_FABRICANTE','PROJETO_ADIADO','PRECO_CONDICAO_COMERCIAL','PRODUTO_INADEQUADO_INDISPONIVEL','OUTRO') then raise exception 'Motivo de encerramento inválido.'; end if;
  if length(v_obs) < 5 then raise exception 'Descreva o motivo do encerramento com pelo menos 5 caracteres.'; end if;
  v_status_final := case when v_motivo='VENDA_CONCLUIDA' then 'GANHO' when v_motivo in ('COMPRA_INDIRETA','PROJETO_ADIADO','SEM_CONTINUIDADE','OUTRO') then 'ENCERRADO' else 'PERDIDO' end;
  update public.cti_oportunidades_registros set status=v_status_final,data_fechamento_real=v_agora::timestamp,motivo_encerramento=v_motivo,observacao_encerramento=v_obs,encerrado_por=p_usuario_id,updated_at=v_agora::timestamp where id=p_oportunidade_id;
  select array_agg(id) into v_ids from public.cti_atividades_registros where oportunidade_id=p_oportunidade_id and upper(coalesce(status,''))='PENDENTE' and arquivado_em is null;
  if v_ids is not null then update public.cti_atividades_registros set status='CANCELADA',updated_at=v_agora where id=any(v_ids); end if;
  insert into public.cti_pipeline(oportunidade_id,etapa,usuario_id,observacao,created_at) values(p_oportunidade_id,v_status_final,p_usuario_id,v_obs,v_agora::timestamp);
  insert into public.cti_oportunidade_historico(oportunidade_id,tipo,descricao,usuario_id,payload,created_at) values(p_oportunidade_id,'ENCERRAMENTO','Processo comercial encerrado e preservado no histórico do cliente.',p_usuario_id,jsonb_build_object('motivo_tipo',v_motivo,'motivo_descricao',v_obs,'status_anterior',v_opp.status,'status_final',v_status_final,'encerrado_em',v_agora),v_agora);
  return (select to_jsonb(o) from public.cti_oportunidades o where o.id=p_oportunidade_id);
end;
$$;

grant execute on function public.cti_encerrar_negociacao(uuid,uuid,text,text) to authenticated, service_role;
