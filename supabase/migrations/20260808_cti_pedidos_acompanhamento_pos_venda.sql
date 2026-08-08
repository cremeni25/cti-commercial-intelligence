alter table public.cti_pedidos
  add column if not exists status_ciclo text default 'PEDIDO',
  add column if not exists carrier_confirmado_em timestamptz,
  add column if not exists faturado_em timestamptz,
  add column if not exists numero_nf text,
  add column if not exists entregue_em timestamptz,
  add column if not exists instalado_em timestamptz,
  add column if not exists encerrado_em timestamptz,
  add column if not exists observacao_acompanhamento text,
  add column if not exists updated_at timestamptz default now();

create index if not exists idx_cti_pedidos_status_ciclo on public.cti_pedidos(status_ciclo);
create index if not exists idx_cti_pedidos_instalado_em on public.cti_pedidos(instalado_em);
