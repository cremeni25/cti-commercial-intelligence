-- CTI P0 — elimina coluna física legada implementador da base operacional.
-- Entradas externas podem ter aliases de origem, porém toda persistência interna é canônica.

do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'cti_anfir'
      and column_name = 'implementador'
  ) and not exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'cti_anfir'
      and column_name = 'implementadora'
  ) then
    alter table public.cti_anfir rename column implementador to implementadora;
  end if;
end $$;

comment on column public.cti_anfir.implementadora is
  'Implementadora canônica CTI. Não usar implementador em novas persistências.';
