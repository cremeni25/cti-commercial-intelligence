begin;

comment on table public.cti_destinatarios_carrier is
  'Cadastro genérico de destinatários administrativos. O nome físico legado é mantido somente por compatibilidade técnica; não restringe destinatários à Carrier.';

comment on table public.cti_envios_carrier is
  'Fila genérica de envios comerciais. O nome físico legado é mantido somente por compatibilidade técnica; pode atender Carrier, Viena, clientes, parceiros ou terceiros selecionados manualmente.';

create or replace view public.cti_destinatarios_administrativos as
select id, nome, email, cargo, ativo, created_at, updated_at
from public.cti_destinatarios_carrier;

create or replace view public.cti_envios_comerciais as
select id, pedido_id, proposta_id, destinatarios, documentos, assunto, corpo,
       status, tentativas, erro, enviado_por, created_at, enviado_em
from public.cti_envios_carrier;

commit;
