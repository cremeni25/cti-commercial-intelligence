# Checklist operacional

- [x] Entrada única por Importar Dados.
- [x] ANFIR continua no fluxo próprio.
- [x] Fonte não ANFIR é preservada antes de qualquer interpretação.
- [x] Interpretação estrutural e semântica automáticas.
- [x] Reconciliação automática apenas para candidata COMERCIAL.
- [x] Promoção automática somente quando a natureza é exclusivamente CRM_CADASTRAL e sem conflitos semânticos.
- [x] Merge por CNPJ sem sobrescrita de divergências.
- [x] Divergências retornam à Governança para decisão Master.
- [x] Evento cti-upload-finalizado é emitido após promoção segura.
