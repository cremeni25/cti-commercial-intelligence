from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_mapa_equipe_router import visao_equipe
from services.ia_comercial_cti import IAComercialOpenAIError
from services.ia_comercial_agente_crm import gerar_resposta_agente

router = APIRouter(prefix="/crm-seguro/mapa-equipe", tags=["inteligencia-comercial"])


class TurnoContextual(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class PerguntaContextual(BaseModel):
    pergunta: str = Field(min_length=1, max_length=2000)
    historico: list[TurnoContextual] = Field(default_factory=list, max_length=8)


def _perfil_analise(visao: dict[str, Any], usuario: UsuarioAutenticado) -> tuple[str, str]:
    selecao = visao.get("selecao") or {}
    selecionado_id = str(selecao.get("id") or "").strip()
    if not selecionado_id:
        return str(usuario.id), str(usuario.tipo_usuario)

    registro = next(
        (item for item in (visao.get("equipe") or []) if str(item.get("id") or "") == selecionado_id),
        None,
    )
    if not registro:
        return str(usuario.id), str(usuario.tipo_usuario)
    return selecionado_id, str(registro.get("tipo_usuario") or "USUARIO_CTI")


def _snapshot_comercial(visao: dict[str, Any]) -> dict[str, Any]:
    selecao = visao.get("selecao") or {}
    dados = visao.get("mercado") or {}
    evidencias = visao.get("evidencias") or {}
    reconciliacao = visao.get("reconciliacao") or {}
    return {
        "selecao": {
            "nome": selecao.get("nome"),
            "codigo_regional": selecao.get("codigo_regional"),
            "ddds": selecao.get("ddds") or [],
        },
        "base_viena_anfir_2026": dados.get("mercado_real_viena_2026"),
        "anfir_com_vinculo_seguro_na_selecao": dados.get("mercado_real_selecao_2026"),
        "participacao_documental_pct": dados.get("participacao_regiao_no_mercado_real_pct"),
        "familias_anfir_vinculadas": dados.get("familias") or {},
        "clientes_anfir_identificados": dados.get("clientes_unicos"),
        "historico_funil": {
            "registros": evidencias.get("historico_registros_2026"),
            "unidades": evidencias.get("historico_unidades_2026"),
            "motivos_perda": evidencias.get("motivos_perda_historico") or [],
        },
        "crm": {
            "registros": evidencias.get("crm_registros"),
            "ativos": evidencias.get("crm_ativos"),
            "valor_ativo": evidencias.get("crm_valor_ativo"),
            "status": evidencias.get("crm_status") or [],
        },
        "conexoes_fontes": {
            "clientes_anfir": reconciliacao.get("clientes_anfir"),
            "clientes_historico": reconciliacao.get("clientes_historico"),
            "clientes_crm": reconciliacao.get("clientes_crm"),
            "presentes_nas_tres": reconciliacao.get("nas_tres_fontes"),
        },
    }


def _fontes_contextuais(visao: dict[str, Any]) -> list[dict[str, str]]:
    selecao = visao.get("selecao") or {}
    mercado = visao.get("mercado") or {}
    evidencias = visao.get("evidencias") or {}
    nome = str(selecao.get("nome") or "Seleção atual")
    codigo = str(selecao.get("codigo_regional") or "").strip()
    ddds = [str(item) for item in (selecao.get("ddds") or []) if str(item).strip()]
    territorio = " · ".join(parte for parte in (codigo, f"DDD {', '.join(ddds)}" if ddds else "") if parte)

    fontes: list[dict[str, str]] = [
        {
            "codigo": "TERRITORIO_RESPONSAVEL",
            "nome": "Território e responsável",
            "evidencia": f"{nome}{f' · {territorio}' if territorio else ''}",
        }
    ]

    if mercado.get("mercado_real_viena_2026") is not None:
        fontes.append(
            {
                "codigo": "ANFIR_2026",
                "nome": "ANFIR 2026",
                "evidencia": (
                    f"{int(mercado.get('clientes_unicos') or 0)} clientes identificados · "
                    f"{int(mercado.get('mercado_real_selecao_2026') or 0)} registros com vínculo seguro"
                ),
            }
        )

    historico_registros = int(evidencias.get("historico_registros_2026") or 0)
    if historico_registros > 0:
        fontes.append(
            {
                "codigo": "HISTORICO_FUNIL_2026",
                "nome": "Histórico/Funil 2026",
                "evidencia": (
                    f"{historico_registros} eventos · "
                    f"{int(evidencias.get('historico_unidades_2026') or 0)} unidades registradas"
                ),
            }
        )

    crm_registros = int(evidencias.get("crm_registros") or 0)
    if crm_registros > 0:
        fontes.append(
            {
                "codigo": "CRM_ATUAL",
                "nome": "CRM atual",
                "evidencia": (
                    f"{crm_registros} registros · "
                    f"{int(evidencias.get('crm_ativos') or 0)} negociações ativas"
                ),
            }
        )
    return fontes


def _regras_contextuais() -> str:
    return (
        "Use exclusivamente as fontes internas autorizadas do CTI e respeite integralmente o RBAC da seleção atual. "
        "ANFIR representa mercado realizado/referência e nunca deve virar oportunidade automática. "
        "Histórico/Funil representa fatos comerciais anteriores; CRM representa negócios atuais em andamento. "
        "Não atribua autoria ou território sem evidência. Não invente vínculos entre fontes. "
        "Interprete o conjunto antes de recomendar qualquer ação e deixe claro quando os dados não sustentarem uma conclusão. "
        "Responda em linguagem comercial natural, direta e específica ao contexto, sem tabela, checklist, quantidade fixa de insights ou frases prontas."
    )


def _mensagem_analise(visao: dict[str, Any]) -> str:
    snapshot = _snapshot_comercial(visao)
    return (
        "Faça uma análise comercial da seleção abaixo. "
        + _regras_contextuais()
        + " Procure relações que realmente acrescentem decisão entre ANFIR, Histórico/Funil, CRM, região/DDD, linhas e modelos de equipamento, implementadoras, fabricantes concorrentes, perdas e cobertura, quando houver evidência. "
        "Não repita os indicadores do painel apenas em forma de frase; explique o que significam em conjunto, onde existe concentração, mudança de comportamento, risco, vazio de atuação ou sinal comercial relevante.\n\n"
        "SNAPSHOT INTERNO DA SELEÇÃO:\n" + json.dumps(snapshot, ensure_ascii=False, default=str)
    )


def _mensagem_pergunta(visao: dict[str, Any], pergunta: str) -> str:
    snapshot = _snapshot_comercial(visao)
    return (
        "Continue a análise comercial dentro do MESMO contexto selecionado nesta tela. "
        + _regras_contextuais()
        + " A pergunta abaixo é um aprofundamento da leitura atual, não uma nova conversa genérica. "
        "Use o histórico transitório somente para manter continuidade de sentido; revalide fatos operacionais nas fontes autorizadas desta execução quando necessário.\n\n"
        f"PERGUNTA DO USUÁRIO:\n{pergunta.strip()}\n\n"
        "SNAPSHOT ATUAL DA SELEÇÃO:\n" + json.dumps(snapshot, ensure_ascii=False, default=str)
    )


def _executar_leitura(
    visao: dict[str, Any],
    usuario: UsuarioAutenticado,
    mensagem: str,
    historico: list[dict[str, str]] | None = None,
) -> tuple[str, dict[str, Any]]:
    usuario_analise_id, tipo_analise = _perfil_analise(visao, usuario)
    try:
        return gerar_resposta_agente(
            mensagem,
            historico or [],
            usuario_analise_id,
            tipo_analise,
        )
    except IAComercialOpenAIError as exc:
        raise HTTPException(status_code=503, detail=exc.mensagem_publica) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="A leitura inteligente não foi concluída.") from exc


def _resposta(texto: str, metadados: dict[str, Any], visao: dict[str, Any]) -> dict[str, Any]:
    if not str(texto or "").strip():
        raise HTTPException(status_code=503, detail="A leitura inteligente não produziu resposta para esta seleção.")
    return {
        "analise": str(texto).strip(),
        "selecao": visao.get("selecao") or {},
        "origem": "IA_COMERCIAL_CTI",
        "somente_leitura": True,
        "persistido": False,
        "fontes": metadados.get("fontes") or [],
        "fontes_contextuais": _fontes_contextuais(visao),
    }


@router.get("/inteligencia")
def inteligencia_comercial_natural(
    responsavel_id: str | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    visao = visao_equipe(responsavel_id=responsavel_id, usuario=usuario)
    texto, metadados = _executar_leitura(visao, usuario, _mensagem_analise(visao))
    return _resposta(texto, metadados, visao)


@router.post("/inteligencia/perguntar")
def inteligencia_comercial_contextual(
    payload: PerguntaContextual,
    responsavel_id: str | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    visao = visao_equipe(responsavel_id=responsavel_id, usuario=usuario)
    historico = [
        {"role": turno.role, "content": turno.content.strip()}
        for turno in payload.historico[-8:]
        if turno.content.strip()
    ]
    texto, metadados = _executar_leitura(
        visao,
        usuario,
        _mensagem_pergunta(visao, payload.pergunta),
        historico,
    )
    return _resposta(texto, metadados, visao)
