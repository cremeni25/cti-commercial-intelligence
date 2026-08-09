alter table public.cti_pedidos
  add column if not exists numero_serie_nf text,
  add column if not exists numero_serie_instalado text;

create index if not exists idx_cti_pedidos_numero_serie_nf on public.cti_pedidos(numero_serie_nf);
create index if not exists idx_cti_pedidos_numero_serie_instalado on public.cti_pedidos(numero_serie_instalado);
