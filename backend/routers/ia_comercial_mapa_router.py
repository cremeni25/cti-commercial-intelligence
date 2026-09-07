from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_mapa_equipe_router import visao_equipe
from services.ia_comercial_cti import IAComercialOpenAIError
from services.ia_comercial_agente_crm import gerar_resposta_agente

router = APIRouter(prefix="/crm-seguro/mapa-equipe", tags=["inteligencia-comercial"])


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


def _mensagem_analise(visao: dict[str, Any]) -> str:
    snapshot = _snapshot_comercial(visao)
    return (
        "Faça uma análise comercial da seleção abaixo usando exclusivamente as fontes internas autorizadas do CTI. "
        "Use o snapshot apenas como ponto factual de partida e consulte o universo CTI para procurar relações que realmente acrescentem decisão: "
        "ANFIR, Histórico/Funil, CRM, região/DDD, linhas e modelos de equipamento, implementadoras, fabricantes concorrentes, perdas e cobertura, quando houver evidência. "
        "Não transforme ausência de vínculo histórico em oportunidade e não atribua registros a uma pessoa sem evidência de autoria ou território. "
        "Não repita os indicadores do painel apenas em forma de frase. Procure explicar o que eles significam em conjunto, onde existe concentração, mudança de comportamento, risco, vazio de atuação ou sinal comercial relevante. "
        "Se os dados não sustentarem uma conclusão, diga isso naturalmente. "
        "Escreva como um profissional comercial experiente conversaria com outro profissional: linguagem natural, direta e específica ao caso. "
        "Não use tabela, não imponha quantidade fixa de insights, não use checklist, não use títulos padronizados e não siga frases prontas. "
        "A resposta pode ter poucos parágrafos; a profundidade deve vir da análise, não do volume de texto.\n\n"
        "SNAPSHOT INTERNO DA SELEÇÃO:\n" + json.dumps(snapshot, ensure_ascii=False, default=str)
    )


@router.get("/inteligencia")
def inteligencia_comercial_natural(
    responsavel_id: str | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    visao = visao_equipe(responsavel_id=responsavel_id, usuario=usuario)
    usuario_analise_id, tipo_analise = _perfil_analise(visao, usuario)

    try:
        texto, metadados = gerar_resposta_agente(
            _mensagem_analise(visao),
            [],
            usuario_analise_id,
            tipo_analise,
        )
    except IAComercialOpenAIError as exc:
        raise HTTPException(status_code=503, detail=exc.mensagem_publica) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="A IA Comercial não concluiu esta leitura.") from exc

    if not str(texto or "").strip():
        raise HTTPException(status_code=503, detail="A IA Comercial não produziu uma leitura para esta seleção.")

    return {
        "analise": str(texto).strip(),
        "selecao": visao.get("selecao") or {},
        "origem": "IA_COMERCIAL_CTI",
        "somente_leitura": True,
        "fontes": metadados.get("fontes") or [],
    }
