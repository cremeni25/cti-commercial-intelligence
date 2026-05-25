# CTI — Operational Rules

## Regras Oficiais da Plataforma

Estas regras são obrigatórias para qualquer evolução do CTI.

---

# 1. Separação obrigatória

## app/
Nunca conter:
- engine
- IA
- scoring
- cálculos complexos
- transformações pesadas

app/ é apenas camada de páginas e rotas.

---

# 2. Modules

Cada domínio deve conter:

- ai/
- components/
- data/
- services/
- types/
- README.md
- index.ts

---

# 3. Services

Toda regra operacional deve viver em:
- services/
- core/

Nunca em:
- components/
- pages/
- drawers/
- tables/

---

# 4. IA

Toda IA deve ser desacoplada.

IA nunca deve:
- renderizar UI
- depender de componentes
- depender de páginas

---

# 5. Components

Components devem:
- renderizar
- receber props
- exibir dados

Components nunca devem:
- calcular score
- classificar entidades
- aplicar regras complexas

---

# 6. Core

Core é responsável por:
- AI global
- CRM
- scoring
- analytics
- database
- auth
- APIs

Core nunca deve renderizar UI.

---

# 7. Shared

Shared deve conter apenas:
- reutilização transversal
- hooks globais
- componentes globais
- utils
- tipagens compartilhadas

---

# 8. Barrel Pattern

Todo módulo deve possuir:
- index.ts

Somente contratos públicos devem ser exportados.

---

# 9. Tipagem

Toda entidade deve possuir:
- interface oficial
- tipagem isolada

Nunca usar:
- any
- tipagem implícita crítica

---

# 10. Crescimento

Toda nova feature deve:
1. respeitar arquitetura
2. respeitar domínio
3. respeitar separação
4. evitar duplicação
5. preservar escalabilidade

---

# Status

Manifesto operacional oficial do CTI.