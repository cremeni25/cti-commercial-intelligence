from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from routers.crm_scope_mapa_equipe_router import visao_equipe
from routers.crm_scope_mapa_insights_router import insights_mapa
from routers.ia_comercial_mapa_router import _executar_leitura

router = APIRouter(prefix="/crm-seguro/mapa-equipe", tags=["inteligencia-comercial-alvo"])


class AlvoMapaPayload(BaseModel):
    origem: str = Field(min_length=1, max_length=120)
    cliente: str = Field(min_length=1, max_length=300)
    responsavel: str = Field(min_length=1, max_length=200)


def _fold(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").strip().upper())
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", texto).strip()


def _direcionamento_origem(insights: dict[str, Any], origem: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if origem == "perdas":
        bloco = insights.get("perdas") or {}
        return bloco.get("direcionamento") or {}, {
            "tipo": "PERDAS",
            "total_perdido": bloco.get("total_perdido"),
            "motivos": bloco.get("motivos") or [],
            "por_linha": bloco.get("por_linha") or [],
        }

    if origem.startswith("linha:"):
        codigo = origem.split(":", 1)[1].strip()
        bloco = next(
            (item for item in (insights.get("linhas_2026") or {}).get("linhas", []) if str(item.get("codigo") or "") == codigo),
            None,
        )
        if not bloco:
            raise HTTPException(status_code=404, detail="Linha comercial não localizada no escopo atual.")
        composicao = bloco.get("composicao_marca") or {}
        return bloco.get("direcionamento") or {}, {
            "tipo": "LINHA",
            "linha": bloco.get("nome"),
            "total_2026": bloco.get("total_2026"),
            "carrier": composicao.get("carrier"),
            "outras_marcas": composicao.get("outras_marcas"),
            "marcas_concorrentes": composicao.get("marcas_concorrentes") or [],
        }

    if origem.startswith("regiao:"):
        identificador = origem.split(":", 1)[1].strip()
        bloco = next(
            (item for item in insights.get("regioes", []) if str(item.get("id") or "") == identificador),
            None,
        )
        if not bloco:
            raise HTTPException(status_code=404, detail="Responsável comercial não localizado no escopo atual.")
        return bloco.get("direcionamento") or {}, {
            "tipo": "RESPONSAVEL",
            "responsavel": bloco.get("nome"),
            "mercado_2026": bloco.get("mercado_2026"),
            "clientes_mercado": bloco.get("clientes_mercado"),
            "crm_ativos": bloco.get("crm_ativos"),
            "pipeline_ativo": bloco.get("pipeline_ativo"),
        }

    raise HTTPException(status_code=400, detail="Origem de inteligência comercial inválida.")


def _localizar_alvo(direcionamento: dict[str, Any], cliente: str, responsavel: str) -> dict[str, Any]:
    cliente_fold = _fold(cliente)
    responsavel_fold = _fold(responsavel)
    for alvo in direcionamento.get("alvos") or []:
        if _fold(alvo.get("cliente")) == cliente_fold and _fold(alvo.get("responsavel")) == responsavel_fold:
            return alvo
    raise HTTPException(status_code=404, detail="Cliente não localizado entre os alvos autorizados desta leitura.")


def _mensagem_alvo(alvo: dict[str, Any], contexto: dict[str, Any], escopo: dict[str, Any]) -> str:
    snapshot = {
        "cliente": alvo.get("cliente"),
        "responsavel": alvo.get("responsavel"),
        "linha_principal": alvo.get("linha_principal"),
        "unidades": alvo.get("unidades"),
        "ocorrencias": alvo.get("ocorrencias"),
        "cobertura": alvo.get("cobertura"),
        "concorrencia": alvo.get("concorrencia"),
        "fontes": alvo.get("fontes") or {},
        "temporalidade": alvo.get("temporalidade") or {},
        "ciclo_comercial": alvo.get("ciclo_comercial") or {},
        "contexto_da_leitura": contexto,
        "escopo_autorizado": escopo,
    }
    return (
        "Você está produzindo a leitura automática de UM cliente dentro do Mapa Estratégico do CTI. "
        "A classificação do ciclo CRM é apenas um sinal estrutural; ela NÃO é a interpretação comercial. "
        "Analise os fatos específicos deste cliente e explique o que realmente diferencia este caso dos demais. "
        "Cruze volume e recorrência ANFIR, linha, concorrência, Histórico/Funil, cobertura CRM, temporalidade, responsável e o contexto agregado da origem. "
        "Não use frases genéricas como 'o mercado gerou um sinal', 'fazer a primeira abordagem' ou textos que serviriam igualmente para qualquer cliente. "
        "Não invente vínculo, data, relacionamento, concorrente, oportunidade ou causa. Quando uma fonte estiver zerada, trate isso como lacuna de evidência, não como prova de inexistência. "
        "A ação deve nascer do diagnóstico deste cliente e indicar o próximo movimento mais coerente com os fatos disponíveis. "
        "Responda em português do Brasil, de forma curta, comercial e natural, sem tabela e sem lista. "
        "Use EXATAMENTE estes dois marcadores, cada um com um parágrafo: INTERPRETAÇÃO: e AÇÃO:.\n\n"
        "SNAPSHOT AUDITÁVEL DO CLIENTE:\n" + json.dumps(snapshot, ensure_ascii=False, default=str)
    )


def _separar_resposta(texto: str) -> tuple[str, str]:
    conteudo = str(texto or "").strip()
    match = re.search(r"INTERPRETA(?:Ç|C)[AÃ]O\s*:\s*(.*?)\s*A(?:Ç|C)[AÃ]O\s*:\s*(.*)$", conteudo, flags=re.I | re.S)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return conteudo, ""


@router.post("/inteligencia/alvo")
def inteligencia_natural_por_alvo(
    payload: AlvoMapaPayload,
    responsavel_id: str | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    insights = insights_mapa(responsavel_id=responsavel_id, usuario=usuario)
    direcionamento, contexto = _direcionamento_origem(insights, payload.origem)
    alvo = _localizar_alvo(direcionamento, payload.cliente, payload.responsavel)

    visao = visao_equipe(responsavel_id=responsavel_id, usuario=usuario)
    texto, metadados = _executar_leitura(
        visao,
        usuario,
        _mensagem_alvo(alvo, contexto, insights.get("escopo") or {}),
    )
    interpretacao, acao = _separar_resposta(texto)
    if not interpretacao:
        raise HTTPException(status_code=503, detail="A Inteligência Comercial não produziu leitura para este cliente.")

    return {
        "interpretacao": interpretacao,
        "acao": acao,
        "cliente": alvo.get("cliente"),
        "responsavel": alvo.get("responsavel"),
        "origem": "IA_COMERCIAL_CTI",
        "somente_leitura": True,
        "fontes": metadados.get("fontes") or [],
    }
