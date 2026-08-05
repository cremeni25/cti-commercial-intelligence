-- Supabase isolado para homologação da IA Comercial CTI.
-- Executar somente em um NOVO projeto Supabase de homologação.
-- Não executar no projeto produtivo.

create extension if not exists pgcrypto;

create table if not exists public.cti_users (
  id uuid primary key default gen_random_uuid(),
  auth_id uuid unique,
  email text unique not null,
  nome text not null,
  tipo_usuario text not null default 'ADMIN_MASTER',
  ativo boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.cti_user_permissions (
  user_id uuid primary key references public.cti_users(id) on delete cascade,
  acesso_total boolean not null default false,
  usuarios_administrar boolean not null default false,
  configuracoes_administrar boolean not null default false
);

create table if not exists public.clientes (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  cidade text,
  uf text,
  ddd text,
  segmento text,
  created_at timestamptz not null default now()
);

create table if not exists public.cti_oportunidades (
  id uuid primary key default gen_random_uuid(),
  cliente_id uuid references public.clientes(id),
  responsavel_id uuid references public.cti_users(id),
  titulo text not null,
  status text,
  linha text,
  valor_estimado numeric(14,2),
  probabilidade numeric(5,2),
  data_fechamento_prevista date,
  created_at timestamptz not null default now()
);

create table if not exists public.cti_oportunidade_itens (
  id uuid primary key default gen_random_uuid(),
  oportunidade_id uuid references public.cti_oportunidades(id) on delete cascade,
  produto text,
  linha text,
  quantidade integer not null default 1,
  valor_unitario numeric(14,2)
);

create table if not exists public.cti_propostas (
  id uuid primary key default gen_random_uuid(),
  oportunidade_id uuid references public.cti_oportunidades(id),
  numero text,
  status text,
  valor_total numeric(14,2),
  created_at timestamptz not null default now()
);

create table if not exists public.cti_pedidos (
  id uuid primary key default gen_random_uuid(),
  oportunidade_id uuid references public.cti_oportunidades(id),
  numero text,
  status text,
  valor_total numeric(14,2),
  created_at timestamptz not null default now()
);

create table if not exists public.cti_atividades (
  id uuid primary key default gen_random_uuid(),
  responsavel_id uuid references public.cti_users(id),
  cliente_id uuid references public.clientes(id),
  tipo text,
  descricao text,
  data_atividade timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.cti_anfir (
  id uuid primary key default gen_random_uuid(),
  cliente text,
  implementadora text,
  fabricante_equipamento text,
  produto text,
  linha text,
  cidade text,
  uf text,
  ddd text,
  data_registro date,
  quantidade integer not null default 1,
  valor numeric(14,2),
  created_at timestamptz not null default now()
);

alter table public.cti_users enable row level security;
alter table public.cti_user_permissions enable row level security;
alter table public.clientes enable row level security;
alter table public.cti_oportunidades enable row level security;
alter table public.cti_oportunidade_itens enable row level security;
alter table public.cti_propostas enable row level security;
alter table public.cti_pedidos enable row level security;
alter table public.cti_atividades enable row level security;
alter table public.cti_anfir enable row level security;

-- Homologação: usuários autenticados podem somente ler.
do $$
declare
  tabela text;
begin
  foreach tabela in array array[
    'cti_users','cti_user_permissions','clientes','cti_oportunidades',
    'cti_oportunidade_itens','cti_propostas','cti_pedidos','cti_atividades','cti_anfir'
  ] loop
    execute format('drop policy if exists homologacao_leitura on public.%I', tabela);
    execute format(
      'create policy homologacao_leitura on public.%I for select to authenticated using (true)',
      tabela
    );
  end loop;
end $$;

-- Nenhuma policy de insert, update ou delete é criada.
-- Portanto, a chave pública/anon do projeto não possui caminho de escrita.

insert into public.clientes (nome, cidade, uf, ddd, segmento)
values
  ('Cliente Homologação Alimentos', 'São Paulo', 'SP', '011', 'Alimentos'),
  ('Cliente Homologação Farma', 'Campinas', 'SP', '019', 'Farmacêutico')
on conflict do nothing;

insert into public.cti_anfir
  (cliente, implementadora, fabricante_equipamento, produto, linha, cidade, uf, ddd, data_registro, quantidade, valor)
values
  ('Cliente Homologação Alimentos', 'Implementadora Teste', 'Carrier', 'Vector HE19', 'TRAILER', 'São Paulo', 'SP', '011', current_date - 30, 2, 420000),
  ('Cliente Homologação Farma', 'Implementadora Teste', 'Carrier', 'Supra 850', 'DIESEL TRUCK', 'Campinas', 'SP', '019', current_date - 60, 1, 180000)
on conflict do nothing;
