alter table public.cti_cliente_cadastro_financeiro_carrier
  add column if not exists ciclo_numero integer,
  add column if not exists ciclo_atual boolean not null default true,
  add column if not exists ciclo_anterior_id uuid,
  add column if not exists encerrado_em timestamptz;

update public.cti_cliente_cadastro_financeiro_carrier
set ciclo_numero = 1
where ciclo_numero is null;

alter table public.cti_cliente_cadastro_financeiro_carrier
  alter column ciclo_numero set not null,
  alter column ciclo_numero set default 1;

do $$ begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'cti_cliente_cadastro_fin_ciclo_anterior_fk'
  ) then
    alter table public.cti_cliente_cadastro_financeiro_carrier
      add constraint cti_cliente_cadastro_fin_ciclo_anterior_fk
      foreign key (ciclo_anterior_id)
      references public.cti_cliente_cadastro_financeiro_carrier(id)
      on delete set null;
  end if;
end $$;

drop index if exists public.uq_cti_cliente_cadastro_fin_ativo;
create unique index if not exists uq_cti_cliente_cadastro_fin_ciclo_atual
  on public.cti_cliente_cadastro_financeiro_carrier(cliente_id)
  where ciclo_atual = true;

create unique index if not exists uq_cti_cliente_cadastro_fin_ciclo_numero
  on public.cti_cliente_cadastro_financeiro_carrier(cliente_id, ciclo_numero);

create index if not exists idx_cti_cliente_cadastro_fin_historico
  on public.cti_cliente_cadastro_financeiro_carrier(cliente_id, ciclo_numero desc);

alter table public.cti_cliente_documentos_financeiros
  add column if not exists ciclo_financeiro_id uuid;

do $$ begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'cti_cliente_doc_fin_ciclo_fk'
  ) then
    alter table public.cti_cliente_documentos_financeiros
      add constraint cti_cliente_doc_fin_ciclo_fk
      foreign key (ciclo_financeiro_id)
      references public.cti_cliente_cadastro_financeiro_carrier(id)
      on delete set null;
  end if;
end $$;

update public.cti_cliente_documentos_financeiros d
set ciclo_financeiro_id = c.id
from public.cti_cliente_cadastro_financeiro_carrier c
where d.ciclo_financeiro_id is null
  and c.cliente_id = d.cliente_id
  and c.ciclo_atual = true;

create index if not exists idx_cti_cliente_doc_fin_ciclo
  on public.cti_cliente_documentos_financeiros(ciclo_financeiro_id, created_at desc);
