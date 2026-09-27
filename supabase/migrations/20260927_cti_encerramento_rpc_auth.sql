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
  select id,auth_id,nome,email,tipo_usuario into v_usuario from public.cti_users where id=p_usuario_id and coalesce(ativo,true)=true limit 1;
  if v_usuario.id is null then raise exception 'Usuário não reconhecido.'; end if;
  if auth.role() = 'authenticated' and v_usuario.auth_id is distinct from auth.uid() then raise exception 'Sessão não corresponde ao usuário informado.'; end if;
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
revoke all on function public.cti_encerrar_negociacao(uuid,uuid,text,text) from public, anon;
grant execute on function public.cti_encerrar_negociacao(uuid,uuid,text,text) to authenticated, service_role;
