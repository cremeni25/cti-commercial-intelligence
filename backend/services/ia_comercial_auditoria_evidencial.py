from __future__ import annotations

import re
from typing import Any

from services.ia_comercial_planejamento import construir_planejamento_comercial, requer_planejamento


_INFERENCIA_MARCADORES = (
    "recomenda",
    "recomendado",
    "sugere",
    "sugerido",
    "pode representar",
    "pode indicar",
    "pode ser",
    "potencial",
    "priorizar",
    "prioridade",
    "oportunidade comercial",
    "implicação",
    "implicacoes",
    "implicações",
    "estratégia",
    "estrategia",
)

_TITULOS_IGNORADOS = (
    "fatos externos verificados",
    "dados internos cti",
    "cruzamento e implicações comerciais",
    "cruzamento e implicacoes comerciais",
    "recomendações",
    "recomendacoes",
)

_DOMINIO_TERMOS: dict[str, tuple[str, ...]] = {
    "clientes": ("cliente", "clientes", "carteira"),
    "oportunidades": ("oportunidade", "oportunidades", "pipeline", "probabilidade", "ganho", "perdido"),
    "itens": ("item", "itens", "equipamento", "equipamentos"),
    "propostas": ("proposta", "propostas", "aceite"),
    "pedidos": ("pedido", "pedidos", "carrier", "faturado", "entregue", "instalado", "encerrado"),
    "atividades": ("atividade", "atividades", "visita", "visitas"),
    "vendas": ("venda", "vendas", "vendido", "negócio", "negocio"),
    "produtos": ("portfólio", "portfolio", "catálogo", "catalogo", "modelo", "modelos", "linha", "linhas"),
    "territorio": ("ddd", "território", "territorio", "cidade", "uf", "região", "regiao", "frota", "veículo", "veiculo", "placa", "chassi", "implementadora", "concorrente"),
    "anfir": ("anfir",),
    "historico": ("histórico", "historico"),
}

_DOMINIOS_DOMINANTES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "produtos",
        (
            "portfólio atual",
            "portfolio atual",
            "portfólio vigente",
            "portfolio vigente",
            "catálogo atual",
            "catalogo atual",
            "catálogo oficial",
            "catalogo oficial",
            "modelos disponíveis",
            "modelos disponiveis",
        ),
    ),
    (
        "vendas",
        (
            "vendas registradas",
            "vendas recentes",
            "histórico de vendas",
            "historico de vendas",
            "vendas do modelo",
            "vendas do equipamento",
            "já teve vendas confirmadas",
            "ja teve vendas confirmadas",
        ),
    ),
)

_WEB_ENTIDADES_IGNORADAS = {
    "brasil", "brasileiro", "brasileira", "mercado", "transporte", "refrigerado", "refrigerada",
    "refrigeração", "refrigeracao", "tecnologia", "tecnologias", "fabricante", "fabricantes",
    "série", "serie", "dados", "externos", "verificados", "pedido", "cliente", "carrier", "trailer",
    "equipamento", "equipamentos", "venda", "vendas", "modelo", "linha", "linhas", "monitoramento",
    "digital", "sustentável", "sustentavel", "eficiência", "eficiencia", "fatos", "internos", "cti",
    "cruzamento", "implicações", "implicacoes", "comerciais", "não", "nao", "uma", "mais",
}


def _normalizar(texto: Any) -> str:
    return str(texto or "").strip().casefold()


def _origens_execucao(metadados: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, list[str]], list[str], list[str]]:
    origens: list[dict[str, Any]] = []
    ids_por_evidencia: dict[str, list[str]] = {}
    ids_web: list[str] = []
    ids_cti: list[str] = []

    for indice, fonte in enumerate(metadados.get("fontes") or [], start=1):
        if not isinstance(fonte, dict) or not fonte.get("url"):
            continue
        origem_id = f"WEB_{indice}"
        ids_web.append(origem_id)
        ids_por_evidencia.setdefault("web", []).append(origem_id)
        origens.append(
            {
                "id": origem_id,
                "tipo": "WEB",
                "descricao": str(fonte.get("descricao") or "Fonte web da execução"),
                "url": str(fonte.get("url")),
                "execucao_atual": True,
            }
        )

    contador_cti = 0
    for item in metadados.get("ferramentas") or []:
        if not isinstance(item, dict) or item.get("tipo") != "CTI":
            continue
        contador_cti += 1
        origem_id = f"CTI_{contador_cti}"
        ids_cti.append(origem_id)
        ferramenta = str(item.get("ferramenta") or "")
        argumentos = dict(item.get("argumentos") or {})
        resumo = dict(item.get("resumo") or {})
        dominio = str(argumentos.get("dominio") or resumo.get("dominio") or "").strip()

        evidencias: set[str] = set()
        if ferramenta == "consultar_catalogo_produtos_cti":
            evidencias.add("produtos")
        elif ferramenta == "consultar_dominio_cti" and dominio:
            evidencias.add(dominio)
            if dominio == "vendas":
                evidencias.add("relacionamentos_vendas")
        elif ferramenta == "consultar_territorio_cti":
            evidencias.add("territorio")
        elif ferramenta == "consultar_anfir_cti":
            evidencias.add("anfir")
        elif ferramenta == "consultar_historico_cti":
            evidencias.add("historico")
        elif ferramenta == "consultar_resumo_cti":
            evidencias.update({"cti_atual", "resumo_cti"})

        for evidencia in evidencias:
            ids_por_evidencia.setdefault(evidencia, []).append(origem_id)

        origens.append(
            {
                "id": origem_id,
                "tipo": "CTI",
                "ferramenta": ferramenta,
                "dominio": dominio or None,
                "filtros": argumentos,
                "total_retornado": resumo.get("total_retornado"),
                "erro": resumo.get("erro"),
                "execucao_atual": True,
            }
        )

    return origens, ids_por_evidencia, ids_web, ids_cti


def _linhas_afirmativas(texto: str) -> list[tuple[str, str | None]]:
    afirmacoes: list[tuple[str, str | None]] = []
    secao: str | None = None

    for linha_bruta in str(texto or "").splitlines():
        linha = linha_bruta.strip()
        if not linha:
            continue
        limpa = re.sub(r"^[\-•*]+\s*", "", linha)
        limpa = re.sub(r"^\(?\d+\)?[\.:\-]?\s*", "", limpa).strip()
        normalizada = _normalizar(limpa)
        if not normalizada:
            continue

        if "fatos externos verificados" in normalizada:
            secao = "WEB"
            continue
        if "dados internos cti" in normalizada:
            secao = "CTI"
            continue
        if "cruzamento e implica" in normalizada or normalizada.startswith("recomendações") or normalizada.startswith("recomendacoes"):
            secao = "INFERENCIA"
            continue
        if any(normalizada == titulo for titulo in _TITULOS_IGNORADOS):
            continue
        if normalizada.startswith("se desejar"):
            continue
        afirmacoes.append((limpa[:1200], secao))

    return afirmacoes


def _dominios_dominantes(texto: str) -> list[str]:
    normalizado = _normalizar(texto)
    dominios: list[str] = []
    for dominio, expressoes in _DOMINIOS_DOMINANTES:
        if any(expressao in normalizado for expressao in expressoes):
            dominios.append(dominio)
    return list(dict.fromkeys(dominios))


def _dominio_dominante(texto: str) -> str | None:
    dominios = _dominios_dominantes(texto)
    return dominios[0] if dominios else None


def _ids_cti_por_texto(texto: str, ids_por_evidencia: dict[str, list[str]], ids_cti: list[str]) -> list[str]:
    normalizado = _normalizar(texto)

    dominante = _dominio_dominante(texto)
    if dominante:
        return list(dict.fromkeys(ids_por_evidencia.get(dominante, [])))

    candidatos: list[str] = []
    evidencias_reconhecidas: list[str] = []

    for evidencia, termos in _DOMINIO_TERMOS.items():
        if any(termo in normalizado for termo in termos):
            evidencias_reconhecidas.append(evidencia)
            candidatos.extend(ids_por_evidencia.get(evidencia, []))

    candidatos = list(dict.fromkeys(candidatos))
    if candidatos:
        return candidatos

    if evidencias_reconhecidas:
        return []

    if len(ids_cti) == 1:
        return list(ids_cti)
    return []


def _entidades_web_texto(texto: str) -> list[str]:
    entidades: list[str] = []
    for token in re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ0-9_-]{3,}\b", str(texto or "")):
        normalizado = token.casefold()
        if normalizado in _WEB_ENTIDADES_IGNORADAS:
            continue
        entidades.append(normalizado)
    return list(dict.fromkeys(entidades))


def _ids_web_por_texto(texto: str, origens: list[dict[str, Any]], ids_web: list[str]) -> list[str]:
    entidades = _entidades_web_texto(texto)
    if not entidades:
        return list(ids_web)

    compativeis: list[str] = []
    for origem in origens:
        if origem.get("tipo") != "WEB":
            continue
        corpus = f"{str(origem.get('descricao') or '')} {str(origem.get('url') or '')}".casefold()
        if any(entidade in corpus for entidade in entidades):
            compativeis.append(str(origem.get("id")))
    return list(dict.fromkeys(compativeis))


def _eh_inferencia(texto: str, secao: str | None) -> bool:
    if secao == "INFERENCIA":
        return True
    normalizado = _normalizar(texto)
    return any(marcador in normalizado for marcador in _INFERENCIA_MARCADORES)


def _premissas_fatuais_inferencia(
    texto: str,
    ids_por_evidencia: dict[str, list[str]],
) -> tuple[list[str], list[str]]:
    exigidas = _dominios_dominantes(texto)
    nao_sustentadas = [dominio for dominio in exigidas if not ids_por_evidencia.get(dominio)]
    return exigidas, nao_sustentadas


def construir_auditoria_evidencial(
    resposta_texto: str,
    metadados: dict[str, Any],
    pergunta_atual: str,
) -> dict[str, Any]:
    origens, ids_por_evidencia, ids_web, ids_cti = _origens_execucao(metadados)
    requeridas = {str(x) for x in (metadados.get("evidencias_requeridas") or [])}
    atendidas = {str(x) for x in (metadados.get("evidencias_atendidas") or [])}
    faltantes = sorted(requeridas - atendidas)

    afirmacoes: list[dict[str, Any]] = []
    sem_evidencia = 0
    inferencias_base_parcial = 0
    for indice, (texto, secao) in enumerate(_linhas_afirmativas(resposta_texto), start=1):
        if _eh_inferencia(texto, secao):
            derivada_de = list(dict.fromkeys(ids_cti + ids_web))
            premissas_exigidas, premissas_nao_sustentadas = _premissas_fatuais_inferencia(texto, ids_por_evidencia)
            if premissas_nao_sustentadas:
                status = "BASE_PARCIAL"
                inferencias_base_parcial += 1
            elif derivada_de:
                status = "RASTREAVEL"
            else:
                status = "SEM_BASE_EXPLICITA"
            afirmacoes.append(
                {
                    "id": f"A{indice}",
                    "texto": texto,
                    "tipo": "INFERENCIA_RECOMENDACAO",
                    "fontes_evidencia": [],
                    "derivada_de": derivada_de,
                    "premissas_fatuais_exigidas": premissas_exigidas,
                    "premissas_fatuais_nao_sustentadas": premissas_nao_sustentadas,
                    "status_rastreabilidade": status,
                }
            )
            continue

        fontes_evidencia: list[str] = []
        tipo = "FATO"
        if secao == "WEB":
            tipo = "FATO_WEB"
            fontes_evidencia = _ids_web_por_texto(texto, origens, ids_web)
        elif secao == "CTI":
            tipo = "FATO_CTI"
            fontes_evidencia = _ids_cti_por_texto(texto, ids_por_evidencia, ids_cti)
        elif ids_cti and not ids_web:
            tipo = "FATO_CTI"
            fontes_evidencia = _ids_cti_por_texto(texto, ids_por_evidencia, ids_cti)
        elif ids_web and not ids_cti:
            tipo = "FATO_WEB"
            fontes_evidencia = _ids_web_por_texto(texto, origens, ids_web)
        else:
            fontes_evidencia = _ids_cti_por_texto(texto, ids_por_evidencia, ids_cti)
            if fontes_evidencia:
                tipo = "FATO_CTI"

        status = "RASTREAVEL" if fontes_evidencia else "SEM_EVIDENCIA_EXPLICITA"
        if not fontes_evidencia:
            sem_evidencia += 1
        afirmacoes.append(
            {
                "id": f"A{indice}",
                "texto": texto,
                "tipo": tipo,
                "fontes_evidencia": fontes_evidencia,
                "derivada_de": [],
                "status_rastreabilidade": status,
            }
        )

    auditoria = {
        "versao": "IA-006-v1",
        "controle": "ia006_cadeia_afirmacao_evidencia_origem",
        "pergunta_atual": str(pergunta_atual or "")[:12000],
        "historico_conta_como_evidencia": False,
        "evidencias_requeridas": sorted(requeridas),
        "evidencias_atendidas": sorted(atendidas),
        "evidencias_necessarias_nao_consultadas": faltantes,
        "recorte_temporal": metadados.get("controle_temporal_pergunta"),
        "recorte_base": metadados.get("controle_recorte_base"),
        "origens_execucao": origens,
        "afirmacoes": afirmacoes,
        "totais": {
            "origens": len(origens),
            "afirmacoes": len(afirmacoes),
            "afirmacoes_sem_evidencia_explicita": sem_evidencia,
            "inferencias_recomendacoes": sum(1 for item in afirmacoes if item.get("tipo") == "INFERENCIA_RECOMENDACAO"),
            "inferencias_base_parcial": inferencias_base_parcial,
        },
    }

    resultado = {
        "controle_auditoria_evidencial": "ia006_cadeia_afirmacao_evidencia_origem",
        "auditoria_evidencial": auditoria,
        "auditoria_afirmacoes_total": len(afirmacoes),
        "auditoria_afirmacoes_sem_evidencia": sem_evidencia,
        "auditoria_inferencias_base_parcial": inferencias_base_parcial,
        "auditoria_fontes_total": len(origens),
        "auditoria_evidencias_faltantes": faltantes,
    }

    fatos_rastreaveis = any(
        item.get("tipo") in {"FATO_CTI", "FATO_WEB"}
        and item.get("status_rastreabilidade") == "RASTREAVEL"
        for item in afirmacoes
    )
    if requer_planejamento(pergunta_atual) and fatos_rastreaveis:
        texto_planejado, metadados_planejamento = construir_planejamento_comercial(
            pergunta_atual=pergunta_atual,
            resposta_texto=resposta_texto,
            metadados={"auditoria_evidencial": auditoria},
        )
        resultado.update(metadados_planejamento)
        if texto_planejado.startswith(resposta_texto):
            resultado["planejamento_texto_renderizado"] = texto_planejado[len(resposta_texto):].strip()

    return resultado
