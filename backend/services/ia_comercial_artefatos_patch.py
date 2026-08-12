from __future__ import annotations

import hashlib
import unicodedata
from typing import Any

from . import ia_comercial_agente_crm as _agente
from .ia_comercial_artefatos import detectar_intencao_artefato


_ORIGINAL_GERAR_RESPOSTA = _agente.gerar_resposta_agente


def _normalizar(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(ch for ch in bruto if not unicodedata.combining(ch)).casefold().strip()


def _mensagem_usuario(mensagem: str) -> str:
    marcador = "\n\nCONTEXTO INTERNO DA IA CTI:"
    return str(mensagem or "").split(marcador, 1)[0].strip()


def _ultima_mensagem(historico: list[dict[str, str]], papel: str) -> str:
    for item in reversed(historico):
        if item.get("role") == papel and str(item.get("content") or "").strip():
            return str(item["content"]).strip()
    return ""


def _pedido_transformacao_artefato(mensagem_usuario: str, solicitados: set[str]) -> bool:
    if not solicitados:
        return False
    texto = _normalizar(mensagem_usuario)
    referencias = (
        "resposta acima",
        "informacoes acima",
        "informacoes apresentadas",
        "dados apresentados",
        "resposta anterior",
        "analise acima",
        "resultado acima",
        "disposicao das respostas",
        "com base no que foi apresentado",
    )
    return any(ref in texto for ref in referencias)


def _snapshot_id(texto: str) -> str:
    return hashlib.sha256(str(texto or "").encode("utf-8")).hexdigest()[:24]


def gerar_resposta_agente(
    mensagem: str,
    historico: list[dict[str, str]] | None,
    usuario_id: str,
    tipo_usuario: str,
) -> tuple[str, dict[str, Any]]:
    historico_atual = historico or []
    pergunta = _mensagem_usuario(mensagem)
    solicitados = detectar_intencao_artefato(pergunta)
    resposta_anterior = _ultima_mensagem(historico_atual, "assistant")
    pergunta_anterior = _ultima_mensagem(historico_atual, "user")

    transforma_snapshot = bool(
        resposta_anterior
        and _pedido_transformacao_artefato(pergunta, solicitados)
    )
    repete_pergunta = bool(
        resposta_anterior
        and pergunta_anterior
        and _normalizar(pergunta) == _normalizar(pergunta_anterior)
    )

    if transforma_snapshot or repete_pergunta:
        snapshot = _snapshot_id(resposta_anterior)
        metadados: dict[str, Any] = {
            "fontes": [
                {
                    "tipo": "SNAPSHOT_CONVERSA",
                    "descricao": "Snapshot evidencial congelado da resposta anterior; nenhuma fonte foi reconsultada.",
                }
            ],
            "modelo": "snapshot_conversa_sem_reconsulta",
            "arquitetura": "snapshot_evidencial_unico",
            "snapshot_evidencial_id": snapshot,
            "controle_snapshot_evidencial": "reutilizado_sem_nova_leitura",
            "controle_fontes_snapshot": "uma_execucao_multifonte_um_snapshot",
            "ia009_contexto_pos_sintese": {
                "solicitados": sorted(solicitados),
                "referencia_texto": resposta_anterior,
                "modo": "TRANSFORMACAO_ARTEFATO" if transforma_snapshot else "REPETICAO_PERGUNTA",
                "snapshot_evidencial_id": snapshot,
            },
            "somente_leitura": True,
            "ferramentas": [],
        }
        if transforma_snapshot:
            return "Artefato gerado a partir do snapshot evidencial da resposta anterior, sem nova consulta às fontes.", metadados
        return resposta_anterior, metadados

    resposta_texto, metadados = _ORIGINAL_GERAR_RESPOSTA(
        mensagem=mensagem,
        historico=historico_atual,
        usuario_id=usuario_id,
        tipo_usuario=tipo_usuario,
    )
    metadados = dict(metadados or {})
    metadados["controle_fontes_snapshot"] = "uma_execucao_multifonte_um_snapshot"
    metadados["ia009_contexto_pos_sintese"] = {
        "solicitados": sorted(solicitados),
        "referencia_texto": resposta_anterior if _pedido_transformacao_artefato(pergunta, solicitados) else "",
        "modo": "NOVA_EXECUCAO_UNICA",
    }
    return resposta_texto, metadados


_agente.gerar_resposta_agente = gerar_resposta_agente
