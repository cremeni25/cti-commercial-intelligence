-- CTI 2026-08-30 — correção territorial homologada pelo negócio.
-- Taboão da Serra e Embu das Artes: Região Sul.
-- Cajamar e Franco da Rocha: Região Oeste.
-- Jundiaí, Itupeva e Cabreúva: Interior, fora da divisão Leste/Oeste do DDD 011.

-- Desativa classificações anteriores que não representam mais a regra comercial.
update public.cti_territorio_regras
set ativo = false, updated_at = now()
where ddd = '011'
  and regra_tipo = 'CIDADE'
  and valor in ('TABOAO DA SERRA','EMBU DAS ARTES','JUNDIAI','ITUPEVA','CABREUVA');

-- Mantém/explicita as classificações corretas.
insert into public.cti_territorio_regras
  (ddd,codigo_regional,nome_humano,regra_tipo,valor,prioridade,origem,ativo)
values
  ('011','REGIAO SUL','Região Sul','CIDADE','TABOAO DA SERRA',10,'REGRA_COMERCIAL_HOMOLOGADA',true),
  ('011','REGIAO SUL','Região Sul','CIDADE','EMBU DAS ARTES',10,'REGRA_COMERCIAL_HOMOLOGADA',true),
  ('011','REGIAO 02','Região Oeste','CIDADE','CAJAMAR',10,'REGRA_COMERCIAL_HOMOLOGADA',true),
  ('011','REGIAO 02','Região Oeste','CIDADE','FRANCO DA ROCHA',10,'REGRA_COMERCIAL_HOMOLOGADA',true),
  ('011','INTERIOR','Interior','CIDADE','JUNDIAI',10,'REGRA_COMERCIAL_HOMOLOGADA',true),
  ('011','INTERIOR','Interior','CIDADE','ITUPEVA',10,'REGRA_COMERCIAL_HOMOLOGADA',true),
  ('011','INTERIOR','Interior','CIDADE','CABREUVA',10,'REGRA_COMERCIAL_HOMOLOGADA',true)
on conflict (ddd,codigo_regional,regra_tipo,valor)
do update set nome_humano=excluded.nome_humano, prioridade=excluded.prioridade,
              origem=excluded.origem, ativo=true, updated_at=now();

-- Reclassifica cadastros já existentes. Preserva contas diretas Master:
-- muda somente o território geográfico (sub_regiao), nunca a responsabilidade comercial efetiva.
update public.clientes
set sub_regiao = case
  when upper(unaccent(coalesce(cidade,''))) in ('TABOAO DA SERRA','EMBU DAS ARTES') then 'REGIAO SUL'
  when upper(unaccent(coalesce(cidade,''))) in ('CAJAMAR','FRANCO DA ROCHA') then 'REGIAO 02'
  when upper(unaccent(coalesce(cidade,''))) in ('JUNDIAI','ITUPEVA','CABREUVA') then 'INTERIOR'
  else sub_regiao
end,
updated_at = now()
where upper(unaccent(coalesce(cidade,''))) in
  ('TABOAO DA SERRA','EMBU DAS ARTES','CAJAMAR','FRANCO DA ROCHA','JUNDIAI','ITUPEVA','CABREUVA');
