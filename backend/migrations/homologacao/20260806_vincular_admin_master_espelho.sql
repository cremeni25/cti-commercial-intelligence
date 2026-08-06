begin;

-- Executar somente após criar, no Auth do projeto espelho, o usuário ADMIN_MASTER
-- com o mesmo e-mail do registro operacional copiado.
do $$
declare
  v_email constant text := 'anderson@cremeni.com.br';
  v_auth_id uuid;
  v_cti_id uuid;
begin
  select id
    into strict v_auth_id
  from auth.users
  where lower(email) = lower(v_email);

  select id
    into strict v_cti_id
  from public.cti_users
  where lower(trim(email)) = lower(v_email)
    and upper(coalesce(tipo_usuario, '')) = 'ADMIN_MASTER';

  update public.cti_users
  set auth_id = v_auth_id,
      ativo = true,
      status_acesso = coalesce(status_acesso, 'ATIVO'),
      acesso_portal = true,
      acesso_crm = true,
      primeiro_acesso_pendente = false,
      cadastro_completo = true,
      updated_at = now()
  where id = v_cti_id;

  if not found then
    raise exception 'Falha ao vincular ADMIN_MASTER no espelho.';
  end if;
end $$;

commit;
