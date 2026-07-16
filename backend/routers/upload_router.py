# ============================================================
# CTI - COMMERCIAL INTELLIGENCE
# Arquivo......: upload_router.py
# Versão.......: 1.0.0
# Status.......: ESTÁVEL
# Data.........: 24/06/2026
#
# Responsabilidade:
# - Receber arquivos enviados pelo frontend
# - Acionar o parser correspondente
# - Gerar inteligência operacional
# - Calcular score
# - Delegar persistência ao UploadEngine
#
# OBS:
# Este arquivo NÃO realiza mais gravação direta no Supabase.
# Toda persistência é responsabilidade do UploadEngine.
# ============================================================

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

import traceback

from collections import Counter

from parsers.viena_parser import processar_planilha_viena_com_relatorio

from core.score_engine import (
    consolidar_scores
)

from core.upload_engine import (
    UploadEngine
)

from repositories.cti_repository import repository

router = APIRouter()

upload_engine = UploadEngine()


# ============================================================
# INTELIGÊNCIA OPERACIONAL
# ============================================================

def gerar_inteligencia_operacional(registros):

    total_registros = len(registros)

    total_valor = sum(
        r.get("valor", 0)
        for r in registros
    )

    estados = Counter(
        r.get("estado", "")
        for r in registros
        if r.get("estado")
    )

    produtos = Counter(
        r.get("linha", "")
        for r in registros
        if r.get("linha")
    )

    implementadoras = Counter(
        r.get("implementadora", "")
        for r in registros
        if r.get("implementadora")
    )

    ranking_estados = estados.most_common(10)
    ranking_produtos = produtos.most_common(10)
    ranking_implementadoras = implementadoras.most_common(10)

    insights = []

    if ranking_estados:

        estado_top = ranking_estados[0]

        insights.append(
            f"O estado com maior volume operacional é {estado_top[0]} com {estado_top[1]} registros."
        )

    if ranking_produtos:

        produto_top = ranking_produtos[0]

        insights.append(
            f"O produto dominante da operação é {produto_top[0]} com {produto_top[1]} ocorrências."
        )

    if ranking_implementadoras:

        impl_top = ranking_implementadoras[0]

        insights.append(
            f"A implementadora com maior presença operacional é {impl_top[0]} com {impl_top[1]} registros."
        )

    if total_valor > 5000000:

        insights.append(
            "A operação apresenta alto volume financeiro consolidado."
        )

    elif total_valor > 1000000:

        insights.append(
            "A operação apresenta volume financeiro relevante."
        )

    else:

        insights.append(
            "A operação ainda possui baixo volume consolidado."
        )

    return {

        "total_registros": total_registros,

        "total_valor": total_valor,

        "ranking_estados": ranking_estados,

        "ranking_produtos": ranking_produtos,

        "ranking_implementadoras": ranking_implementadoras,

        "insights": insights
    }


# ============================================================
# ADAPTADOR DE PERSISTÊNCIA LEGADA
# ============================================================

def adaptar_payload_persistencia_legada(registros):

    payload = []

    for registro in registros:

        item = dict(registro)

        item["implementador"] = item.get(
            "implementadora"
        )

        item.pop(
            "implementadora",
            None
        )

        payload.append(item)

    return payload


# ============================================================
# UPLOAD CTI
# ============================================================

@router.post("/upload/anfir/seguro")
async def upload_anfir_seguro(
    file: UploadFile = File(...)
):

    try:

        contents = await file.read()

        registros_processados, relatorio = processar_planilha_viena_com_relatorio(
            contents,
            file.filename
        )

        if not registros_processados:
            relatorio["status"] = "SEM_REGISTROS_PROCESSADOS"
            return relatorio

        inteligencia = gerar_inteligencia_operacional(
            registros_processados
        )

        score = consolidar_scores(
            registros_processados
        )

        resultado_persistencia = {
            "inseridos": 0,
            "atualizados": 0,
            "duplicados_ignorados": 0,
            "erros": 0,
        }

        for origem_base in relatorio["bases_processadas"]:
            registros_base = [
                registro
                for registro in registros_processados
                if registro.get("origem_base") == origem_base
            ]

            resultado_base = repository.persistir_registros_idempotente(
                registros_base
            )

            relatorio["bases_processadas"][origem_base]["inseridos"] = (
                resultado_base["inseridos"]
            )
            relatorio["bases_processadas"][origem_base]["atualizados"] = (
                resultado_base["atualizados"]
            )
            relatorio["bases_processadas"][origem_base]["duplicados_ignorados"] += (
                resultado_base["duplicados_ignorados"]
            )
            relatorio["bases_processadas"][origem_base]["erros"] += (
                resultado_base["erros"]
            )

            for chave in resultado_persistencia:
                resultado_persistencia[chave] += resultado_base[chave]

        total_gravado = (
            resultado_persistencia["inseridos"]
            + resultado_persistencia["atualizados"]
            + resultado_persistencia["duplicados_ignorados"]
        )

        relatorio["status"] = (
            "PROCESSADO"
            if total_gravado > 0
            else "SEM_PERSISTENCIA"
        )
        relatorio["persistencia"] = resultado_persistencia
        relatorio["inteligencia"] = inteligencia
        relatorio["score"] = score

        return relatorio

    except Exception as e:

        erro = traceback.format_exc()

        print("\n")
        print("=" * 80)
        print("ERRO COMPLETO DO UPLOAD")
        print("=" * 80)
        print(erro)
        print("=" * 80)

        raise HTTPException(
            status_code=500,
            detail=erro
        )
