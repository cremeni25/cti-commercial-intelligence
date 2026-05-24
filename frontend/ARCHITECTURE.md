# CTI — Arquitetura Oficial

## Estrutura Oficial

src/
  app/
  core/
  modules/
  shared/

---

## app

Responsável por:
- rotas
- páginas
- navegação
- layouts

Não conter:
- regra de negócio
- IA
- scoring
- acesso direto ao banco

---

## core

Responsável por:
- IA global
- CRM
- scoring
- APIs
- banco
- analytics
- autenticação

---

## modules

Responsável por:
- domínios operacionais
- componentes do domínio
- datasets
- filtros
- tabelas
- lógica específica

---

## shared

Responsável por:
- componentes reutilizáveis
- hooks globais
- helpers
- utils
- types globais

---

## Regras Oficiais do CTI

1. Não criar lógica pesada dentro de app
2. Não duplicar componentes
3. Não misturar IA com domínio
4. Não acessar banco diretamente pelas páginas
5. Toda IA deve nascer em core/ai
6. Todo scoring deve nascer em core/scoring
7. CRM deve ser centralizado
8. Domínios operacionais devem permanecer isolados