# CTI — Commercial Technology & Intelligence

## Arquitetura Oficial do Projeto

O CTI é uma plataforma enterprise modular de inteligência comercial,
territorial, operacional e estratégica.

A arquitetura foi desenhada para:
- escalabilidade global
- modularização operacional
- IA multiagente
- CRM corporativo
- scoring inteligente
- analytics operacional
- integração Supabase
- APIs enterprise
- automação operacional

---

# Estrutura Oficial

src/

## app/
Camada de rotas e páginas do Next.js.

Responsável apenas por:
- rotas
- composição
- renderização macro

Não deve conter:
- lógica operacional
- regras de negócio
- inteligência
- scoring
- transformações complexas

---

## modules/
Domínios operacionais independentes do CTI.

Cada domínio possui:

- ai/
- components/
- data/
- services/
- types/
- README.md

Domínios atuais:
- implementadoras
- transportadoras
- locadoras
- oportunidades

Cada módulo é um microecossistema operacional.

---

## core/
Núcleo corporativo global do CTI.

Responsável por:
- AI global
- scoring global
- CRM
- database
- auth
- analytics
- APIs corporativas

O core nunca deve conter renderização visual.

---

## shared/
Componentes e estruturas compartilhadas.

Responsável por:
- UI reutilizável
- hooks compartilhados
- utilitários
- tipagens globais

---

## services/
Integrações globais e gateways externos.

---

# Padrão Oficial

## UI
Componentes React renderizam apenas.

## ENGINE
Toda lógica operacional deve viver em:
- services/
- core/

## IA
Toda inteligência contextual deve viver em:
- ai/

## MOCKS
Toda fonte mock deve viver em:
- data/

## TIPOS
Toda tipagem deve viver em:
- types/

---

# Diretrizes Oficiais

- Nunca misturar UI com engine operacional
- Nunca colocar lógica complexa em page.tsx
- Nunca duplicar regras entre módulos
- Sempre separar domínio e núcleo global
- Toda IA deve ser desacoplada da renderização
- Toda engine deve ser reutilizável
- Toda estrutura deve ser previsível

---

# Status Atual

Arquitetura enterprise modular oficialmente consolidada.