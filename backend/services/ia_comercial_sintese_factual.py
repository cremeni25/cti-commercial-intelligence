from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from services.ia_comercial_agente import _executar_ferramenta_cti
from services.ia_comercial_cti import IAComercialOpenAIError, _classificar_falha_openai


SYNTHESIS_MODEL = os.getenv("OPENAI_AGENT_MODEL", os.getenv("OPENAI_WEB_MODEL", "gpt-4.1-mini"))

DOMINIOS_FACTUAIS = {
    "cti_atual",
    "historico",
    "anfir",
    "territorio",
    "produtos",
    "vendas",
    "clientes",
    "oportunidades",
    "relacionamentos_vendas",
}

INSTRUCOES_SINTESE_FATUAL = """Você é a camada de síntese factual da IA Comercial CTI.
Sua única função é responder à PERGUNTA_ATUAL usando exclusivamente as EVIDENCIAS_EXECUCAO fornecidas no JSON de entrada.
Você não recebe histórico de conversa, resposta preliminar do agente nem conhecimento operacional implícito como evidência.

REGRAS ABSOLUTAS DE EVIDÊNCIA:
- Não invente, complete ou reutilize fatos ausentes das EVIDENCIAS_EXECUCAO.
- EVIDENCIAS_EXECUCAO contém somente fontes autorizadas pelas EVIDENCIAS_REQUERIDAS da pergunta atual. Não acrescente fatos de outros domínios.
- DOMINIOS_NAO_CONSULTADOS são explicitamente desconhecidos nesta execução. Não faça afirmações positivas nem negativas sobre eles.
- Se oportunidades não foram consultadas, não diga que existem, não existem, estão abertas, fechadas, ganhas, perdidas ou ausentes do pipeline.
- Se vendas não foram consultadas, não diga que existem ou não existem vendas, nem ausência de vínculo de venda.
- Se produtos não foram consultados, não nomeie modelos do catálogo, portfólio atual ou disponibilidade comercial. Modelos podem ser descritos apenas conforme a cobertura do próprio recorte territorial/ANFIR quando essa evidência existir.
- "Oportunidade comercial" em sentido analítico é uma inferência/recomendação, não a entidade Oportunidade do CRM. Pode indicar sinais comerciais sustentados pelos dados, deixando claro que são inferências.
- Cliente só pode ser chamado de ativo/inativo quando esse status estiver explicitamente presente na evidência consultada. Status de registro ANFIR não prova status do cliente no CRM.
- Status operacional, documental ou ANFIR não prova venda, aceite, negócio concluído, relacionamento comercial ativo ou entrega.
- Nesta camada factual, não use "maioria", "predominante", "predominantes", "líder", "líderes", "domina", "dominam", "dominante" ou equivalentes para descrever distribuição. Informe sempre contagens e, quando útil, percentuais sobre o universo total do recorte.
- Quando a cobertura de um campo for parcial, informe a contagem exata sobre o universo total ou qualifique explicitamente como "entre os registros preenchidos".
- Preserve ausências e qualidade dos dados. Se um valor de fabricante/modelo/status tiver grafia anômala ou cobertura parcial, descreva a limitação sem normalizar silenciosamente o dado como se fosse completo.
- CAMPO AUSENTE NÃO SIGNIFICA OBJETO AUSENTE: modelo, fabricante, status ou qualquer outro campo vazio/nulo significa apenas "não registrado/não informado na fonte". Nunca conclua que o cliente não possui aquele item, equipamento, condição ou característica no mundo real.
- Ausência de modelo, fabricante ou outro campo pode sustentar somente recomendação de qualificação/atualização da base ou investigação comercial para preencher a informação. Por si só, não sustenta oportunidade de venda, renovação, substituição, modernização, conversão, ganho de share ou oferta de produto.
- Só use dimensões factuais que aparecem em RESUMO_RELEVANTE. Se status, fabricante de equipamento, implementadora, catálogo ou outra dimensão não estiver presente ali, não a mencione.
- Para sinais de oportunidade comercial, derive recomendações apenas das dimensões presentes: concentração territorial pode justificar priorização geográfica; lacunas de dados podem justificar qualificação da base. Não transforme lacuna cadastral em demanda comercial.
- Em análises de frota, diferencie obrigatoriamente total_registros de total_veiculos_identificaveis. Um mesmo veículo pode aparecer em mais de um registro histórico. Nunca trate total_registros como quantidade de veículos únicos quando total_veiculos_identificaveis estiver disponível.
- Cobertura de placa, chassi, fabricante/modelo do caminhão ou número de frota descreve qualidade/completude da base; não conclua ausência física do veículo ou atributo quando o campo não estiver preenchido.
- Rankings de tipo de veículo, fabricante e modelo do caminhão contam registros do recorte, salvo indicação explícita em contrário; não os apresente como contagem de veículos únicos.
- Preserve literalmente as categorias retornadas nos rankings de frota. Não some, normalize, una ou declare que uma contagem "inclui variações de grafia" quando o backend não fornecer explicitamente um agregado normalizado. Se houver grafias diferentes, apresente-as separadamente ou sinalize a variação como qualidade de dado.
- Diferencie fato, limitação e inferência/recomendação.
- Responda em português do Brasil, com linguagem comercial clara e direta.
"""


def _normalizar(texto: Any) -> str:
    return str(texto or "").strip().casefold()


def _evidencias_atendidas(metadados: dict[str, Any]) -> set[str]:
    valores = metadados.get("evidencias_atendidas") or []
    return {str(item) for item in valores if str(item)}


def _evidencias_requeridas(metadados: dict[str, Any]) -> set[str]:
    valores = metadados.get("evidencias_requeridas") or []
    return {str(item) for item in valores if str(item)}


def _evidencias_permitidas_sintese(metadados: dict[str, Any]) -> set[str]:
    atendidas = _evidencias_atendidas(metadados)
    requeridas = _evidencias_requeridas(metadados)
    if requeridas:
        return atendidas & requeridas
    return atendidas


def _dominios_nao_consultados(evidencias: set[str]) -> list[str]:
    return sorted(DOMINIOS_FACTUAIS - evidencias)


def _dominio_da_ferramenta(ferramenta: str, argumentos: dict[str, Any]) -> set[str]:
    if ferramenta == "consultar_resumo_cti":
        return {"cti_atual"}
    if ferramenta == "consultar_historico_cti":
        return {"historico"}
    if ferramenta == "consultar_catalogo_produtos_cti":
        return {"produtos"}
    if ferramenta == "consultar_territorio_cti":
        return {"territorio"}
    if ferramenta == "consultar_anfir_cti":
        return {"anfir"}
    if ferramenta == "consultar_dominio_cti":
        dominio = str(argumentos.get("dominio") or "")
        if dominio == "vendas":
            return {"vendas", "relacionamentos_vendas"}
        if dominio in {"clientes", "oportunidades"}:
            return {dominio}
    return set()


def _dimensoes_territoriais_pedidas(pergunta_atual: str) -> set[str]:
    texto = _normalizar(pergunta_atual)
    dimensoes: set[str] = {"totais"}
    if "cliente" in texto:
        dimensoes.add("clientes")
    if "modelo" in texto:
        dimensoes.add("modelos")
    if any(t in texto for t in ("concentração", "concentracao", "territorial", "território", "territorio", "cidade", "ddd", "região", "regiao")):
        dimensoes.add("territorio")
    if "implementadora" in texto:
        dimensoes.add("implementadoras")
    if "fabricante" in texto or "marca" in texto:
        dimensoes.add("fabricantes")
    if "linha" in texto:
        dimensoes.add("linhas")
    if any(
        t in texto
        for t in (
            "frota",
            "veículo",
            "veiculo",
            "veículos",
            "veiculos",
            "placa",
            "chassi",
            "caminhão",
            "caminhao",
            "caminhões",
            "caminhoes",
            "tipo de veículo",
            "tipo de veiculo",
        )
    ):
        dimensoes.add("frota")
    return dimensoes


def _resumo_territorial_relevante(resultado: dict[str, Any], pergunta_atual: str) -> dict[str, Any]:
    resumo = resultado.get("resumo") or {}
    if not isinstance(resumo, dict):
        resumo = {}
    dimensoes = _dimensoes_territoriais_pedidas(pergunta_atual)
    relevante: dict[str, Any] = {
        "total_registros": resumo.get("total_registros", resultado.get("total_encontrado")),
        "total_clientes": resumo.get("total_clientes"),
    }
    if "clientes" in dimensoes:
        relevante["ranking_clientes"] = resumo.get("ranking_clientes") or []
    if "modelos" in dimensoes:
        cobertura = resumo.get("cobertura") or {}
        relevante["cobertura_modelos"] = {
            "com_modelo": cobertura.get("com_modelo"),
            "sem_modelo": cobertura.get("sem_modelo"),
        }
        relevante["ranking_modelos"] = resumo.get("ranking_modelos") or []
    if "territorio" in dimensoes:
        relevante["ranking_ddds"] = resumo.get("ranking_ddds") or []
        relevante["ranking_estados"] = resumo.get("ranking_estados") or []
        relevante["ranking_cidades"] = resumo.get("ranking_cidades") or []
    if "implementadoras" in dimensoes:
        relevante["ranking_implementadoras"] = resumo.get("ranking_implementadoras") or []
    if "fabricantes" in dimensoes:
        relevante["ranking_fabricantes_equipamento"] = resumo.get("ranking_fabricantes_equipamento") or []
    if "linhas" in dimensoes:
        relevante["ranking_linhas"] = resumo.get("ranking_linhas") or []
    if "frota" in dimensoes:
        cobertura = resumo.get("cobertura") or {}
        relevante["frota"] = {
            "total_veiculos_identificaveis": resumo.get("total_veiculos_identificaveis"),
            "registros_sem_identificador_veiculo": resumo.get("registros_sem_identificador_veiculo"),
            "cobertura_identificacao": {
                "com_placa": cobertura.get("com_placa"),
                "sem_placa": cobertura.get("sem_placa"),
                "com_chassi": cobertura.get("com_chassi"),
                "sem_chassi": cobertura.get("sem_chassi"),
                "com_numero_frota": cobertura.get("com_numero_frota"),
                "sem_numero_frota": cobertura.get("sem_numero_frota"),
            },
            "cobertura_caminhao": {
                "com_fabricante_caminhao": cobertura.get("com_fabricante_caminhao"),
                "sem_fabricante_caminhao": cobertura.get("sem_fabricante_caminhao"),
                "com_modelo_caminhao": cobertura.get("com_modelo_caminhao"),
                "sem_modelo_caminhao": cobertura.get("sem_modelo_caminhao"),
            },
            "ranking_tipos_veiculo_por_registros": resumo.get("ranking_tipos_veiculo") or [],
            "ranking_fabricantes_caminhao_por_registros": resumo.get("ranking_fabricantes_caminhao") or [],
            "ranking_modelos_caminhao_por_registros": resumo.get("ranking_modelos_caminhao") or [],
            "regra_contagem": "total_registros é histórico; total_veiculos_identificaveis deduplica por chassi, depois placa e id_operacional",
            "regra_rankings": "categorias preservam a grafia bruta da fonte; não agregar variações sem campo normalizado explícito",
        }
    relevante["regra_ausencia_dado"] = "campo não preenchido significa somente informação não registrada na fonte"
    return relevante


def _reduzir_resultado_para_sintese(
    ferramenta: str,
    resultado: dict[str, Any],
    pergunta_atual: str,
) -> dict[str, Any]:
    if ferramenta in {"consultar_territorio_cti", "consultar_anfir_cti"}:
        return {
            "fonte": resultado.get("fonte"),
            "visao": resultado.get("visao"),
            "filtros_aplicados": resultado.get("filtros_aplicados"),
            "total_encontrado": resultado.get("total_encontrado"),
            "RESUMO_RELEVANTE": _resumo_territorial_relevante(resultado, pergunta_atual),
            "observacao": resultado.get("observacao"),
        }
    return resultado


def _reexecutar_fontes_cti(
    metadados: dict[str, Any],
    usuario_id: str,
    tipo_usuario: str,
    pergunta_atual: str = "",
) -> list[dict[str, Any]]:
    fontes: list[dict[str, Any]] = []
    assinaturas: set[str] = set()
    permitidas = _evidencias_permitidas_sintese(metadados)

    for item in metadados.get("ferramentas") or []:
        if not isinstance(item, dict) or item.get("tipo") != "CTI":
            continue
        ferramenta = str(item.get("ferramenta") or "").strip()
        argumentos = item.get("argumentos") or {}
        if not ferramenta or not isinstance(argumentos, dict):
            continue
        dominios = _dominio_da_ferramenta(ferramenta, argumentos)
        if permitidas and not (dominios & permitidas):
            continue
        assinatura = f"{ferramenta}:{json.dumps(argumentos, sort_keys=True, ensure_ascii=False, default=str)}"
        if assinatura in assinaturas:
            continue
        assinaturas.add(assinatura)
        resultado = _executar_ferramenta_cti(ferramenta, argumentos, usuario_id, tipo_usuario)
        fontes.append(
            {
                "ferramenta": ferramenta,
                "argumentos": argumentos,
                "resultado": _reduzir_resultado_para_sintese(ferramenta, resultado, pergunta_atual),
            }
        )
    return fontes


def sintetizar_fatos_execucao(
    pergunta_atual: str,
    metadados: dict[str, Any],
    usuario_id: str,
    tipo_usuario: str,
) -> tuple[str | None, dict[str, Any]]:
    evidencias = _evidencias_permitidas_sintese(metadados)
    if not evidencias:
        return None, {"controle_sintese_factual": "nao_aplicada_sem_evidencias"}
    if "web" in evidencias:
        return None, {"controle_sintese_factual": "adiada_para_ia003_com_web"}

    fontes = _reexecutar_fontes_cti(
        metadados,
        usuario_id,
        tipo_usuario,
        pergunta_atual=pergunta_atual,
    )
    if not fontes:
        return None, {"controle_sintese_factual": "nao_aplicada_sem_fontes_cti_reexecutaveis"}

    payload = {
        "PERGUNTA_ATUAL": pergunta_atual,
        "EVIDENCIAS_REQUERIDAS": sorted(evidencias),
        "DOMINIOS_NAO_CONSULTADOS": _dominios_nao_consultados(evidencias),
        "EVIDENCIAS_EXECUCAO": fontes,
    }

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise IAComercialOpenAIError(
            "OPENAI_API_KEY não está configurada no backend.",
            codigo="OPENAI_KEY_MISSING",
        )

    try:
        client = OpenAI(api_key=api_key, timeout=120.0, max_retries=1)
        resposta = client.responses.create(
            model=SYNTHESIS_MODEL,
            instructions=INSTRUCOES_SINTESE_FATUAL,
            input=[
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False, default=str),
                }
            ],
            store=False,
        )
    except IAComercialOpenAIError:
        raise
    except Exception as exc:
        raise _classificar_falha_openai(exc) from exc

    texto = str(getattr(resposta, "output_text", "") or "").strip()
    if not texto:
        raise IAComercialOpenAIError(
            "A síntese factual não produziu uma resposta textual.",
            codigo="OPENAI_EMPTY_SYNTHESIS",
        )

    uso = getattr(resposta, "usage", None)
    return texto, {
        "controle_sintese_factual": "reconstruida_pergunta_fontes_e_dimensoes_requeridas",
        "sintese_factual_response_id": getattr(resposta, "id", None),
        "sintese_factual_tokens_entrada": getattr(uso, "input_tokens", None),
        "sintese_factual_tokens_saida": getattr(uso, "output_tokens", None),
        "sintese_factual_fontes_reexecutadas": len(fontes),
        "sintese_factual_evidencias_permitidas": sorted(evidencias),
        "sintese_factual_dominios_nao_consultados": _dominios_nao_consultados(evidencias),
        "sintese_factual_dimensoes_territoriais": sorted(_dimensoes_territoriais_pedidas(pergunta_atual)),
    }
