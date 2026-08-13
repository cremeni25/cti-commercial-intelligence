from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.supabase_client import supabase
from backend.services.schema_compat import insert_schema_compatible, update_schema_compatible

router = APIRouter(prefix="/crm-app", tags=["CRM App"])


class ClienteEdicao(BaseModel):
    nome: str
    cnpj: str | None = None
    inscricao_estadual: str | None = None
    endereco: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    estado: str | None = None
    cep: str | None = None
    contato: str | None = None
    fone: str | None = None
    email: str | None = None
    email_xml: str | None = None
    categoria: str | None = "TRANSPORTADORA"
    ddd: str | None = None
    sub_regiao: str | None = None


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _digitos(valor: Any) -> str:
    return re.sub(r"\D", "", _texto(valor))


def _nome(item: dict[str, Any]) -> str:
    return _texto(item.get("nome") or item.get("razao_social") or item.get("nome_fantasia") or item.get("cliente") or item.get("empresa"))


def _payload(dados: ClienteEdicao) -> dict[str, Any]:
    nome = _texto(dados.nome)
    if len(nome) < 2 or not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", nome):
        raise HTTPException(status_code=422, detail="Informe um nome / razão social válido.")
    categoria = _texto(dados.categoria or "TRANSPORTADORA").upper()
    return {
        "nome": nome,
        "cnpj": _digitos(dados.cnpj) or None,
        "inscricao_estadual": _texto(dados.inscricao_estadual) or None,
        "endereco": _texto(dados.endereco) or None,
        "numero": _texto(dados.numero) or None,
        "complemento": _texto(dados.complemento) or None,
        "bairro": _texto(dados.bairro) or None,
        "cidade": _texto(dados.cidade) or None,
        "estado": _texto(dados.estado).upper() or None,
        "cep": _digitos(dados.cep) or None,
        "contato": _texto(dados.contato) or None,
        "fone": _texto(dados.fone) or None,
        "email": _texto(dados.email).lower() or None,
        "email_xml": _texto(dados.email_xml).lower() or None,
        "categoria": categoria,
        "segmento": categoria,
        "ddd": _digitos(dados.ddd) or None,
        "sub_regiao": _texto(dados.sub_regiao) or None,
        "status": "ATIVO",
        "updated_at": _agora(),
    }


def _localizar_unificado(cliente_id: str) -> dict[str, Any] | None:
    for tabela in ("clientes", "cti_clientes"):
        try:
            itens = supabase.table(tabela).select("*").eq("id", cliente_id).limit(1).execute().data or []
        except Exception:
            itens = []
        if itens:
            item = itens[0]
            return {
                **item,
                "nome": _nome(item),
                "cidade": item.get("cidade") or item.get("municipio"),
                "estado": item.get("estado") or item.get("uf"),
                "categoria": item.get("categoria") or item.get("segmento"),
                "origem_cadastro": tabela,
            }
    return None


@router.get("/clientes/{cliente_id}")
def obter_cliente_crm_app(cliente_id: str):
    cliente = _localizar_unificado(cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente


@router.put("/clientes/{cliente_id}")
def atualizar_cliente_crm_app(cliente_id: str, dados: ClienteEdicao):
    origem = _localizar_unificado(cliente_id)
    if not origem:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    payload = _payload(dados)
    alvo = supabase.table("clientes").select("*").eq("id", cliente_id).limit(1).execute().data or []
    if not alvo and payload.get("cnpj"):
        alvo = supabase.table("clientes").select("*").eq("cnpj", payload["cnpj"]).limit(1).execute().data or []
    if not alvo:
        alvo = supabase.table("clientes").select("*").ilike("nome", payload["nome"]).limit(1).execute().data or []

    if alvo:
        registro_id = str(alvo[0]["id"])
        atualizado, compat = update_schema_compatible(supabase, "clientes", registro_id, payload)
        cliente = (atualizado or alvo)[0]
    else:
        criado, compat = insert_schema_compatible(supabase, "clientes", payload, protected_fields={"nome"})
        if not criado:
            raise HTTPException(status_code=500, detail="Não foi possível materializar o cadastro canônico do cliente.")
        cliente = criado[0]

    return {
        "cliente": cliente,
        "compatibilidade": compat,
        "origem_anterior": origem.get("origem_cadastro"),
        "cadastro_canonico": "clientes",
    }
