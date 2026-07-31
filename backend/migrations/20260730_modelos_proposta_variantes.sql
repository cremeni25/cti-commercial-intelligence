begin;

insert into public.cti_modelos_proposta
(linha_produto, equipamento, nome, versao, conteudo_template, arquivo_origem, ativo)
select linha_produto, 'CITIMAX 500AE', 'Proposta Comercial CITIMAX 500AE', versao,
       conteudo_template || '{"variante_ativa":"CITIMAX 500AE","configuracao_ativa":"ACOPLADO_E_ELETRICO","possui_eletrico":true}'::jsonb,
       arquivo_origem, ativo
from public.cti_modelos_proposta
where linha_produto = 'DIRECT DRIVE' and equipamento = 'CITIMAX 500' and versao = 1
on conflict (linha_produto, equipamento, versao) do update set
 nome = excluded.nome, conteudo_template = excluded.conteudo_template,
 arquivo_origem = excluded.arquivo_origem, ativo = excluded.ativo, updated_at = now();

insert into public.cti_modelos_proposta
(linha_produto, equipamento, nome, versao, conteudo_template, arquivo_origem, ativo)
select linha_produto, 'CITIMAX D6AE', 'Proposta Comercial CITIMAX D6AE', versao,
       conteudo_template || '{"variante_ativa":"CITIMAX D6AE","configuracao_ativa":"ACOPLADO_E_ELETRICO","possui_eletrico":true,"compressor":"TM16"}'::jsonb,
       arquivo_origem, ativo
from public.cti_modelos_proposta
where linha_produto = 'DIRECT DRIVE' and equipamento = 'CITIMAX D6' and versao = 1
on conflict (linha_produto, equipamento, versao) do update set
 nome = excluded.nome, conteudo_template = excluded.conteudo_template,
 arquivo_origem = excluded.arquivo_origem, ativo = excluded.ativo, updated_at = now();

insert into public.cti_modelos_proposta
(linha_produto, equipamento, nome, versao, conteudo_template, arquivo_origem, ativo)
select linha_produto, 'CITIMAX D7AE', 'Proposta Comercial CITIMAX D7AE', versao,
       conteudo_template || '{"variante_ativa":"CITIMAX D7AE","configuracao_ativa":"ACOPLADO_E_ELETRICO","possui_eletrico":true}'::jsonb,
       arquivo_origem, ativo
from public.cti_modelos_proposta
where linha_produto = 'DIRECT DRIVE' and equipamento = 'CITIMAX D7' and versao = 1
on conflict (linha_produto, equipamento, versao) do update set
 nome = excluded.nome, conteudo_template = excluded.conteudo_template,
 arquivo_origem = excluded.arquivo_origem, ativo = excluded.ativo, updated_at = now();

insert into public.cti_modelos_proposta
(linha_produto, equipamento, nome, versao, conteudo_template, arquivo_origem, ativo)
select linha_produto, 'CITIMAX 400AE', 'Proposta Comercial CITIMAX 400AE', versao,
       conteudo_template || '{"variante_ativa":"CITIMAX 400AE","configuracao_ativa":"ACOPLADO_E_ELETRICO","possui_eletrico":true}'::jsonb,
       arquivo_origem, ativo
from public.cti_modelos_proposta
where linha_produto = 'DIRECT DRIVE' and equipamento = 'CITIMAX 400' and versao = 1
on conflict (linha_produto, equipamento, versao) do update set
 nome = excluded.nome, conteudo_template = excluded.conteudo_template,
 arquivo_origem = excluded.arquivo_origem, ativo = excluded.ativo, updated_at = now();

commit;
