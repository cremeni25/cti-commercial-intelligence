# PR 79 — ordem segura de execução no Supabase

Execute os arquivos abaixo manualmente no SQL Editor, um por vez, aguardando `Success` antes de avançar.

1. `20260730_oportunidades_itens_propostas_pedidos.sql`
2. `20260730_catalogo_comercial_precos.sql`
3. `20260730_catalogo_comercial_precos_correcao.sql`
4. `20260730_modelos_propostas_recebidos.sql`
5. `20260730_variantes_modelos_proposta.sql`

## Regras de validação

Após os cinco arquivos, confirme:

```sql
select codigo, nome_comercial, preco_cheio
from public.cti_catalogo_equipamentos e
left join public.cti_tabela_precos p
  on p.equipamento_codigo = e.codigo
 and p.tabela_codigo = 'TABELA-INICIAL-2026'
where e.codigo in (
  'CITIMAX-500', 'CITIMAX-500-AE',
  'CITIMAX-D6', 'CITIMAX-D6-AE',
  'CITIMAX-D7', 'CITIMAX-D7-AE'
)
order by e.codigo;
```

Valores esperados:

- CITIMAX 500: R$ 27.000,00
- CITIMAX 500AE: R$ 41.000,00
- CITIMAX D6: R$ 28.000,00
- CITIMAX D6AE: R$ 43.000,00
- CITIMAX D7: R$ 29.000,00
- CITIMAX D7AE: R$ 45.000,00

A linha Trailer permanece no catálogo e na tabela de preços, com templates documentais pendentes de recebimento.
