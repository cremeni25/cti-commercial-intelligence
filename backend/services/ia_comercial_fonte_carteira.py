"""Carteira setorizada e dicionário comercial como fontes da IA Comercial."""
from __future__ import annotations

from services import ia_comercial_universo as universo

FONTES = {
    "carteira_setorizada": (
        "Um registro por cliente com a setorização do CTI: grupo (CLIENTE_ATIVO = comprou em até 24 meses, "
        "CLIENTE_INATIVO, PROSPECT_COM_FROTA, PROSPECT), porte da frota (GRANDE 20+, MEDIO 5-19, PEQUENO 1-4), "
        "sinais (RECORRENTE, JANELA_RENOVACAO = equipamento mais novo com 6+ anos, USA_CONCORRENTE, NEGOCIO_ABERTO, "
        "SEM_RESPONSAVEL), frota registrada no ANFIR (total, Carrier, concorrência), implementadora principal, última "
        "compra, unidades compradas, negócios em aberto e responsável comercial. Use para segmentar e priorizar clientes."
    ),
    "glossario_comercial": "Dicionário oficial de termos do CTI (cliente, responsável comercial, negócio, frota registrada, janela de renovação etc.) com sinônimos aceitos.",
}
_ORIGINAL = None
_ATIVADO = False


def _carregar(usuario_id: str, tipo_usuario: str):
    from core.glossario_comercial import GLOSSARIO
    from services import carteira_setorizada

    fontes, metadados = _ORIGINAL(usuario_id, tipo_usuario)
    gestao = str(tipo_usuario or "").upper() in {"ADMIN_MASTER", "DIRETOR_VIENA_SP"}
    try:
        registros = carteira_setorizada.setorizacao(responsavel_id=None if gestao else str(usuario_id), limite=100000)["clientes"]
    except Exception:
        registros = []
    fontes["carteira_setorizada"] = registros
    fontes["glossario_comercial"] = [{"termo": g["termo"], "definicao": g["definicao"], "sinonimos": ", ".join(g["sinonimos"])} for g in GLOSSARIO]
    metadados["carteira_setorizada"] = {"total_registros": len(registros), "escopo": "empresa" if gestao else "propria_carteira", "modo": "somente_leitura"}
    return fontes, metadados


def ativar() -> None:
    global _ATIVADO, _ORIGINAL
    if _ATIVADO:
        return
    _ORIGINAL = universo._carregar_fontes
    universo.FONTES_PUBLICAS.update(FONTES)
    universo._carregar_fontes = _carregar
    _ATIVADO = True


ativar()
