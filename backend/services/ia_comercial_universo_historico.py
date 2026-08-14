from __future__ import annotations

from typing import Any

from services import ia_comercial_universo as universo
from services.historical_commercial_source import carregar_historico_comercial

FONTE = "historico_comercial"
DESCRICAO = (
    "Histórico comercial homologado 2023–2026 do funil Viena, com BACKLOG, OPORTUNIDADE e "
    "INTERMEDIAÇÃO-OEM. Contém cliente, equipamento, quantidade, valores nominais, observações, "
    "status reconstruído, motivo de perda, canal, implementadora, representante histórico e "
    "responsabilidade atual. É somente leitura, preserva proveniência e não representa Pipeline ativo."
)

_ORIGINAL_CARREGAR_FONTES = universo._carregar_fontes
_PATCH_APLICADO = False


def _carregar_fontes_com_historico(usuario_id: str, tipo_usuario: str) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    fontes, metadados = _ORIGINAL_CARREGAR_FONTES(usuario_id, tipo_usuario)
    # O ciclo HIST foi homologado pelo ADMIN_MASTER. Até existir regra territorial
    # determinística para todos os perfis, a nova fonte não amplia acesso de terceiros.
    if str(tipo_usuario or "").upper() == "ADMIN_MASTER":
        registros = [dict(item) for item in carregar_historico_comercial()]
        fontes[FONTE] = registros
        metadados["historico_comercial"] = {
            "autorizado": True,
            "total_registros": len(registros),
            "modo": "somente_leitura",
            "nao_promove_crm": True,
        }
    else:
        fontes[FONTE] = []
        metadados["historico_comercial"] = {
            "autorizado": False,
            "motivo": "RBAC histórico comercial ainda não individualizado para este perfil",
            "modo": "somente_leitura",
        }
    return fontes, metadados


def registrar_historico_comercial_no_universo() -> None:
    global _PATCH_APLICADO
    if _PATCH_APLICADO:
        return
    universo.FONTES_PUBLICAS[FONTE] = DESCRICAO
    universo._carregar_fontes = _carregar_fontes_com_historico
    _PATCH_APLICADO = True
