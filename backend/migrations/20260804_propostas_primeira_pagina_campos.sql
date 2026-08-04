begin;

alter table public.cti_oportunidade_itens
  add column if not exists voltagem text,
  add column if not exists valor_entrada numeric(14,2) check (valor_entrada is null or valor_entrada >= 0),
  add column if not exists autorizada_nome_endereco text,
  add column if not exists lynx_meses integer check (lynx_meses is null or lynx_meses >= 0);

comment on column public.cti_oportunidade_itens.voltagem is
  'Campo variável da primeira página dos documentos oficiais aplicáveis; uso exclusivo do módulo Propostas.';
comment on column public.cti_oportunidade_itens.valor_entrada is
  'Valor de entrada da primeira página da proposta oficial; não representa garantia ou condição documental compartilhada.';
comment on column public.cti_oportunidade_itens.autorizada_nome_endereco is
  'Nome e endereço da autorizada Carrier informado exclusivamente para a proposta.';
comment on column public.cti_oportunidade_itens.lynx_meses is
  'Período Lynx Fleet somente para documentos oficiais que exibem esse campo na primeira página.';

commit;
