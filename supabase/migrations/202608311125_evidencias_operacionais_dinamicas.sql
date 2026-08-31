-- cti_atividades, cti_oportunidades e vendas são views canônicas e variam em tempo real.
-- O motor transversal passa a lê-las dinamicamente; evita snapshot operacional obsoleto.
delete from public.cti_evidencias_comerciais where fonte in ('CRM','FUNIL','VENDA');

comment on table public.cti_evidencias_comerciais is
'Índice persistente de evidências ANFIR reconciliadas. CRM, Funil e Vendas são lidos dinamicamente pelo motor transversal para não gerar snapshots operacionais obsoletos.';
