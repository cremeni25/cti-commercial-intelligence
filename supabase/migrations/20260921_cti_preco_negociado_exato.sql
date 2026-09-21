alter table public.cti_oportunidade_itens_registros
  add column if not exists preco_negociado_unitario numeric(14,2)
  check (preco_negociado_unitario is null or preco_negociado_unitario >= 0);

create or replace view public.cti_oportunidade_itens as
select
    id,
    oportunidade_id,
    linha_produto,
    equipamento,
    configuracao,
    quantidade,
    preco_unitario,
    desconto_percentual,
    (
      round(
        quantidade::numeric *
        coalesce(
          preco_negociado_unitario,
          preco_unitario * (1 - desconto_percentual / 100)
        ),
        2
      )
    )::numeric(14,2) as valor_total,
    condicao_pagamento,
    prazo_entrega,
    validade_condicao,
    frete,
    local_entrega,
    garantia,
    opcionais,
    observacoes_comerciais,
    observacoes_tecnicas,
    status,
    ordem,
    created_at,
    updated_at,
    equipamento_codigo,
    modelo_base,
    nome_comercial,
    preco_tabela,
    tabela_preco_codigo,
    tabela_preco_vigencia,
    compressor,
    possui_eletrico,
    registro_teste,
    arquivado_em,
    arquivado_por,
    motivo_arquivamento,
    lote_arquivamento_id,
    preco_negociado_unitario
from public.cti_oportunidade_itens_registros
where arquivado_em is null
with local check option;

grant select, insert, update, delete, truncate, references, trigger
on public.cti_oportunidade_itens
to postgres, anon, authenticated, service_role;
