alter table public.cti_atividades_registros
    add column if not exists parceiro_nome text,
    add column if not exists parceiro_tipo text,
    add column if not exists parceiro_organizacao text;

create or replace view public.cti_atividades as
select
    id,
    cliente_id,
    oportunidade_id,
    usuario_id,
    tipo,
    descricao,
    status,
    data_atividade,
    created_at,
    proposta_id,
    pedido_id,
    titulo,
    data,
    horario,
    updated_at,
    concluida_em,
    registro_teste,
    arquivado_em,
    arquivado_por,
    motivo_arquivamento,
    lote_arquivamento_id,
    parceiro_nome,
    parceiro_tipo,
    parceiro_organizacao
from public.cti_atividades_registros
where arquivado_em is null;
