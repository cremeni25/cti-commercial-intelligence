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

from planilha_engine_viena import (
    processar_planilha_viena
)

from core.score_engine import (
    consolidar_scores
)

from core.upload_engine import (
    UploadEngine
)

from core.supabase_client import supabase

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
        r.get("implementador", "")
        for r in registros
        if r.get("implementador")
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
# UPLOAD CTI
# ============================================================

@router.post("/upload/anfir/seguro")
async def upload_anfir_seguro(
    file: UploadFile = File(...)
):

    try:

        contents = await file.read()

        registros = processar_planilha_viena(
            contents
        )

        inteligencia = gerar_inteligencia_operacional(
            registros
        )

        score = consolidar_scores(
            registros
        )

        registros_processados = []

        for r in registros:

            registros_processados.append({

                "ano": r.get("ano"),
                "mes": r.get("mes"),
                "data_venda": r.get("data_venda"),
                "cliente": r.get("cliente"),
                "cnpj": r.get("cnpj"),
                "cidade": r.get("cidade"),
                "estado": r.get("estado"),
                "ddd": r.get("ddd"),
                "regiao": r.get("regiao"),
                "placa": r.get("placa"),
                "chassi": r.get("chassi"),
                "implementador": r.get("implementador"),
                "linha": r.get("linha"),
                "modelo": r.get("modelo"),
                "responsavel": r.get("responsavel"),
                "valor": float(r.get("valor", 0)),
                "origem_dado": r.get("origem_dado", "VIENA"),
                "arquivo_origem": r.get("arquivo_origem"),

                "id_operacional": r.get("id_operacional"),
                "hash_registro": r.get("hash_registro"),

                "ativo": True

            })

        ids_lote = [
            r["id_operacional"]
            for r in registros_processados
            if r.get("id_operacional")
        ]

        existentes = (
            supabase
            .table("cti_anfir")
            .select("id_operacional")
            .in_("id_operacional", ids_lote)
            .execute()
        )

        ids_existentes = {
            r["id_operacional"]
            for r in (existentes.data or [])
        }

        registros_novos = [
            r
            for r in registros_processados
            if r.get("id_operacional") not in ids_existentes
        ]

        ignorados = (
            len(registros_processados)
            - len(registros_novos)
        )

        resultado_upload = upload_engine.processar(

            tabela="cti_anfir",

            registros=registros_novos

        )

        resultado_upload["ignorados"] = ignorados

        return {

            "status": "Upload realizado com sucesso",

            "upload": resultado_upload,

            "inteligencia": inteligencia,

            "score": score

        }

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