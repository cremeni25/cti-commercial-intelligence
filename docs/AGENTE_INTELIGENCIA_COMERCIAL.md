# Agente de Inteligência Comercial e registro de módulos

## O que é

O agente lê o núcleo comercial (oportunidades, propostas, pedidos e atividades), já filtrado pelo escopo do usuário, e devolve **uma leitura única e priorizada**, chamada *briefing*. O briefing responde a cinco perguntas:

| Pergunta | Bloco do briefing |
|---|---|
| Como estou? | `indicadores`: no máximo 5 (pipeline aberto, ações para hoje, valor em risco, prontos para fechar, ganhos no mês) |
| O que faço primeiro? | `prioridades`: uma por negócio, ranqueadas por gravidade + valor + tempo parado, cada uma com explicação, evidência e próximo passo |
| Onde estou perdendo dinheiro? | `riscos` |
| Como está o funil? | `pipeline` por etapa |
| Posso confiar nos números? | `qualidade`: índice de 0 a 100 e negócios sem valor, sem previsão, sem cliente ou sem equipamento |

O agente **somente lê**: não altera registros e não depende de modelo de linguagem, por isso o resultado é auditável e testável. A IA Comercial conversacional recebe os mesmos sinais como a fonte `prioridades_comerciais` do universo de dados. Perguntas como "por onde começo hoje?" usam exatamente a leitura exibida na tela.

## Onde aparece

- **Portal:** `/central`, Central de Inteligência (primeiro item do menu). A gestão pode alternar entre a equipe consolidada e um responsável específico.
- **App de campo:** card "Prioridades do agente" na tela inicial, abaixo das ações principais, e leitura completa em `/crm-app/prioridades`. Se a leitura falhar, o card simplesmente não aparece e o restante do app continua igual.
- **API:** `GET /crm-seguro/inteligencia/briefing?responsavel_id=&limite=` e `GET /crm-seguro/plataforma/modulos`.

## Resolver direto da prioridade

Cada prioridade traz ações que resolvem o item sem sair da lista:

| Prioridade | Ações | Por onde passa |
|---|---|---|
| Negócio (parado, vencido, sem retorno, sem próximo passo, pronto para fechar) | **Agendar próximo passo**: tipo, data e assunto | `POST /crm-seguro/atividades`, o mesmo fluxo seguro do app (escopo, responsável e histórico) |
| Atividade (follow-up atrasado, compromisso de hoje) | **Concluir** ou **Reagendar** | `PUT /crm-seguro/atividades/{id}/concluir` e `PUT /crm-seguro/atividades/{id}` |
| Qualquer alerta | **Não se aplica** (esconde por 30 dias) ou **Adiar até** uma data (máximo de 60 dias), sempre com motivo | `POST /crm-seguro/inteligencia/feedback` |

"Não se aplica" e "adiar" **não apagam nada**: só escondem aquele alerta daquele negócio até o prazo. Depois disso, o alerta volta se a situação continuar. Cada ajuste fica registrado com autor e motivo. A gestão vê em `GET /crm-seguro/inteligencia/aprendizado` quais alertas a equipe mais dispensa e por quê. Exemplo: se "negócio parado" for dispensado muitas vezes com "alerta cedo demais", é sinal de aumentar o limiar de 21 dias.

**Ativação no banco:** o ajuste usa a tabela `cti_inteligencia_feedback` (migração `supabase/migrations/20261107120000_cti_inteligencia_feedback.sql`). Até ela ser aplicada, agendar, concluir e reagendar funcionam normalmente; o "não se aplica" responde com um aviso claro e nada quebra.

## Catálogo de produtos

- Portal em `/catalogo` e app em `/crm-app/catalogo`: busca por modelo, linha ou compressor; filtro TR/DT/DD; materiais por modelo e por linha; botão **Copiar para WhatsApp**, que gera o resumo do modelo com o link do material.
- O preço de tabela vigente aparece só para a gestão e para quem visualiza ou emite propostas.
- Os materiais vêm do Linktree oficial (`@carriertransicoldbrasil`) e ficam em `backend/data/catalogo_materiais.json`. Para incluir ou alterar um material, edite o arquivo:
  - `linhas` (`TRAILER`, `DIESEL TRUCK`, `DIRECT DRIVE` ou `TR`/`DT`/`DD`) liga o material à linha;
  - `termos` (trecho do nome do modelo) ou `equipamentos` (código do catálogo) ligam o material a um modelo.

  Um material de modelo que não encontra o modelo no catálogo aparece na linha. Material sem linha nem modelo aparece em "Materiais de divulgação". Somente links `https://` são aceitos, e o teste `test_arquivo_de_materiais_versionado_e_valido` impede um material inválido.

## Regras de escopo

Seguem a regra oficial do CRM seguro: o Master e o Diretor com acesso total veem a equipe e podem filtrar por responsável. Todos os demais perfis veem apenas a própria carteira; se tentarem filtrar outro responsável, recebem 403. Na IA conversacional vale a regra já aplicada pela IA: somente o ADMIN_MASTER tem visão consolidada. Links de prioridades que o perfil não pode abrir são exibidos como texto, sem link.

## Sinais nativos

| Código | Categoria | Regra (limiares em `provedores.LIMIARES`, ajustáveis por `CTI_INTELIGENCIA_*`) |
|---|---|---|
| `FOLLOWUP_ATRASADO` | ação | atividade pendente com data passada (alta a partir de 7 dias) |
| `AGENDA_HOJE` | ação | atividade pendente para hoje |
| `SEM_PROXIMO_PASSO` | ação | negócio aberto sem atividade futura |
| `FECHAMENTO_VENCIDO` | risco | previsão de fechamento no passado e negócio aberto |
| `PROPOSTA_SEM_RETORNO` | risco | proposta vigente sem movimento há 7 dias ou mais |
| `OPORTUNIDADE_PARADA` | risco | sem movimento há 21 dias ou mais (alta a partir de 45) |
| `PEDIDO_SEM_MOVIMENTO` | risco | pedido/dossiê/Carrier sem movimento há 14 dias ou mais |
| `PRONTO_PARA_FECHAR` | oportunidade | probabilidade de 70% ou mais e fechamento em até 30 dias |

Negócios encerrados (ganho, perdido, cancelado, faturado, encerrado) nunca recebem recomendação. "Hoje" é a data civil de Brasília (UTC−3).

## Como adicionar um módulo novo (ex.: Treinamentos, Catálogo)

1. **Declare o módulo** em `backend/core/modulos_plataforma.py` (`status="planejado"`). Ele já aparece na Central como "Em breve".
2. **Crie as telas** e informe `rota_web`/`rota_app`, mudando o status para `beta` e depois `ativo`. O teste `test_modulos_plataforma.py` falha se uma rota declarada não existir no frontend.
3. **Se o módulo gerar inteligência**, registre um provedor de sinais:

```python
from services.inteligencia_comercial import Sinal, registrar_provedor

@registrar_provedor("treinamentos", modulo="treinamentos")
def recomendar_trilhas(contexto):
    # contexto.oportunidades, contexto.atividades, contexto.hoje, contexto.extras
    return [Sinal(codigo="TREINAMENTO_RECOMENDADO", categoria="acao", severidade="baixa", ...)]
```

O sinal entra automaticamente no briefing, na Central, no app e na IA. Um provedor com defeito é isolado: aparece em `provedores` com `ok=false` e os demais sinais continuam sendo entregues.

## Evolução sugerida

- **Catálogo de produtos:** criar a vitrine de consulta para a equipe (hoje a administração fica em Configurações) e um provedor que sinalize itens sem correspondência no catálogo.
- **Treinamentos comerciais:** trilhas por linha (TR/DT/DD) e etapa, com um provedor que recomende trilhas a partir dos padrões de perda e dos negócios parados de cada vendedor.
- **Narrativa por IA:** gerar o texto do briefing por modelo de linguagem, sempre a partir dos sinais determinísticos (nunca em substituição a eles).
