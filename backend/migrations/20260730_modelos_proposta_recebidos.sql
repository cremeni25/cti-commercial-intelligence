begin;

insert into public.cti_modelos_proposta
(linha_produto, equipamento, nome, versao, conteudo_template, arquivo_origem, ativo)
values
('DIRECT DRIVE','CITIMAX 280','Proposta Comercial CITIMAX 280',1,
 '{"modelo_base":"CITIMAX 280","configuracao":"PADRAO","especificacoes":{"capacidade_0c":"3.000 W","capacidade_menos_20c":"1.600 W","vazao_ar":"2.000 m3/h","gas_refrigerante":"R 404 A"},"instalacao":"Rede Carrier","campos_variaveis":["data","empresa_faturamento","cliente","cpf_cnpj","inscricao_estadual","endereco","telefone","email","voltagem","quantidade","valor_unitario","valor_total","acessorios","condicao_pagamento","entrada","entrega","autorizada","frete","validade","dados_aplicacao","assinatura"]}'::jsonb,
 'CITIMAX 280 rev 19.05.docx',true),
('DIRECT DRIVE','CITIMAX 400','Proposta Comercial CITIMAX 400',1,
 '{"modelo_base":"CITIMAX 400","configuracao":"ACOPLADO","especificacoes":{"capacidade_0c":"4.250 W","capacidade_menos_20c":"2.200 W","vazao_ar":"2.000 m3/h","gas_refrigerante":"R 404 A"},"instalacao":"Rede Carrier","campos_variaveis":["data","empresa_faturamento","cliente","cpf_cnpj","inscricao_estadual","endereco","telefone","email","voltagem","quantidade","valor_unitario","valor_total","acessorios","condicao_pagamento","entrada","entrega","autorizada","frete","validade","dados_aplicacao","assinatura"]}'::jsonb,
 'CITIMAX 400 Rev 19.05.docx',true),
('DIRECT DRIVE','CITIMAX 500','Proposta Comercial CITIMAX 500 e 500AE',1,
 '{"modelo_base":"CITIMAX 500","variantes":[{"nome_comercial":"CITIMAX 500","configuracao":"ACOPLADO","possui_eletrico":false},{"nome_comercial":"CITIMAX 500AE","configuracao":"ACOPLADO_E_ELETRICO","possui_eletrico":true}],"compressor":"TM16","especificacoes":{"capacidade_0c":"5.100 W","capacidade_menos_20c":"2.700 W","vazao_ar":"2.200 m3/h","gas_refrigerante":"R 404 A"},"instalacao":"Rede Carrier","campos_variaveis":["data","empresa_faturamento","cliente","cpf_cnpj","inscricao_estadual","endereco","telefone","email","voltagem","tipo_equipamento","quantidade","valor_unitario","valor_total","acessorios","condicao_pagamento","entrada","entrega","autorizada","frete","validade","dados_aplicacao","assinatura"]}'::jsonb,
 'CITIMAX 500 rev 19.05.doc',true),
('DIRECT DRIVE','CITIMAX D7','Proposta Comercial CITIMAX D7 e D7AE',1,
 '{"modelo_base":"CITIMAX D7","variantes":[{"nome_comercial":"CITIMAX D7","configuracao":"ACOPLADO","possui_eletrico":false},{"nome_comercial":"CITIMAX D7AE","configuracao":"ACOPLADO_E_ELETRICO","possui_eletrico":true}],"especificacoes":{"capacidade_0c":"6.550 W","capacidade_menos_20c":"3.490 W","vazao_ar":"2.200 m3/h","gas_refrigerante":"R 404 A"},"instalacao":"Rede Carrier","campos_variaveis":["data","empresa_faturamento","cliente","cpf_cnpj","inscricao_estadual","endereco","telefone","email","voltagem","tipo_equipamento","quantidade","valor_unitario","valor_total","acessorios","condicao_pagamento","entrada","entrega","autorizada","frete","validade","dados_aplicacao","assinatura"]}'::jsonb,
 'CITIMAX D7 Rev 19.05.docx',true),
('DIRECT DRIVE','CITIMAX D6','Proposta Comercial CITIMAX D6 e D6AE',1,
 '{"modelo_base":"CITIMAX D6","herda_modelo":"CITIMAX D7","variantes":[{"nome_comercial":"CITIMAX D6","configuracao":"ACOPLADO","possui_eletrico":false},{"nome_comercial":"CITIMAX D6AE","configuracao":"ACOPLADO_E_ELETRICO","possui_eletrico":true}],"substituicoes":{"modelo":"CITIMAX D6","compressor":"TM16"},"instalacao":"Rede Carrier"}'::jsonb,
 'DERIVADO:CITIMAX D7 Rev 19.05.docx',true),
('DIRECT DRIVE','XARIOS 350','Proposta Comercial XARIOS 350',1,
 '{"modelo_base":"XARIOS 350","configuracao":"PADRAO","compressor":"QP15","possui_eletrico":true,"especificacoes":{"capacidade_0c":"3.530 W","capacidade_menos_20c":"2.020 W","vazao_ar":"1.520 m3/h","gas_refrigerante":"R 404 A","motor_eletrico":"220V/380V automático"},"instalacao":"Rede Carrier"}'::jsonb,
 'XARIOS 350 Rev 19.05.doc',true),
('DIRECT DRIVE','XARIOS 6','Proposta Comercial XARIOS 6',1,
 '{"modelo_base":"XARIOS 6","configuracao":"PADRAO","compressor":"QP16","possui_eletrico":true,"especificacoes":{"capacidade_0c":"5.310 W","capacidade_menos_20c":"2.700 W","vazao_ar":"2.190 m3/h","gas_refrigerante":"R 404 A","motor_eletrico":"220V/380V automático"},"instalacao":"Rede Carrier"}'::jsonb,
 'XARIOS 6 Rev 19.05.doc',true),
('DIESEL TRUCK','SUPRA 750','Proposta Comercial SUPRA 750',1,
 '{"modelo_base":"SUPRA 750","compressor":"05K 2CC","possui_eletrico":true,"especificacoes":{"capacidade_2c":"20.500 Btu/h","capacidade_menos_29c":"7.500 Btu/h","vazao_ar":"2.400 m3/h","gas_refrigerante":"R 404 A","motor_diesel":"Kubota","motor_eletrico":"220V/380V automático"},"instalacao":"Rede Carrier"}'::jsonb,
 'SUPRA 750 Rev 19.05.docx',true),
('DIESEL TRUCK','SUPRA 850','Proposta Comercial SUPRA 850',1,
 '{"modelo_base":"SUPRA 850","compressor":"05K 4CC","possui_eletrico":true,"especificacoes":{"capacidade_2c":"23.000 Btu/h","capacidade_menos_18c":"15.500 Btu/h","capacidade_menos_29c":"10.000 Btu/h","vazao_ar":"2.300 m3/h","gas_refrigerante":"R 404 A","motor_diesel":"Kubota","motor_eletrico":"220V/380V automático"},"instalacao":"Rede Carrier"}'::jsonb,
 'SUPRA 850 Rev 19.05.docx',true),
('DIESEL TRUCK','SUPRA 1150','Proposta Comercial SUPRA 1150',1,
 '{"modelo_base":"SUPRA 1150","compressor":"05G 6CC","possui_eletrico":true,"especificacoes":{"capacidade_0c":"35.800 Btu/h","capacidade_menos_20c":"21.700 Btu/h","vazao_ar":"3.350 m3/h","gas_refrigerante":"R 404 A","motor_diesel":"Kubota","motor_eletrico":"220V ou 380V"},"instalacao":"Rede Carrier"}'::jsonb,
 'SUPRA 1150 Rev 19.05.docx',true),
('DIESEL TRUCK','S8','Proposta Comercial S8',1,
 '{"modelo_base":"S8","compressor":"05K 2CC","possui_eletrico":true,"especificacoes":{"capacidade_2c":"22.000 Btu/h","capacidade_menos_18c":"14.000 Btu/h","capacidade_menos_29c":"8.500 Btu/h","vazao_ar":"2.548 m3/h","gas_refrigerante":"R 404 A","motor_diesel":"Kubota","motor_eletrico":"220V/380V automático"},"instalacao":"Rede Carrier"}'::jsonb,
 'S 8 Rev 19.05.docx',true),
('DIESEL TRUCK','S9','Proposta Comercial S9',1,
 '{"modelo_base":"S9","compressor":"05K 4CC","possui_eletrico":true,"especificacoes":{"capacidade_2c":"24.000 Btu/h","capacidade_menos_18c":"18.500 Btu/h","capacidade_menos_29c":"11.500 Btu/h","vazao_ar":"2.548 m3/h","gas_refrigerante":"R 404 A","motor_diesel":"Kubota","motor_eletrico":"220V/380V automático"},"instalacao":"Rede Carrier"}'::jsonb,
 'S 9 Rev 19.05.docx',true)
on conflict (linha_produto, equipamento, versao) do update set
  nome = excluded.nome,
  conteudo_template = excluded.conteudo_template,
  arquivo_origem = excluded.arquivo_origem,
  ativo = excluded.ativo,
  updated_at = now();

update public.cti_catalogo_equipamentos set template_disponivel = true, updated_at = now()
where codigo in (
 'CITIMAX-280','CITIMAX-400','CITIMAX-400-AE','CITIMAX-500','CITIMAX-500-AE',
 'CITIMAX-D6','CITIMAX-D6-AE','CITIMAX-D7','CITIMAX-D7-AE','XARIOS-350','XARIOS-6',
 'SUPRA-750','SUPRA-850','SUPRA-1150','S8','S9'
);

update public.cti_catalogo_equipamentos set template_disponivel = false, updated_at = now()
where linha_produto = 'TRAILER';

commit;
