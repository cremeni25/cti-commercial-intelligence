# Etapa 19.2 — correção da aprovação e convite

A correção registra no backend a etapa exata de falha do fluxo de aprovação (`envio do convite`, `criação do perfil CTI` ou `atualização da solicitação`), mantém rollback do usuário Auth quando necessário e substitui o valor textual `now()` por timestamp UTC ISO válido.

A solicitação permanece pendente quando a aprovação não é concluída.
