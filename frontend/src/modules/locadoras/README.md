# Módulo — Locadoras

## Objetivo

Responsável pela inteligência operacional,
territorial, comercial e estratégica
das locadoras vinculadas ao CTI.

---

# Estrutura Oficial

locadoras/

## ai/
Camada de inteligência contextual e operacional.

Responsável por:
- insights
- recomendações
- criticidade
- leitura territorial
- inteligência estratégica

Nunca deve renderizar UI.

---

## components/
Camada visual do domínio.

Responsável por:
- tabelas
- drawers
- filtros
- cards
- renderização visual

Nunca deve conter:
- regras complexas
- scoring
- inteligência operacional
- transformações pesadas

---

## data/
Mocks e fontes temporárias.

Responsável por:
- mocks
- seeds
- dados temporários
- dados estáticos

---

## services/
Engine operacional do domínio.

Responsável por:
- ordenação
- scoring
- cálculos
- transformações
- classificação
- engines reutilizáveis

Toda regra operacional deve viver aqui.

---

## types/
Tipagens oficiais do domínio.

Responsável por:
- interfaces
- contratos
- entidades
- tipos reutilizáveis

---

# Regras Oficiais

- Nunca misturar UI com engine
- Nunca colocar lógica operacional em components/
- Nunca colocar IA em page.tsx
- Toda inteligência deve ser desacoplada
- Toda transformação deve ser reutilizável
- Toda regra operacional deve viver em services/

---

# Status

Módulo blueprint oficial do CTI.