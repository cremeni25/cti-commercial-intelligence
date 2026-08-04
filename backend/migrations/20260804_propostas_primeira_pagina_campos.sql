begin;

alter table public.cti_propostas
  add column if not exists voltagem text,
  add column if not exists valor_entrada numeric(14,2) check (valor_entrada is null or valor_entrada >= 0),
  add column if not exists autorizada_nome_endereco text,
  add column if not exists lynx_meses integer check (lynx_meses is null or lynx_meses >= 0);

comment on column public.cti_propostas.voltagem is
  'Campo variável da primeira página do documento oficial aplicável à versão desta proposta.';
comment on column public.cti_propostas.valor_entrada is
  'Valor de entrada da primeira página desta proposta oficial.';
comment on column public.cti_propostas.autorizada_nome_endereco is
  'Nome e endereço da autorizada Carrier informado exclusivamente nesta proposta.';
comment on column public.cti_propostas.lynx_meses is
  'Período Lynx Fleet desta proposta, somente para documentos oficiais que exibem o campo.';

commit;
