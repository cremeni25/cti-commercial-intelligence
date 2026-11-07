# Revisão CTI — 07/11/2026

Base: `ded5a74`. Objetivo: simplificar a devolutiva dos dados, organizar a inteligência por meio de um agente e preparar a plataforma para novos módulos, sem alterar o fluxo comercial em operação (cliente → interação → oportunidade → proposta → pedido → venda).

## Falhas confirmadas e corrigidas

| Achado | Efeito | Correção |
|---|---|---|
| `nucleo_comercial` devolvia probabilidade `1.0` (escala 0–1) para PEDIDO/DOSSIÊ/CARRIER/FATURADO, mas calculava `valor_ponderado = valor × prob / 100` | O valor ponderado dos negócios em pedido saía com 1% do valor real; Forecast e Funil Carrier somavam esse valor | Escala única de 0 a 100 (`100.0`), com teste de regressão |
| A página Forecast exibia a probabilidade como `p × 100` | Um negócio de 50% aparecia como "5000%" | Normalização igual à das demais telas (`p ≤ 1 ? p×100 : p`) |

## Novidades (aditivas)

- **Agente de Inteligência Comercial** (`backend/services/inteligencia_comercial/`): briefing priorizado, explicado e auditável; sinais organizados por provedor e por módulo. Ver `docs/AGENTE_INTELIGENCIA_COMERCIAL.md`.
- **Central de Inteligência** (`/central`): primeiro item do menu do portal, com uma tela única de prioridades, riscos, funil, confiabilidade dos dados e módulos.
- **Prioridades no app:** card na tela inicial, abaixo das ações principais, e a tela `/crm-app/prioridades`.
- **IA Comercial:** passa a ler a fonte `prioridades_comerciais`, com o mesmo raciocínio da Central e sem nova ferramenta nem mudança nas guardas existentes.
- **Registro de módulos** (`backend/core/modulos_plataforma.py`): fonte única do que a plataforma faz, com Catálogo (em evolução) e Treinamentos (em breve) já declarados.
- **Repositório:** `backend/.venv` (6.018 arquivos, ligado a um Python de Codespace inexistente) foi retirado do versionamento, em commit próprio. O Render instala a partir de `requirements.txt`.

## Evidências locais

- Backend: **870 aprovados**, 1 ignorado (linha de base: 832), incluindo 38 testes novos (regras, escopo HTTP, isolamento de falhas, IA e rotas de módulos).
- Frontend: TypeScript e build de produção aprovados; lint dos arquivos alterados sem avisos.
- Chromium real com build Next e APIs sintéticas: `central-browser.mjs` (6 verificações, incluindo backend antigo/404 sem quebrar a tela inicial e data civil brasileira) e `crm-home-browser.mjs` (7 verificações já existentes, todas mantidas).

Nenhum teste usou contas reais ou dados de produção. Após o deploy, conferir com sessão autorizada: a leitura de um vendedor (somente a própria carteira), a visão consolidada do Master e a calibração dos limiares com a gestão comercial.

## Ordem de publicação

O frontend tolera um backend anterior: sem o endpoint, o card do app não aparece e a Central mostra um aviso. O ideal é publicar o backend (Render) antes ou junto do frontend (Vercel).
