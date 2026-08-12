from __future__ import annotations

from typing import Any

from services import ia_comercial_agente_crm as crm
from services import ia_comercial_universo as universo


ONTOLOGIA_COMERCIAL_CTI: dict[str, Any] = {
    "contexto_raiz": (
        "Inteligência comercial para transporte rodoviário refrigerado e implementos/equipamentos "
        "de transporte, com dados CRM, ANFIR, frota, território, equipamentos e mercado."
    ),
    "entidades": {
        "implementadora": {
            "definicao": (
                "Empresa do ecossistema de implementos/equipamentos de transporte representada no CTI/ANFIR, "
                "como fabricante/implementadora de carrocerias, baús, semirreboques, implementos ou estruturas "
                "rodoviárias associadas aos veículos e clientes do histórico CTI."
            ),
            "nao_e": [
                "consultoria ou integradora de software",
                "empresa implementadora de SAP, Oracle, ServiceNow, ERP ou core banking",
                "sinônimo de fabricante de equipamento de refrigeração",
            ],
            "fonte_identidade_atual": "implementadoras_cadastro",
            "fonte_analitica_historica": "historico_anfir",
            "campo_historico": "implementadora",
            "contexto_web_obrigatorio": (
                "implementos rodoviários, carrocerias, baús, semirreboques e equipamentos/estruturas para "
                "transporte rodoviário no Brasil"
            ),
        },
        "fabricante_equipamento": {
            "definicao": (
                "Fabricante do equipamento de refrigeração/controle de temperatura associado ao veículo, "
                "mantido como dimensão distinta de implementadora."
            ),
            "nao_e": ["implementadora", "transportadora", "cliente"],
            "fonte_analitica_historica": "historico_anfir",
            "campo_historico": "fabricante_equipamento",
        },
        "cliente": {
            "definicao": "Conta/empresa atendida comercialmente dentro do CRM e do histórico autorizado do CTI.",
            "fontes": ["clientes", "historico_anfir", "oportunidades", "vendas", "pedidos"],
        },
        "equipamento": {
            "definicao": (
                "Produto/equipamento comercial do portfólio de refrigeração para transporte, com linha e modelo "
                "próprios; não confundir com implemento rodoviário ou com fabricante do implemento."
            ),
            "fontes": ["catalogo_produtos", "historico_anfir", "itens_oportunidade", "vendas"],
        },
    },
}


CONTRATOS_ANALITICOS_FONTES: dict[str, dict[str, Any]] = {
    "historico_anfir": {
        "natureza": "fato_historico_analitico",
        "finalidades": [
            "frequência e ranking por ocorrência histórica",
            "tendências e distribuição territorial",
            "cruzamentos entre implementadora, cliente, equipamento, linha, modelo, fabricante e território",
        ],
        "permite_agregacao": True,
    },
    "implementadoras_cadastro": {
        "natureza": "dimensao_cadastral_atual",
        "finalidades": ["identidade", "existência", "status", "listagem cadastral atual"],
        "nao_usar_para": [
            "ranking por frequência histórica",
            "medir porte, participação, produção, faturamento ou volume de atuação",
            "substituir o histórico ANFIR",
        ],
        "permite_agregacao": False,
        "fonte_analitica_relacionada": "historico_anfir",
    },
    "catalogo_produtos": {
        "natureza": "dimensao_referencia",
        "finalidades": ["identidade de linhas/modelos", "aliases e portfólio oficial"],
        "permite_agregacao": False,
    },
    "perfil_usuario": {
        "natureza": "contexto_operacional",
        "finalidades": ["escopo", "perfil", "contextualização e RBAC"],
        "permite_agregacao": False,
    },
}


_ORIGINAL_CATALOGAR = universo.catalogar_universo_cti
_ORIGINAL_CONSULTAR = universo.consultar_universo_cti
_ORIGINAL_FONTES_REQUERIDAS = crm._fontes_requeridas_universais
_ORIGINAL_INSTRUCAO_FALTANTES = crm._instrucao_evidencias_faltantes_universal


INSTRUCOES_ONTOLOGIA = """

ONTOLOGIA COMERCIAL CTI — REGRA DE ESTABILIDADE SEMÂNTICA OBRIGATÓRIA:
- O significado comercial das entidades vem do catálogo/ontologia do CTI, não do significado genérico de uma palavra na internet.
- Antes de consultar dados internos ou executar web_search em uma pergunta CTI, consulte catalogar_universo_cti e use a ontologia e os contratos analíticos devolvidos para definir a classe da entidade e a finalidade correta da fonte.
- Uma fonte cadastral/dimensional serve para identidade, existência, status e referência. Não transforme quantidade de linhas cadastrais em ranking de porte, frequência, participação ou atuação.
- Uma fonte histórica/factual serve para análise temporal, frequência, ranking por ocorrência e cruzamentos quando seus campos suportarem a métrica solicitada.
- Se uma consulta for recusada por finalidade analítica incompatível, corrija o plano usando a fonte analítica relacionada; não tente contornar a recusa com outro campo do mesmo cadastro.
- IMPLEMENTADORA no universo CTI/ANFIR pertence ao ecossistema de implementos/equipamentos de transporte rodoviário (carrocerias, baús, semirreboques, implementos e estruturas rodoviárias). NÃO significa consultoria de tecnologia nem implementadora de SAP, Oracle, ServiceNow, ERP ou core banking.
- IMPLEMENTADORA também NÃO é sinônimo de FABRICANTE DE EQUIPAMENTO de refrigeração; preserve as dimensões separadas.
- Ao pesquisar na web uma entidade originada do CTI, mantenha obrigatoriamente a mesma classe semântica e o mesmo setor. Formule a busca externa com o contexto comercial da ontologia e descarte resultados de outro setor, mesmo que usem a mesma palavra.
- Para implementadoras, resultados web de SAP/ERP/Oracle/ServiceNow/TI são semanticamente inválidos e devem ser descartados; a pesquisa deve permanecer em implementos rodoviários/carrocerias/baús/semirreboques/equipamentos de transporte.
- Se o usuário pedir "maiores" e o CTI só sustentar frequência histórica, apresente explicitamente "maiores por frequência de registros no histórico CTI". Só apresente porte nacional por produção, faturamento ou market share quando a web trouxer métrica externa compatível e verificável.
- A mesma pergunta, repetida sem alteração, deve preservar entidade, setor, finalidade analítica e critério. Variação de fontes externas não autoriza mudança de ontologia.
"""


def catalogar_universo_cti(usuario_id: str, tipo_usuario: str) -> dict[str, Any]:
    resultado = _ORIGINAL_CATALOGAR(usuario_id, tipo_usuario)
    enriquecido = dict(resultado)
    enriquecido["ontologia_comercial"] = ONTOLOGIA_COMERCIAL_CTI
    enriquecido["contratos_analiticos"] = CONTRATOS_ANALITICOS_FONTES

    fontes = []
    for item in resultado.get("fontes") or []:
        if not isinstance(item, dict):
            continue
        fonte = dict(item)
        contrato = CONTRATOS_ANALITICOS_FONTES.get(str(fonte.get("fonte") or ""))
        if contrato:
            fonte["contrato_analitico"] = contrato
        fontes.append(fonte)
    enriquecido["fontes"] = fontes
    enriquecido["regra_semantica"] = (
        "Resolva primeiro a entidade pela ontologia CTI; escolha a fonte pela finalidade analítica; "
        "preserve a mesma classe semântica em qualquer pesquisa web."
    )
    return enriquecido


def _consulta_analiticamente_incompativel(
    fonte: str,
    *,
    agrupar_por: list[str] | None,
    metricas: list[dict[str, Any]] | None,
    ordenar_por: str | None,
) -> dict[str, Any] | None:
    contrato = CONTRATOS_ANALITICOS_FONTES.get(str(fonte or ""))
    if not contrato or contrato.get("permite_agregacao", True):
        return None

    possui_agregacao = bool(agrupar_por or metricas)
    if not possui_agregacao:
        return None

    retorno: dict[str, Any] = {
        "erro": "A fonte selecionada é cadastral/referencial e não pode ser usada para esse cálculo analítico.",
        "codigo": "FONTE_FINALIDADE_ANALITICA_INCOMPATIVEL",
        "fonte": fonte,
        "contrato_analitico": contrato,
        "orientacao": "Refaça o plano usando uma fonte factual/analítica compatível com a métrica solicitada.",
    }
    if contrato.get("fonte_analitica_relacionada"):
        retorno["fonte_analitica_sugerida"] = contrato["fonte_analitica_relacionada"]
    return retorno


def consultar_universo_cti(
    usuario_id: str,
    tipo_usuario: str,
    *,
    fonte: str,
    filtros: list[dict[str, Any]] | None = None,
    termo: str | None = None,
    agrupar_por: list[str] | None = None,
    metricas: list[dict[str, Any]] | None = None,
    ordenar_por: str | None = None,
    direcao: str = "desc",
    limite: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    incompatibilidade = _consulta_analiticamente_incompativel(
        fonte,
        agrupar_por=agrupar_por,
        metricas=metricas,
        ordenar_por=ordenar_por,
    )
    if incompatibilidade:
        return incompatibilidade

    resultado = _ORIGINAL_CONSULTAR(
        usuario_id,
        tipo_usuario,
        fonte=fonte,
        filtros=filtros,
        termo=termo,
        agrupar_por=agrupar_por,
        metricas=metricas,
        ordenar_por=ordenar_por,
        direcao=direcao,
        limite=limite,
        offset=offset,
    )
    if isinstance(resultado, dict):
        resultado = dict(resultado)
        resultado["contrato_analitico"] = CONTRATOS_ANALITICOS_FONTES.get(str(fonte or ""), {})
        resultado["ontologia_comercial"] = ONTOLOGIA_COMERCIAL_CTI
    return resultado


def _fontes_requeridas_com_ontologia(mensagem: str) -> set[str]:
    requeridas = set(_ORIGINAL_FONTES_REQUERIDAS(mensagem))
    if requeridas != {"web"}:
        requeridas.add("catalogo_cti")
    return requeridas


def _instrucao_faltantes_com_ontologia(faltantes: set[str]) -> str:
    passos: list[str] = []
    if "catalogo_cti" in faltantes:
        passos.append(
            "execute catalogar_universo_cti antes de escolher fonte interna ou pesquisar a web; use a ontologia "
            "e os contratos analíticos devolvidos para fixar entidade, setor e finalidade da fonte"
        )
    restante = set(faltantes) - {"catalogo_cti"}
    if restante:
        passos.append(_ORIGINAL_INSTRUCAO_FALTANTES(restante))
    return (
        "INSTRUÇÃO INTERNA DE ESTABILIDADE SEMÂNTICA: ainda não finalize. "
        + " ".join(passos)
    )


def aplicar_patch_ontologia() -> None:
    # O agente importa as funções do universo por valor; atualizamos os dois pontos.
    universo.catalogar_universo_cti = catalogar_universo_cti
    universo.consultar_universo_cti = consultar_universo_cti
    crm.catalogar_universo_cti = catalogar_universo_cti
    crm.consultar_universo_cti = consultar_universo_cti

    crm._fontes_requeridas_universais = _fontes_requeridas_com_ontologia
    crm._instrucao_evidencias_faltantes_universal = _instrucao_faltantes_com_ontologia
    if INSTRUCOES_ONTOLOGIA not in crm._INSTRUCOES_UNIVERSAIS:
        crm._INSTRUCOES_UNIVERSAIS += INSTRUCOES_ONTOLOGIA


aplicar_patch_ontologia()
