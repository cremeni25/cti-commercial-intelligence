begin;

alter table public.cti_modelos_proposta
  add column if not exists origem_documento text not null default 'CARRIER',
  add column if not exists arquivo_template_storage text,
  add column if not exists arquivo_template_nome_original text,
  add column if not exists arquivo_template_mime text,
  add column if not exists arquivo_template_tamanho_bytes bigint,
  add column if not exists arquivo_template_hash_sha256 text,
  add column if not exists layout_preservado boolean not null default true,
  add column if not exists conteudo_integral_obrigatorio boolean not null default true,
  add column if not exists imutavel boolean not null default true,
  add column if not exists homologado_em timestamptz,
  add column if not exists homologado_por uuid,
  add column if not exists observacoes_integridade text;

alter table public.cti_modelos_proposta
  drop constraint if exists cti_modelos_proposta_origem_documento_check;

alter table public.cti_modelos_proposta
  add constraint cti_modelos_proposta_origem_documento_check
  check (origem_documento in ('CARRIER','VIENA','CTI','OUTRO'));

alter table public.cti_modelos_proposta
  drop constraint if exists cti_modelos_proposta_hash_sha256_check;

alter table public.cti_modelos_proposta
  add constraint cti_modelos_proposta_hash_sha256_check
  check (
    arquivo_template_hash_sha256 is null
    or arquivo_template_hash_sha256 ~ '^[a-fA-F0-9]{64}$'
  );

create table if not exists public.cti_modelos_proposta_auditoria (
  id uuid primary key default gen_random_uuid(),
  modelo_proposta_id uuid not null references public.cti_modelos_proposta(id) on delete restrict,
  operacao text not null,
  versao integer not null,
  arquivo_template_storage text,
  arquivo_template_nome_original text,
  arquivo_template_hash_sha256 text,
  conteudo_template jsonb not null default '{}'::jsonb,
  executado_por uuid,
  executado_em timestamptz not null default now(),
  justificativa text,
  constraint cti_modelos_proposta_auditoria_operacao_check
    check (operacao in ('CRIACAO','HOMOLOGACAO','ATIVACAO','DESATIVACAO','NOVA_VERSAO','CORRECAO_METADADOS'))
);

create index if not exists cti_modelos_proposta_auditoria_modelo_idx
  on public.cti_modelos_proposta_auditoria(modelo_proposta_id, executado_em desc);

create or replace function public.cti_proteger_template_comercial()
returns trigger
language plpgsql
as $$
begin
  if old.imutavel = true
     and old.arquivo_template_hash_sha256 is not null
     and (
       new.arquivo_template_storage is distinct from old.arquivo_template_storage
       or new.arquivo_template_nome_original is distinct from old.arquivo_template_nome_original
       or new.arquivo_template_mime is distinct from old.arquivo_template_mime
       or new.arquivo_template_tamanho_bytes is distinct from old.arquivo_template_tamanho_bytes
       or new.arquivo_template_hash_sha256 is distinct from old.arquivo_template_hash_sha256
       or new.conteudo_template is distinct from old.conteudo_template
       or new.linha_produto is distinct from old.linha_produto
       or new.equipamento is distinct from old.equipamento
       or new.versao is distinct from old.versao
     )
  then
    raise exception using
      errcode = 'P0001',
      message = 'Template comercial imutável. Crie uma nova versão; não altere o documento Carrier homologado.';
  end if;

  return new;
end;
$$;

drop trigger if exists trg_cti_proteger_template_comercial
  on public.cti_modelos_proposta;

create trigger trg_cti_proteger_template_comercial
before update on public.cti_modelos_proposta
for each row
execute function public.cti_proteger_template_comercial();

update public.cti_modelos_proposta
set
  origem_documento = 'CARRIER',
  layout_preservado = true,
  conteudo_integral_obrigatorio = true,
  imutavel = true,
  observacoes_integridade = coalesce(
    observacoes_integridade,
    'Documento mestre Carrier: preservar integralmente textos técnicos, comerciais, jurídicos, garantias, responsabilidades, tabela de revisões, identidade visual, paginação, tabelas, cabeçalhos e rodapés. Somente campos variáveis previamente mapeados podem ser preenchidos.'
  ),
  updated_at = now()
where ativo = true;

commit;
