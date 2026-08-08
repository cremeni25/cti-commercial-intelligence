begin;

alter table public.clientes
  add column if not exists cnpj text,
  add column if not exists inscricao_estadual text,
  add column if not exists endereco text,
  add column if not exists numero text,
  add column if not exists complemento text,
  add column if not exists bairro text,
  add column if not exists cep text,
  add column if not exists contato text,
  add column if not exists fone text,
  add column if not exists email text,
  add column if not exists email_xml text,
  add column if not exists categoria text,
  add column if not exists ddd text,
  add column if not exists sub_regiao text,
  add column if not exists updated_at timestamptz default now();

create unique index if not exists clientes_cnpj_normalizado_unique
  on public.clientes ((regexp_replace(cnpj, '\D', '', 'g')))
  where nullif(regexp_replace(coalesce(cnpj,''), '\D', '', 'g'),'') is not null;

insert into public.clientes (nome, cidade, estado, cnpj, segmento, categoria, ddd, sub_regiao, status)
select distinct on (upper(trim(a.cliente)))
  trim(a.cliente),
  nullif(trim(a.cidade),''),
  nullif(upper(trim(a.estado)),''),
  nullif(regexp_replace(coalesce(a.cnpj,''),'\D','','g'),''),
  'TRANSPORTADOR',
  'TRANSPORTADORA',
  nullif(regexp_replace(coalesce(a.ddd,''),'\D','','g'),''),
  nullif(trim(a.sub_regiao),''),
  'ATIVO'
from public.cti_anfir a
where coalesce(trim(a.cliente),'') <> ''
  and upper(coalesce(trim(a.estado),'')) = 'SP'
  and not exists (
    select 1 from public.clientes c
    where upper(trim(c.nome)) = upper(trim(a.cliente))
       or (
         nullif(regexp_replace(coalesce(c.cnpj,''),'\D','','g'),'') is not null
         and nullif(regexp_replace(coalesce(a.cnpj,''),'\D','','g'),'') is not null
         and regexp_replace(c.cnpj,'\D','','g') = regexp_replace(a.cnpj,'\D','','g')
       )
  )
order by upper(trim(a.cliente)), a.created_at desc nulls last;

commit;
