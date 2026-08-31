-- CTI — Verdade Comercial Transversal
-- Preserva fontes originais e cria apenas vínculos/evidências reconciliadas.

create table if not exists public.cti_evidencias_comerciais (
  id uuid primary key default gen_random_uuid(),
  fonte text not null,
  fonte_registro_id text not null,
  cliente_id uuid null references public.clientes(id) on delete set null,
  cnpj_normalizado text null,
  cliente_nome text null,
  temporalidade text not null,
  evento text not null,
  estado_comercial text null,
  data_evento date null,
  segmento text null,
  equipamento text null,
  quantidade numeric null,
  valor numeric null,
  responsavel_id uuid null,
  metodo_reconciliacao text not null default 'SEM_RECONCILIACAO',
  confianca numeric not null default 0,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (fonte, fonte_registro_id, evento)
);

create index if not exists idx_cti_evidencias_cliente on public.cti_evidencias_comerciais(cliente_id);
create index if not exists idx_cti_evidencias_cnpj on public.cti_evidencias_comerciais(cnpj_normalizado);
create index if not exists idx_cti_evidencias_fonte on public.cti_evidencias_comerciais(fonte, data_evento);
create index if not exists idx_cti_evidencias_temporal on public.cti_evidencias_comerciais(temporalidade, estado_comercial);

-- ANFIR: passado confirmado. Só vincula por CNPJ inequívoco; sem CNPJ permanece como evidência não reconciliada.
insert into public.cti_evidencias_comerciais
  (fonte,fonte_registro_id,cliente_id,cnpj_normalizado,cliente_nome,temporalidade,evento,estado_comercial,data_evento,segmento,equipamento,quantidade,valor,metodo_reconciliacao,confianca,metadata)
select
  'ANFIR', a.id::text, c.id,
  nullif(regexp_replace(coalesce(a.cnpj,''),'\D','','g'),''), a.cliente,
  'PASSADO_CONFIRMADO','RESULTADO_MERCADO',upper(coalesce(a.status,a.categoria,'ENCERRADO')),
  case when a.ano is not null and a.mes between 1 and 12 then make_date(a.ano,a.mes,1) else null end,
  a.linha, coalesce(a.equipamento,a.modelo), coalesce(a.quantidade,1), a.valor,
  case when c.id is not null then 'CNPJ_EXATO' else 'SEM_RECONCILIACAO' end,
  case when c.id is not null then 1 else 0 end,
  jsonb_build_object('arquivo_origem',a.arquivo_origem,'categoria_fonte',a.categoria,'status_fonte',a.status,'chassi',a.chassi,'placa',a.placa)
from public.cti_anfir a
left join public.clientes c
  on nullif(regexp_replace(coalesce(a.cnpj,''),'\D','','g'),'') is not null
 and regexp_replace(coalesce(c.cnpj,''),'\D','','g') = regexp_replace(coalesce(a.cnpj,''),'\D','','g')
where coalesce(a.ativo,true)=true
on conflict (fonte,fonte_registro_id,evento) do update set
  cliente_id=excluded.cliente_id, cnpj_normalizado=excluded.cnpj_normalizado, cliente_nome=excluded.cliente_nome,
  temporalidade=excluded.temporalidade, estado_comercial=excluded.estado_comercial, data_evento=excluded.data_evento,
  segmento=excluded.segmento, equipamento=excluded.equipamento, quantidade=excluded.quantidade, valor=excluded.valor,
  metodo_reconciliacao=excluded.metodo_reconciliacao, confianca=excluded.confianca, metadata=excluded.metadata, updated_at=now();

-- CRM: ação diária/origem operacional.
insert into public.cti_evidencias_comerciais
  (fonte,fonte_registro_id,cliente_id,cliente_nome,temporalidade,evento,estado_comercial,data_evento,responsavel_id,metodo_reconciliacao,confianca,metadata)
select
  'CRM', at.id::text, at.cliente_id, c.nome,
  'PRESENTE_OPERACIONAL','ACAO_COMERCIAL',upper(coalesce(at.status,'REGISTRADA')),
  coalesce(at.data,at.data_atividade::date,at.created_at::date), at.usuario_id,
  case when at.cliente_id is not null then 'CLIENTE_ID' else 'SEM_RECONCILIACAO' end,
  case when at.cliente_id is not null then 1 else 0 end,
  jsonb_build_object('tipo',at.tipo,'titulo',at.titulo,'descricao',at.descricao,'oportunidade_id',at.oportunidade_id)
from public.cti_atividades at
left join public.clientes c on c.id=at.cliente_id
where at.arquivado_em is null and coalesce(at.registro_teste,false)=false
on conflict (fonte,fonte_registro_id,evento) do update set
  cliente_id=excluded.cliente_id, cliente_nome=excluded.cliente_nome, temporalidade=excluded.temporalidade,
  estado_comercial=excluded.estado_comercial, data_evento=excluded.data_evento, responsavel_id=excluded.responsavel_id,
  metodo_reconciliacao=excluded.metodo_reconciliacao, confianca=excluded.confianca, metadata=excluded.metadata, updated_at=now();

-- FUNIL: oportunidades possuem passado encerrado e futuro/backlog em uma única fonte canônica.
insert into public.cti_evidencias_comerciais
  (fonte,fonte_registro_id,cliente_id,cliente_nome,temporalidade,evento,estado_comercial,data_evento,valor,responsavel_id,metodo_reconciliacao,confianca,metadata)
select
  'FUNIL', o.id::text, o.cliente_id, c.nome,
  case when upper(coalesce(o.status,'')) in ('GANHO','PERDIDO','ENCERRADO','FECHADO') then 'PASSADO_CONFIRMADO' else 'EM_CURSO_BACKLOG' end,
  'OPORTUNIDADE',upper(coalesce(o.status,'ABERTA')),
  coalesce(o.data_fechamento_real::date,o.data_fechamento_prevista::date,o.data_abertura::date,o.created_at::date),
  o.valor_estimado,o.responsavel_id,
  case when o.cliente_id is not null then 'CLIENTE_ID' else 'SEM_RECONCILIACAO' end,
  case when o.cliente_id is not null then 1 else 0 end,
  jsonb_build_object('titulo',o.titulo,'origem',o.origem,'probabilidade',o.probabilidade,'data_abertura',o.data_abertura,'data_fechamento_prevista',o.data_fechamento_prevista,'data_fechamento_real',o.data_fechamento_real)
from public.cti_oportunidades o
left join public.clientes c on c.id=o.cliente_id
where o.arquivado_em is null and coalesce(o.registro_teste,false)=false
on conflict (fonte,fonte_registro_id,evento) do update set
  cliente_id=excluded.cliente_id, cliente_nome=excluded.cliente_nome, temporalidade=excluded.temporalidade,
  estado_comercial=excluded.estado_comercial, data_evento=excluded.data_evento, valor=excluded.valor,
  responsavel_id=excluded.responsavel_id, metodo_reconciliacao=excluded.metodo_reconciliacao,
  confianca=excluded.confianca, metadata=excluded.metadata, updated_at=now();

-- Vendas operacionais: passado confirmado, quando houver.
insert into public.cti_evidencias_comerciais
  (fonte,fonte_registro_id,cliente_id,cliente_nome,temporalidade,evento,estado_comercial,data_evento,equipamento,valor,metodo_reconciliacao,confianca,metadata)
select
  'VENDA', v.id::text, v.cliente_id, c.nome,
  'PASSADO_CONFIRMADO','VENDA_CONFIRMADA','GANHO',v.data_venda,v.equipamento_codigo,v.valor,
  case when v.cliente_id is not null then 'CLIENTE_ID' else 'SEM_RECONCILIACAO' end,
  case when v.cliente_id is not null then 1 else 0 end,
  jsonb_build_object('tipo_venda',v.tipo_venda,'pedido_id',v.pedido_id,'oportunidade_id',v.oportunidade_id,'observacao',v.observacao)
from public.vendas v
left join public.clientes c on c.id=v.cliente_id
where v.arquivado_em is null and coalesce(v.registro_teste,false)=false
on conflict (fonte,fonte_registro_id,evento) do update set
  cliente_id=excluded.cliente_id, cliente_nome=excluded.cliente_nome, temporalidade=excluded.temporalidade,
  estado_comercial=excluded.estado_comercial, data_evento=excluded.data_evento, equipamento=excluded.equipamento,
  valor=excluded.valor, metodo_reconciliacao=excluded.metodo_reconciliacao, confianca=excluded.confianca,
  metadata=excluded.metadata, updated_at=now();

comment on table public.cti_evidencias_comerciais is
'Camada canônica de evidências do CTI. Não substitui ANFIR, CRM, Funil ou Vendas; conecta fatos da mesma jornada comercial mantendo origem e temporalidade.';
