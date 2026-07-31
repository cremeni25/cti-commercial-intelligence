begin;

create or replace function public.cti_proteger_template_comercial()
returns trigger
language plpgsql
as $$
begin
  if old.imutavel = true
     and old.arquivo_template_hash_sha256 is not null
     and old.arquivo_template_storage is not null
     and old.homologado_em is not null
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

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'CITIMAX 280  rev 19.05.docx',
    arquivo_template_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    arquivo_template_tamanho_bytes = 114827,
    arquivo_template_hash_sha256 = 'cfff7c3150ebb5996c7799392758860d09fe57ff733bf400329328f0297be134',
    updated_at = now()
where linha_produto = 'DIRECT DRIVE' and equipamento = 'CITIMAX 280' and versao = 1;

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'CITIMAX 400  Rev 19.05.docx',
    arquivo_template_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    arquivo_template_tamanho_bytes = 115680,
    arquivo_template_hash_sha256 = 'a5ffe314e90ced97ab094e9ad7e7dfab459fdd1b1e6e330d93338e26d605b348',
    updated_at = now()
where linha_produto = 'DIRECT DRIVE' and equipamento in ('CITIMAX 400','CITIMAX 400AE') and versao = 1;

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'CITIMAX 500 rev 19.05.doc',
    arquivo_template_mime = 'application/msword',
    arquivo_template_tamanho_bytes = 193024,
    arquivo_template_hash_sha256 = 'c84d26142315e43549e8722f49dfbc1732b192f6f21462a468acbd63e51614e6',
    updated_at = now()
where linha_produto = 'DIRECT DRIVE' and equipamento in ('CITIMAX 500','CITIMAX 500AE') and versao = 1;

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'CITIMAX D7 Rev 19.05.docx',
    arquivo_template_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    arquivo_template_tamanho_bytes = 145617,
    arquivo_template_hash_sha256 = '73959306b3ba9aa737110fa3f86738968f919bbb01d5f2f0940798971148c106',
    updated_at = now()
where linha_produto = 'DIRECT DRIVE' and equipamento in ('CITIMAX D6','CITIMAX D6AE','CITIMAX D7','CITIMAX D7AE') and versao = 1;

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'XARIOS 350 Rev 19.05.doc',
    arquivo_template_mime = 'application/msword',
    arquivo_template_tamanho_bytes = 333824,
    arquivo_template_hash_sha256 = '68cb1d1fcb68b050a3d8709afa301285ec5e56f2e8897007cc42b01c06e3bedf',
    updated_at = now()
where linha_produto = 'DIRECT DRIVE' and equipamento = 'XARIOS 350' and versao = 1;

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'XARIOS 6 Rev 19.05.doc',
    arquivo_template_mime = 'application/msword',
    arquivo_template_tamanho_bytes = 365056,
    arquivo_template_hash_sha256 = 'b23b08868f4417b9672425c0b27f1c9d0b4c62004a8a9a70b01f5fa1e3917b01',
    updated_at = now()
where linha_produto = 'DIRECT DRIVE' and equipamento = 'XARIOS 6' and versao = 1;

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'SUPRA 750 Rev 19.05.docx',
    arquivo_template_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    arquivo_template_tamanho_bytes = 175128,
    arquivo_template_hash_sha256 = 'b92f82b82ea0dc6b5ad3930e5856f1784a1a372b370dd244fcc6578f322f12e3',
    updated_at = now()
where linha_produto = 'DIESEL TRUCK' and equipamento = 'SUPRA 750' and versao = 1;

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'SUPRA 850 Rev 19.05.docx',
    arquivo_template_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    arquivo_template_tamanho_bytes = 173828,
    arquivo_template_hash_sha256 = '6f3f38de5213ccee25bcc646c3b4810f6859ff5c666f741adc1ed2313b3708ef',
    updated_at = now()
where linha_produto = 'DIESEL TRUCK' and equipamento = 'SUPRA 850' and versao = 1;

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'SUPRA 1150 Rev 19.05.docx',
    arquivo_template_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    arquivo_template_tamanho_bytes = 173748,
    arquivo_template_hash_sha256 = 'b0cb9876d78f552d49d528ac3408a9095e2af284bfbc2a9812f14b60385a2e98',
    updated_at = now()
where linha_produto = 'DIESEL TRUCK' and equipamento = 'SUPRA 1150' and versao = 1;

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'S 8 Rev 19.05.docx',
    arquivo_template_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    arquivo_template_tamanho_bytes = 126952,
    arquivo_template_hash_sha256 = 'f1a879d4ca39c717a957dfd9c0588c97cfb69380fce0cfc0d71514c7133f3e36',
    updated_at = now()
where linha_produto = 'DIESEL TRUCK' and equipamento = 'S8' and versao = 1;

update public.cti_modelos_proposta
set arquivo_template_nome_original = 'S 9  Rev 19.05.docx',
    arquivo_template_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    arquivo_template_tamanho_bytes = 124116,
    arquivo_template_hash_sha256 = 'd910f7c912f79c09fe0e152f2e9b13d71060b175544ca3accf2aea1167e27487',
    updated_at = now()
where linha_produto = 'DIESEL TRUCK' and equipamento = 'S9' and versao = 1;

insert into public.cti_modelos_proposta_auditoria
(modelo_proposta_id, operacao, versao, arquivo_template_nome_original, arquivo_template_hash_sha256, conteudo_template, justificativa)
select id, 'CORRECAO_METADADOS', versao, arquivo_template_nome_original,
       arquivo_template_hash_sha256, conteudo_template,
       'Registro do hash SHA-256 calculado diretamente sobre o arquivo Carrier original, sem conversão ou alteração.'
from public.cti_modelos_proposta
where ativo = true
  and arquivo_template_hash_sha256 is not null
  and not exists (
    select 1
    from public.cti_modelos_proposta_auditoria a
    where a.modelo_proposta_id = cti_modelos_proposta.id
      and a.arquivo_template_hash_sha256 = cti_modelos_proposta.arquivo_template_hash_sha256
      and a.operacao = 'CORRECAO_METADADOS'
  );

commit;
