from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.planilha_engine import processar_planilha_universal
from supabase import create_client
import os

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@router.post("/upload/anfir/seguro")
async def upload_anfir_seguro(file: UploadFile = File(...)):

    try:

        contents = await file.read()

        registros = processar_planilha_universal(contents)

        registros_processados = []

        for r in registros:

            registros_processados.append({
                "ano": r.get("ano"),
                "mes": r.get("mes"),
                "estado": r.get("estado"),
                "linha": r.get("linha"),
                "implementador": r.get("implementador"),
                "valor": float(r.get("valor", 0))
            })

        batch_size = 500

        for i in range(0, len(registros_processados), batch_size):

            batch = registros_processados[i:i + batch_size]

            supabase.table("cti_anfir").insert(batch).execute()

        return {
            "status": "ANFIR atualizado",
            "registros_inseridos": len(registros_processados)
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar planilha: {str(e)}"
        )
