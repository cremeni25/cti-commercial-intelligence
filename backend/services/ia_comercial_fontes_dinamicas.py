from __future__ import annotations

from typing import Any

from core.supabase_client import supabase
from services import ia_comercial_universo as universo

FONTE = "fontes_universais"
DESCRICAO = (
    "Fontes documentais e estruturadas homologadas pelo ADMIN_MASTER no Back Office Universal. "
    "Inclui PDFs, Word, PowerPoint, planilhas, textos, JSON e demais fontes publicadas, com "
    "proveniência, classificação, nome do arquivo e registros semânticos. Use esta fonte quando "
    "a pergunta puder depender de documentos ou uploads homologados que não pertencem às fontes nativas do CRM/ANFIR."
)

_ORIGINAL_CARREGAR_FONTES = universo._carregar_fontes
_ATIVADO = False


def _dados(resposta: Any) -> list[dict[str, Any]]:
    dados = getattr(resposta, "data", None)
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]
    if isinstance(dados, dict):
        return [dados]
    return []


def _carregar_publicadas(tipo_usuario: str) -> list[dict[str, Any]]:
    if str(tipo_usuario or "").upper() != "ADMIN_MASTER":
        return []
    try:
        fontes = _dados(
            supabase.table("cti_fontes_universais")
            .select("id,nome_arquivo,nome_exibicao,tipo_detectado,classificacao_negocio,classificacao_sugerida,descricao_semantica,sha256,created_at,publicado_ia_em")
            .eq("publicado_ia", True)
            .eq("status_governanca", "PUBLICADO_IA")
            .order("created_at", desc=True)
            .execute()
        )
    except Exception:
        # A camada universal é complementar. Se o repositório dinâmico estiver
        # indisponível, as fontes nativas do CTI continuam consultáveis e a IA
        # não deve falhar por causa de um upload externo temporariamente inacessível.
        return []
    if not fontes:
        return []

    por_id = {str(item.get("id")): item for item in fontes if item.get("id")}
    registros: list[dict[str, Any]] = []
    for fonte_id, fonte in por_id.items():
        try:
            semanticos = _dados(
                supabase.table("cti_fontes_semanticas")
                .select("indice,tipo_registro,conteudo_texto,dados,metadados")
                .eq("fonte_id", fonte_id)
                .order("indice")
                .limit(5000)
                .execute()
            )
        except Exception:
            continue
        for item in semanticos:
            dados = item.get("dados") if isinstance(item.get("dados"), dict) else {}
            metadados = item.get("metadados") if isinstance(item.get("metadados"), dict) else {}
            registro = dict(dados)
            registro.update({
                "fonte_id": fonte_id,
                "fonte_nome_arquivo": fonte.get("nome_exibicao") or fonte.get("nome_arquivo"),
                "fonte_tipo": fonte.get("tipo_detectado"),
                "fonte_classificacao": fonte.get("classificacao_negocio") if fonte.get("classificacao_negocio") not in (None, "", "NAO_CLASSIFICADA") else fonte.get("classificacao_sugerida"),
                "fonte_descricao": fonte.get("descricao_semantica"),
                "fonte_sha256": fonte.get("sha256"),
                "registro_indice": item.get("indice"),
                "registro_tipo": item.get("tipo_registro"),
                "conteudo_texto": item.get("conteudo_texto"),
                "registro_metadados": metadados,
            })
            registros.append(universo._sanitizar_registro(registro))
    return registros


def _carregar_fontes_com_uploads(usuario_id: str, tipo_usuario: str):
    fontes, metadados = _ORIGINAL_CARREGAR_FONTES(usuario_id, tipo_usuario)
    registros = _carregar_publicadas(tipo_usuario)
    fontes[FONTE] = registros
    metadados[FONTE] = {
        "autorizado": str(tipo_usuario or "").upper() == "ADMIN_MASTER",
        "total_registros": len(registros),
        "modo": "somente_leitura",
        "origem": "BACKOFFICE_UNIVERSAL",
        "descoberta_dinamica": True,
    }
    return fontes, metadados


def ativar_fontes_dinamicas() -> None:
    global _ATIVADO
    if _ATIVADO:
        return
    universo.FONTES_PUBLICAS[FONTE] = DESCRICAO
    universo._carregar_fontes = _carregar_fontes_com_uploads
    _ATIVADO = True


ativar_fontes_dinamicas()
