# CTI — Glossário Semântico PT / EN / ES

Este arquivo define conceitos, não traduções literais. O significado operacional do CTI é a fonte de verdade; cada idioma expressa esse conceito com terminologia natural de CRM, vendas, refrigeração de transporte e gestão comercial.

| Conceito CTI | PT-BR | EN | ES (LATAM) | Diretriz |
|---|---|---|---|---|
| painel de gestão consolidada | Dashboard Executivo | Executive Dashboard | Panel Ejecutivo | Não usar tradução literal de "dashboard" quando a função for executiva. |
| registro cronológico do negócio | Histórico Comercial | Commercial History | Historial Comercial | Diferente de audit log técnico. |
| inteligência aplicada à rotina de vendas | IA Comercial | Sales AI | IA Comercial | Em inglês, "Sales AI" comunica a função com naturalidade. |
| empresa cliente no CRM de campo | Cliente | Account | Cliente | Em inglês B2B, Account é o conceito de CRM; customer é reservado a contextos transacionais. |
| empresa cadastrada no núcleo mestre | Empresa | Company | Empresa | Cadastro empresarial amplo, não necessariamente cliente ativo. |
| empresa que implementa/carroça o veículo | Implementadora | Body Builder | Carrocero | Terminologia de mercado, não tradução palavra por palavra. |
| negócio comercial em potencial | Oportunidade | Opportunity | Oportunidad | Entidade-pai do negócio no CTI. |
| documento comercial de oferta | Proposta | Proposal | Propuesta | Não confundir com quotation quando o objeto inclui documento, versões e aceite. |
| execução após aceite comercial | Pedido | Order | Pedido | Entidade operacional posterior à proposta aceita. |
| negócio realizado/concluído | Venda | Sale | Venta | Representa realizado, não oportunidade aberta. |
| ação comercial registrada | Atividade | Activity | Actividad | Inclui ligação, reunião, visita, retorno e próxima ação. |
| visita comercial em campo | Visita | Field Visit | Visita | Em inglês, Field Visit evita ambiguidade com visita de site genérica. |
| cadastros estruturantes | Cadastros | Master Data | Datos maestros | Conceito administrativo de dados mestres. |
| governança de origem dos dados | Governança de Fontes | Data Source Governance | Gobernanza de Fuentes | Não simplificar para Sources. |

## Regras institucionais

1. PT-BR é a referência funcional atual, mas não é uma frase-mãe para tradução literal.
2. Dados livres do usuário — nomes, razão social, observações, histórico digitado, endereços e textos de negociação — permanecem no idioma original do registro.
3. Status técnicos armazenados no banco permanecem canônicos; a interface localiza apenas a apresentação.
4. Datas, números e moedas devem usar `Intl` conforme o idioma selecionado, sem alterar o valor armazenado.
5. CTI Web e CRM App consomem o mesmo catálogo semântico e a mesma preferência de idioma.
6. Novos textos de interface devem entrar por chave semântica antes de serem exibidos em uma tela.
7. O espanhol adotado é neutro para LATAM (`es-419`); evitar espanhol excessivamente regional.
8. O inglês adotado é corporativo B2B e natural para CRM/sales operations; evitar traduções artificiais do português.
