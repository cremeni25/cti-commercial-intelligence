-- Amplia a reconciliação ANFIR somente quando nome normalizado + cidade normalizada
-- identificam exatamente um cliente no cadastro CTI. Não altera a fonte ANFIR.
with clientes_norm as (
  select
    id::text as id,
    upper(trim(regexp_replace(translate(coalesce(nome,''),'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç','AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'),'\s+',' ','g'))) as nome_norm,
    upper(trim(regexp_replace(translate(coalesce(cidade,''),'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç','AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'),'\s+',' ','g'))) as cidade_norm
  from public.clientes
), unicos as (
  select nome_norm,cidade_norm,min(id)::uuid as cliente_id
  from clientes_norm
  where nome_norm<>'' and cidade_norm<>''
  group by nome_norm,cidade_norm
  having count(*)=1
), anf as (
  select
    id::text as fonte_registro_id,
    upper(trim(regexp_replace(translate(coalesce(cliente,''),'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç','AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'),'\s+',' ','g'))) as nome_norm,
    upper(trim(regexp_replace(translate(coalesce(cidade,''),'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç','AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'),'\s+',' ','g'))) as cidade_norm
  from public.cti_anfir
  where coalesce(ativo,true)=true
)
update public.cti_evidencias_comerciais e
set cliente_id=u.cliente_id,
    metodo_reconciliacao='NOME_CIDADE_EXATOS_UNICOS',
    confianca=0.90,
    updated_at=now()
from anf a join unicos u using(nome_norm,cidade_norm)
where e.fonte='ANFIR'
  and e.fonte_registro_id=a.fonte_registro_id
  and e.cliente_id is null;
