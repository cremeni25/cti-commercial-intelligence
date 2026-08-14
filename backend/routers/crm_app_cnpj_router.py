from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core.supabase_client import supabase
from services.cnpj_enrichment_service import consultar_cnpj_publico, somente_digitos

router = APIRouter(prefix="/crm-app/clientes", tags=["CRM App"])


def _existente(cnpj: str):
    for tabela in ("clientes", "cti_clientes"):
        try:
            itens = supabase.table(tabela).select("*").eq("cnpj", cnpj).limit(1).execute().data or []
        except Exception:
            itens = []
        if itens:
            item = itens[0]
            return {
                "id": item.get("id"),
                "nome": item.get("nome") or item.get("cliente") or item.get("razao_social") or item.get("nome_fantasia"),
                "cnpj": cnpj,
                "cidade": item.get("cidade") or item.get("municipio"),
                "estado": item.get("estado") or item.get("uf"),
                "origem_cadastro": tabela,
            }
    return None


@router.get("/cnpj/{cnpj}")
def consultar_cnpj_cliente(cnpj: str):
    normalizado = somente_digitos(cnpj)
    existente = _existente(normalizado) if normalizado else None
    if existente:
        return {"status": "CLIENTE_EXISTENTE", "cnpj": normalizado, "cliente": existente, "fonte": "CTI"}

    resultado = consultar_cnpj_publico(normalizado)
    if not resultado.get("ok"):
        tipo = resultado.get("tipo")
        status_code = 422 if tipo == "CNPJ_INVALIDO" else 404 if tipo == "NAO_ENCONTRADO" else 503
        raise HTTPException(status_code=status_code, detail=resultado.get("detail") or "Não foi possível consultar o CNPJ.")

    return {"status": "ENCONTRADO", "cnpj": normalizado, "dados": resultado["dados"], "fonte": resultado["dados"].get("fonte")}
