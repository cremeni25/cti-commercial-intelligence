# Core Database

Camada oficial de persistência do CTI.

Responsável por:
- Supabase
- conexões
- persistência
- acesso global ao banco
- camada de dados corporativa

Nunca deve:
- renderizar UI
- conter lógica visual
- depender de componentes

Toda persistência do CTI deve passar por esta camada.