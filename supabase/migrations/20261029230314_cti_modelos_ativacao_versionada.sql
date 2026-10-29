-- A troca de versão e sua auditoria confirmam juntas; documentos emitidos não são alterados.
create or replace function public.cti_ativar_modelo_proposta(p_modelo_id uuid, p_usuario_id uuid, p_sha256 text)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare alvo public.cti_modelos_proposta; equipamento_alvo text;
begin
  if not exists(select 1 from public.cti_users where id=p_usuario_id and ativo=true and tipo_usuario='ADMIN_MASTER' and auth_id is not null) then
    raise exception 'Ativação exclusiva do ADMIN_MASTER ativo' using errcode='42501';
  end if;
  select equipamento into equipamento_alvo from public.cti_modelos_proposta where id=p_modelo_id;
  if equipamento_alvo is null then raise exception 'Modelo não encontrado' using errcode='P0002'; end if;
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('cti:modelo:' || equipamento_alvo,0));
  select * into strict alvo from public.cti_modelos_proposta where id=p_modelo_id for update;
  if alvo.homologado_em is null or alvo.arquivo_template_storage is null or alvo.arquivo_template_hash_sha256 is distinct from p_sha256 then
    raise exception 'Modelo não homologado ou arquivo alterado; confira novamente' using errcode='55000';
  end if;
  if alvo.ativo and not exists(select 1 from public.cti_modelos_proposta where equipamento=equipamento_alvo and ativo and id<>alvo.id) then
    return to_jsonb(alvo);
  end if;
  insert into public.cti_modelos_proposta_auditoria(modelo_proposta_id,operacao,versao,arquivo_template_storage,arquivo_template_nome_original,arquivo_template_hash_sha256,conteudo_template,justificativa)
    select id,'DESATIVACAO',versao,arquivo_template_storage,arquivo_template_nome_original,arquivo_template_hash_sha256,conteudo_template,
      'Substituição por nova versão homologada; Master ' || p_usuario_id::text
    from public.cti_modelos_proposta where equipamento=equipamento_alvo and ativo and id<>alvo.id;
  update public.cti_modelos_proposta set ativo=false,updated_at=now() where equipamento=equipamento_alvo and ativo and id<>alvo.id;
  update public.cti_modelos_proposta set ativo=true,updated_at=now() where id=alvo.id returning * into alvo;
  insert into public.cti_modelos_proposta_auditoria(modelo_proposta_id,operacao,versao,arquivo_template_storage,arquivo_template_nome_original,arquivo_template_hash_sha256,conteudo_template,justificativa)
    values(alvo.id,'ATIVACAO',alvo.versao,alvo.arquivo_template_storage,alvo.arquivo_template_nome_original,alvo.arquivo_template_hash_sha256,alvo.conteudo_template,
      'Versão integral homologada ativada pelo Master ' || p_usuario_id::text);
  return to_jsonb(alvo);
end $$;
revoke all on function public.cti_ativar_modelo_proposta(uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.cti_ativar_modelo_proposta(uuid,uuid,text) to service_role;
