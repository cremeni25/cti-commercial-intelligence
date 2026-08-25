from routers.pedidos_documentos_oficiais_router import _protocolo_ja_cobre_documento


def proposta_com_sha(sha: str | None):
    snapshot = {}
    if sha:
        snapshot["arquivo_documento"] = {"sha256": sha, "path": "arquivo.docx"}
    return {"snapshot_dados": snapshot}


def protocolo_com_sha(sha: str):
    return {"tipo": "ENVIO_PEDIDO_OFICIAL", "status_envio": "ENVIADO", "anexo": {"sha256": sha}}


def test_mesmo_sha_permanece_idempotente():
    assert _protocolo_ja_cobre_documento(protocolo_com_sha("abc"), proposta_com_sha("abc")) is True


def test_revisao_sem_documento_final_ainda_nao_esta_coberta():
    assert _protocolo_ja_cobre_documento(protocolo_com_sha("abc"), proposta_com_sha(None)) is False


def test_novo_sha_pode_ser_reenviado_sem_apagar_protocolo_anterior():
    assert _protocolo_ja_cobre_documento(protocolo_com_sha("abc"), proposta_com_sha("def")) is False
