alter table public.cti_atividades
  add column if not exists proposta_id uuid,
  add column if not exists pedido_id uuid,
  add column if not exists titulo text,
  add column if not exists data date,
  add column if not exists horario time without time zone,
  add column if not exists updated_at timestamp with time zone,
  add column if not exists concluida_em timestamp with time zone;

create index if not exists idx_cti_atividades_proposta_id on public.cti_atividades(proposta_id);
create index if not exists idx_cti_atividades_pedido_id on public.cti_atividades(pedido_id);
create index if not exists idx_cti_atividades_data on public.cti_atividades(data);

update public.cti_atividades
set data = data_atividade::date,
    horario = data_atividade::time
where data_atividade is not null
  and data is null;
