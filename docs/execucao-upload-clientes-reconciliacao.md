# Upload inteligente de listas cadastrais

O CTI utiliza a mesma porta de entrada de `Importar Dados` para listas de clientes. Arquivos não reconhecidos como ANFIR permanecem preservados na Governança Universal e seguem, quando elegíveis, por interpretação, semântica, staging e reconciliação.

Quando a fonte é classificada como `COMERCIAL`, o destino é `CANDIDATO_OPERACIONAL_VALIDACAO`, a natureza é exclusivamente `CRM_CADASTRAL` e não há conflito semântico, o upload executado por ADMIN_MASTER aprova a reconciliação e solicita a promoção pelo adaptador canônico de CLIENTE.

A promoção usa CNPJ como identificador prioritário, enriquece apenas campos vazios e bloqueia qualquer divergência de negócio. Uma divergência retorna o item para reconciliação e não substitui silenciosamente o cadastro existente.

Fontes mistas, ambíguas ou com conflitos permanecem em staging e são encaminhadas à Governança de Fontes para decisão Master.
