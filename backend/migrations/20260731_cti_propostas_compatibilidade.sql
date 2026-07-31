begin;

alter table public.cti_propostas
  add column if not exists condicoes text,
  add column if not exists produtos text,
  add column if not exists equipamentos text;

commit;
