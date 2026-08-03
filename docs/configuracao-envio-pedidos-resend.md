# Configuração do envio transacional de pedidos

O CTI usa o serviço Resend exclusivamente no backend. Nenhuma chave deve ser exposta no frontend ou versionada no repositório.

## Variáveis no Render

- `RESEND_API_KEY`: chave secreta criada no painel Resend.
- `CTI_EMAIL_FROM`: remetente verificado, recomendado: `CTI Pedidos <pedidos@send.cti-intelligence.com>`.
- `CTI_EMAIL_REPLY_TO`: endereço que receberá respostas, por exemplo o e-mail comercial responsável.

## Domínio

Cadastrar `send.cti-intelligence.com` no Resend e publicar na UOL Host somente os registros SPF e DKIM fornecidos pelo provedor. Não alterar as entradas atuais de `app.cti-intelligence.com`, domínio raiz, `painel` ou `sac`.

## Comportamento seguro

Enquanto `RESEND_API_KEY` e `CTI_EMAIL_FROM` não estiverem configurados, o botão de envio permanece bloqueado no CRM App. Os destinatários continuam registrados e o pedido permanece com status `ENVIO PENDENTE`.

Após envio confirmado pelo provedor, o CTI registra no dossiê do pedido:

- status `ENVIADO`;
- data e hora;
- provedor;
- protocolo externo (`message_id`);
- remetente;
- destinatários;
- assunto enviado.

Uma segunda chamada de envio para o mesmo pedido retorna o protocolo já registrado e não dispara nova mensagem.
