begin;

create or replace function public.cti_registrar_teste_campo_automatico()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  campanha_detectada text;
begin
  if upper(coalesce(new.descricao, '')) not like '%TESTE DE CAMPO%'
     and upper(coalesce(new.titulo, '')) not like '%TESTE DE CAMPO%' then
    return new;
  end if;

  campanha_detectada := coalesce(
    nullif(substring(upper(coalesce(new.descricao, '')) from '\[CAMPANHA:[[:space:]]*([^]]+)\]'), ''),
    'TESTE_CAMPO_GERAL'
  );
  campanha_detectada := regexp_replace(trim(campanha_detectada), '[^A-Z0-9_-]+', '_', 'g');

  insert into public.cti_testes_campo (
    campanha,
    oportunidade_id,
    cliente_id,
    criado_por,
    observacao,
    status
  ) values (
    campanha_detectada,
    new.id,
    new.cliente_id,
    new.responsavel_id,
    'TESTE DE CAMPO',
    'ATIVO'
  )
  on conflict (campanha, oportunidade_id) do nothing;

  return new;
end;
$$;

drop trigger if exists cti_oportunidades_registrar_teste_campo on public.cti_oportunidades;
create trigger cti_oportunidades_registrar_teste_campo
after insert or update of titulo, descricao
on public.cti_oportunidades
for each row
execute function public.cti_registrar_teste_campo_automatico();

commit;
