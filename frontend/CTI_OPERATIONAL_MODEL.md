# CTI — Operational Model

## Modelo Operacional Oficial

Este documento define as entidades oficiais,
fluxos operacionais e contratos corporativos do CTI.

Nenhuma IA, dashboard, scoring,
analytics ou pipeline pode operar
fora destas definições.

---

# 1. CLIENTE

Entidade operacional principal.

Representa:
- transportadora
- operador logístico
- frigorífico
- embarcador
- operador de frota

Nunca:
- produto
- montadora
- fabricante
- região
- observação textual

## Campos oficiais

- id
- razao_social
- nome_fantasia
- cnpj
- cidade
- estado
- segmento
- score
- status
- origem
- created_at

---

# 2. OPORTUNIDADE

Representa potencial comercial identificado.

## Campos oficiais

- id
- cliente_id
- produto
- montadora
- implementadora
- concorrente
- valor
- status
- probabilidade
- origem
- created_at

---

# 3. IMPLEMENTADORA

OEM operacional vinculada à cadeia refrigerada.

## Campos oficiais

- id
- nome
- cidade
- estado
- market_share
- score
- status
- concorrencia
- created_at

---

# 4. PRODUTO

Linha operacional do equipamento.

## Valores oficiais

- TR
- DT
- DD

Nunca utilizar:
- nomes livres
- variações sem normalização

---

# 5. CONCORRENTE

Fabricante concorrente operacional.

## Valores controlados

- THERMO KING
- FRIGOKING
- THERMOSTAR
- RODOFRIO
- THERMOFLEX

---

# 6. MONTADORA

Fabricante do caminhão.

## Exemplos

- VOLVO
- SCANIA
- MERCEDES
- VW
- IVECO

---

# 7. PIPELINE

Fluxo operacional oficial.

## Fluxo válido

UPLOAD
→ NORMALIZAÇÃO
→ VALIDAÇÃO
→ CLASSIFICAÇÃO
→ PERSISTÊNCIA
→ ANALYTICS
→ IA
→ DASHBOARD

Nenhum dado pode pular etapas.

---

# 8. DADOS BRUTOS

Dados originais nunca devem ser apagados.

Devem possuir:
- hash
- origem
- arquivo
- aba
- timestamp
- rastreabilidade

---

# 9. IA

IA nunca define verdade operacional.

IA:
- sugere
- interpreta
- classifica
- recomenda

Validação oficial pertence ao pipeline corporativo.

---

# 10. SCORING

Scoring deve ser:
- reproduzível
- auditável
- rastreável
- explicável

Nunca puramente heurístico.

---

# 11. DASHBOARDS

Dashboards nunca devem:
- interpretar dados
- corrigir semântica
- aplicar heurística crítica

Dashboards apenas consomem:
- dados validados
- entidades oficiais
- métricas oficiais

---

# 12. GOVERNANÇA

Toda nova funcionalidade deve respeitar
- contrato operacional
- taxonomia oficial
- separação de responsabilidade
- rastreabilidade
- auditabilidade

---

# Status

Contrato operacional oficial do CTI.