begin;

insert into public.cti_catalogo_equipamentos
(codigo, linha_produto, modelo_base, nome_comercial, configuracao, compressor, possui_eletrico, template_disponivel, ordem)
values
('CITIMAX-D5-AE','DIRECT DRIVE','CITIMAX D5','CITIMAX D5AE','ACOPLADO_E_ELETRICO',null,true,false,235),
('CITIMAX-D5','DIRECT DRIVE','CITIMAX D5','CITIMAX D5','ACOPLADO',null,false,false,236)
on conflict (codigo) do update set
  linha_produto = excluded.linha_produto,
  modelo_base = excluded.modelo_base,
  nome_comercial = excluded.nome_comercial,
  configuracao = excluded.configuracao,
  compressor = excluded.compressor,
  possui_eletrico = excluded.possui_eletrico,
  template_disponivel = excluded.template_disponivel,
  ordem = excluded.ordem,
  updated_at = now();

insert into public.cti_tabela_precos
(tabela_codigo, equipamento_codigo, preco_cheio, moeda, vigencia_inicio, ativo)
values
('TABELA-INICIAL-2026','CITIMAX-D5-AE',41000,'BRL','2026-07-30',true),
('TABELA-INICIAL-2026','CITIMAX-D5',27000,'BRL','2026-07-30',true)
on conflict (tabela_codigo, equipamento_codigo, vigencia_inicio) do update set
  preco_cheio = excluded.preco_cheio,
  moeda = excluded.moeda,
  ativo = excluded.ativo,
  updated_at = now();

update public.cti_tabela_precos
set preco_cheio = 41000, updated_at = now()
where tabela_codigo = 'TABELA-INICIAL-2026'
  and equipamento_codigo = 'CITIMAX-500-AE'
  and vigencia_inicio = '2026-07-30';

commit;
