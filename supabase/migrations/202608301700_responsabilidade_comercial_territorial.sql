-- CTI 2026-08-30 — território geográfico separado da responsabilidade comercial efetiva.
alter table public.clientes add column if not exists responsavel_comercial_id uuid null references public.cti_users(id) on delete set null;
alter table public.clientes add column if not exists responsabilidade_tipo text not null default 'TERRITORIO';
alter table public.clientes add column if not exists responsabilidade_atualizada_em timestamptz null;
alter table public.clientes add column if not exists responsabilidade_atualizada_por uuid null references public.cti_users(id) on delete set null;

create table if not exists public.cti_territorio_regras (
 id uuid primary key default gen_random_uuid(), ddd text not null, codigo_regional text not null,
 nome_humano text not null, regra_tipo text not null check (regra_tipo in ('CIDADE','BAIRRO','CEP_PREFIXO')),
 valor text not null, prioridade integer not null default 100, origem text not null default 'REGRA_COMERCIAL_HOMOLOGADA',
 ativo boolean not null default true, created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 unique(ddd,codigo_regional,regra_tipo,valor)
);

create table if not exists public.cti_cliente_responsabilidade_historico (
 id uuid primary key default gen_random_uuid(), cliente_id uuid not null references public.clientes(id) on delete cascade,
 responsavel_anterior_id uuid null references public.cti_users(id) on delete set null,
 responsavel_novo_id uuid null references public.cti_users(id) on delete set null,
 tipo_anterior text null, tipo_novo text not null, motivo text null,
 alterado_por uuid null references public.cti_users(id) on delete set null, created_at timestamptz not null default now()
);

create index if not exists idx_clientes_responsavel_comercial on public.clientes(responsavel_comercial_id);
create index if not exists idx_clientes_ddd_subregiao on public.clientes(ddd,sub_regiao);
create index if not exists idx_cti_territorio_regras_lookup on public.cti_territorio_regras(ddd,regra_tipo,valor) where ativo;

insert into public.cti_territorio_regras(ddd,codigo_regional,nome_humano,regra_tipo,valor,prioridade) values
('011','REGIAO 01','Região Leste','CIDADE','GUARULHOS',10),('011','REGIAO 01','Região Leste','CIDADE','ATIBAIA',10),('011','REGIAO 01','Região Leste','CIDADE','MAIRIPORA',10),('011','REGIAO 01','Região Leste','CIDADE','MOGI DAS CRUZES',10),('011','REGIAO 01','Região Leste','CIDADE','SUZANO',10),
('011','REGIAO 02','Região Oeste','CIDADE','BARUERI',10),('011','REGIAO 02','Região Oeste','CIDADE','OSASCO',10),('011','REGIAO 02','Região Oeste','CIDADE','CARAPICUIBA',10),('011','REGIAO 02','Região Oeste','CIDADE','COTIA',10),('011','REGIAO 02','Região Oeste','CIDADE','SANTANA DE PARNAIBA',10),('011','REGIAO 02','Região Oeste','CIDADE','JANDIRA',10),('011','REGIAO 02','Região Oeste','CIDADE','TABOAO DA SERRA',10),('011','REGIAO 02','Região Oeste','CIDADE','EMBU DAS ARTES',10),('011','REGIAO 02','Região Oeste','CIDADE','CAJAMAR',10),('011','REGIAO 02','Região Oeste','CIDADE','FRANCO DA ROCHA',10),('011','REGIAO 02','Região Oeste','CIDADE','JUNDIAI',10),('011','REGIAO 02','Região Oeste','CIDADE','ITUPEVA',10),('011','REGIAO 02','Região Oeste','CIDADE','CABREUVA',10),
('011','REGIAO 01','Região Leste','BAIRRO','PENHA',5),('011','REGIAO 01','Região Leste','BAIRRO','CIDADE LIDER',5),('011','REGIAO 01','Região Leste','BAIRRO','CIDADE TIRADENTES',5),('011','REGIAO 01','Região Leste','BAIRRO','ITAQUERA',5),('011','REGIAO 01','Região Leste','BAIRRO','JD GUAIANAZES',5),('011','REGIAO 01','Região Leste','BAIRRO','MOOCA',5),('011','REGIAO 01','Região Leste','BAIRRO','PARQUE DA MOOCA',5),('011','REGIAO 01','Região Leste','BAIRRO','QUARTA PARADA',5),('011','REGIAO 01','Região Leste','BAIRRO','VILA BERTIOGA',5),('011','REGIAO 01','Região Leste','BAIRRO','VILA GOMES CARDIM',5),('011','REGIAO 01','Região Leste','BAIRRO','VILA PRUDENTE',5),('011','REGIAO 01','Região Leste','BAIRRO','PQ NOVO MUNDO',5),
('011','REGIAO 02','Região Oeste','BAIRRO','JAGUARE',5),('011','REGIAO 02','Região Oeste','BAIRRO','VILA LEOPOLDINA',5),('011','REGIAO 02','Região Oeste','BAIRRO','BUTANTA',5),('011','REGIAO 02','Região Oeste','BAIRRO','VILA BUTANTA',5),('011','REGIAO 02','Região Oeste','BAIRRO','JARDIM IPANEMA  ZONA OESTE',5),('011','REGIAO 02','Região Oeste','BAIRRO','PARQUE SAO DOMINGOS',5),('011','REGIAO 02','Região Oeste','BAIRRO','PINHEIROS',5),('011','REGIAO 02','Região Oeste','BAIRRO','PRQ DOS PRINCIPES',5),('011','REGIAO 02','Região Oeste','BAIRRO','JARAGUA',5),('011','REGIAO 02','Região Oeste','BAIRRO','JARDIM JARAGUA',5),('011','REGIAO 02','Região Oeste','BAIRRO','JARDIM JARAGUA  SAO DOMINGOS',5),('011','REGIAO 02','Região Oeste','BAIRRO','VILA CLARICE',5),('011','REGIAO 02','Região Oeste','BAIRRO','PERUS',5),('011','REGIAO 02','Região Oeste','BAIRRO','VILA OLIMPIA',5),('011','REGIAO 02','Região Oeste','BAIRRO','BROOKLIN PAULISTA',5),('011','REGIAO 02','Região Oeste','BAIRRO','PARAISOPOLIS',5),('011','REGIAO 02','Região Oeste','BAIRRO','PARQUE REBOUCAS',5)
on conflict do nothing;
