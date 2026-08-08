begin;

alter table public.vendas
  add column if not exists pedido_id uuid references public.cti_pedidos(id) on delete restrict,
  add column if not exists oportunidade_id uuid references public.cti_oportunidades(id) on delete restrict,
  add column if not exists item_oportunidade_id uuid references public.cti_oportunidade_itens(id) on delete restrict,
  add column if not exists equipamento_codigo text references public.cti_catalogo_equipamentos(codigo) on delete restrict,
  add column if not exists implementadora_id uuid references public.implementadoras(id) on delete restrict;

-- O modelo legado de vendas exigia equipamento_id/implementador_id de tabelas antigas.
-- O CRM atual trabalha com cti_catalogo_equipamentos e pedido/oportunidade como fontes canônicas.
alter table public.vendas
  alter column equipamento_id drop not null,
  alter column implementador_id drop not null;

create unique index if not exists vendas_pedido_unique
  on public.vendas(pedido_id)
  where pedido_id is not null;

create index if not exists vendas_equipamento_codigo_idx
  on public.vendas(equipamento_codigo)
  where equipamento_codigo is not null;

create index if not exists vendas_implementadora_id_idx
  on public.vendas(implementadora_id)
  where implementadora_id is not null;

commit;
