from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from planilha_engine_viena import (
    processar_planilha_viena
)

from supabase import create_client

from collections import Counter

from core.score_engine import (
    consolidar_scores
)

import os


router = APIRouter()


SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ======================================
# INTELIGÊNCIA OPERACIONAL
# ======================================
def gerar_inteligencia_operacional(
    registros
):

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
        r.get("implementador", "")
        for r in registros
        if r.get("implementador")
    )

    ranking_estados = (
        estados.most_common(10)
    )

    ranking_produtos = (
        produtos.most_common(10)
    )

    ranking_implementadoras = (
        implementadoras.most_common(10)
    )

    insights = []

    # ===============================
    # INSIGHT ESTADOS
    # ===============================
    if ranking_estados:

        estado_top = ranking_estados[0]

        insights.append(
            f"O estado com maior volume operacional é {estado_top[0]} com {estado_top[1]} registros."
        )

    # ===============================
    # INSIGHT PRODUTOS
    # ===============================
    if ranking_produtos:

        produto_top = ranking_produtos[0]

        insights.append(
            f"O produto dominante da operação é {produto_top[0]} com {produto_top[1]} ocorrências."
        )

    # ===============================
    # INSIGHT IMPLEMENTADORAS
    # ===============================
    if ranking_implementadoras:

        impl_top = (
            ranking_implementadoras[0]
        )

        insights.append(
            f"A implementadora com maior presença operacional é {impl_top[0]} com {impl_top[1]} registros."
        )

    # ===============================
    # INSIGHT VOLUME
    # ===============================
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

        "total_registros":
            total_registros,

        "total_valor":
            total_valor,

        "ranking_estados":
            ranking_estados,

        "ranking_produtos":
            ranking_produtos,

        "ranking_implementadoras":
            ranking_implementadoras,

        "insights":
            insights
    }


# ======================================
# UPLOAD ANFIR SEGURO
# ======================================
@router.post("/upload/anfir/seguro")
async def upload_anfir_seguro(
    file: UploadFile = File(...)
):

    try:

        contents = await file.read()

        registros = processar_planilha_viena(contents)

        inteligencia = (
            gerar_inteligencia_operacional(
                registros
            )
        )

        score = consolidar_scores(
            registros
        )

        registros_processados = []

        for r in registros:

            registros_processados.append({

                "ano":
                    r.get("ano"),

                "mes":
                    r.get("mes"),

                "estado":
                    r.get("estado"),

                "linha":
                    r.get("linha"),

                "implementador":
                    r.get("implementador"),

                "valor":
                    float(
                        r.get(
                            "valor",
                            0
                        )
                    ),

                "score_inicial":
                    r.get(
                        "score_inicial",
                        0
                    ),

                "classificacao":
                    r.get(
                        "classificacao",
                        ""
                    ),

                "origem":
                    r.get(
                        "origem",
                        ""
                    )
            })

        batch_size = 500

        for i in range(
            0,
            len(registros_processados),
            batch_size
        ):

            batch = (
                registros_processados[
                    i:i + batch_size
                ]
            )

            supabase.table(
                "cti_anfir"
            ).insert(batch).execute()

        return {

            "status":
                "ANFIR atualizado",

            "registros_inseridos":
                len(
                    registros_processados
                ),

            "inteligencia": inteligencia,

            "scores": scores
        }

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=(
                f"Erro ao processar planilha: {str(e)}"
            )
        )

