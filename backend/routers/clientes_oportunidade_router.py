from datetime import datetime, timezone
import os
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client

from backend.services.schema_compat import insert_schema_compatible, update_schema_compatible

router = APIRouter(prefix="/crm-app", tags=["CRM App"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase não configurado")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class ClienteContexto(BaseModel):
    id: Optional[str] = None
    nome: str
    cidade: Optional[str] = None
    estado: Optional[str] = None
    segmento: Optional[str] = None
    ddd: Optional[str] = None
    sub_regiao: Optional[str] = None


class OportunidadeContexto(BaseModel):
    responsavel_id: str
    titulo: str
    descricao: Optional[str] = None
    valor_estimado: float = 0
    probabilidade: float = 0
    data_fechamento_prevista: Optional[str] = None
    linha_equipamentos: Optional[str] = None
    equipamento: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    ddd: Optional[str] = None
    sub_regiao: Optional[str] = None


class ClienteOportunidadeCreate(BaseModel):
    cliente: ClienteContexto
    oportunidade: OportunidadeContexto


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalizar_probabilidade(valor: Any) -> float:
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        return 0
    numero = max(0, min(100, numero))
    return numero / 100 if numero > 1 else numero


def _contexto_comercial(dados: ClienteOportunidadeCreate) -> dict[str, Any]:
    return {
        "linhas": dados.oportunidade.linha_equipamentos,
        "equipamentos": dados.oportunidade.equipamento,
        "municipio": dados.oportunidade.municipio or dados.cliente.cidade,
        "uf": dados.oportunidade.estado or dados.cliente.estado,
        "ddd": dados.cliente.ddd or dados.oportunidade.ddd,
        "sub_regiao": dados.cliente.sub_regiao or dados.oportunidade.sub_regiao,
        "segmento": dados.cliente.segmento,
    }


def _descricao_com_contexto(descricao: Optional[str], contexto: dict[str, Any]) -> str:
    base = (descricao or "").strip()
    linhas = [base] if base else []
    linhas.append("[CONTEXTO CTI]")
    for chave, valor in contexto.items():
        if valor:
            linhas.append(f"{chave}: {valor}")
    return "\n".join(linhas)


def _criar_ou_atualizar_cliente(cliente: ClienteContexto) -> tuple[dict[str, Any], dict[str, Any]]:
    nome = cliente.nome.strip()
    if not nome:
        raise HTTPException(status_code=422, detail="Informe o nome do cliente.")

    payload = {
        "nome": nome,
        "cidade": (cliente.cidade or "").strip() or None,
        "estado": (cliente.estado or "").strip().upper() or None,
        "segmento": (cliente.segmento or "TRANSPORTADOR").strip().upper(),
        "ddd": (cliente.ddd or "").strip() or None,
        "sub_regiao": (cliente.sub_regiao or "").strip() or None,
    }

    if cliente.id:
        existente = supabase.table("clientes").select("*").eq("id", cliente.id).execute().data or []
        if existente:
            atuais = existente[0]
            atualizacao = {chave: valor for chave, valor in payload.items() if valor and not atuais.get(chave)}
            if atualizacao:
                resposta, compat = update_schema_compatible(supabase, "clientes", cliente.id, atualizacao)
                if resposta:
                    return resposta[0], compat
            return atuais, {"removed_fields": {}, "persisted_fields": []}

    candidatos = supabase.table("clientes").select("*").ilike("nome", nome).limit(1).execute().data or []
    if candidatos:
        existente = candidatos[0]
        atualizacao = {chave: valor for chave, valor in payload.items() if valor and not existente.get(chave)}
        if atualizacao and existente.get("id"):
            resposta, compat = update_schema_compatible(supabase, "clientes", str(existente["id"]), atualizacao)
            if resposta:
                return resposta[0], compat
        return existente, {"removed_fields": {}, "persisted_fields": []}

    criado, compat = insert_schema_compatible(
        supabase,
        "clientes",
        payload,
        protected_fields={"nome"},
    )
    if not criado:
        raise HTTPException(status_code=500, detail="O cliente não foi criado no banco de dados.")
    return criado[0], compat


def _registrar_auxiliar(table: str, payload: dict[str, Any], avisos: list[str], nome: str) -> None:
    try:
        _, compat = insert_schema_compatible(supabase, table, payload)
        if compat["removed_fields"]:
            avisos.append(f"{nome}: campos não existentes ignorados {list(compat['removed_fields'])}")
    except Exception as erro:
        avisos.append(f"{nome}: {erro}")


@router.post("/cliente-oportunidade")
def criar_cliente_e_oportunidade(dados: ClienteOportunidadeCreate):
    etapa = "cliente"
    try:
        cliente, compat_cliente = _criar_ou_atualizar_cliente(dados.cliente)
        cliente_id = str(cliente.get("id") or "")
        if not cliente_id:
            raise RuntimeError("Cliente criado sem identificador.")

        etapa = "oportunidade"
        oportunidade = dados.oportunidade
        contexto = _contexto_comercial(dados)
        payload = {
            "cliente_id": cliente_id,
            "responsavel_id": oportunidade.responsavel_id,
            "titulo": oportunidade.titulo.strip(),
            "descricao": _descricao_com_contexto(oportunidade.descricao, contexto),
            "origem": "CRM_APP",
            "status": "OPORTUNIDADE",
            "valor_estimado": oportunidade.valor_estimado,
            "probabilidade": _normalizar_probabilidade(oportunidade.probabilidade),
            "data_fechamento_prevista": oportunidade.data_fechamento_prevista,
            "linha_equipamentos": oportunidade.linha_equipamentos,
            "equipamento": oportunidade.equipamento,
            "municipio": oportunidade.municipio or cliente.get("cidade"),
            "estado": oportunidade.estado or cliente.get("estado"),
        }
        criado, compat_oportunidade = insert_schema_compatible(
            supabase,
            "cti_oportunidades",
            payload,
            protected_fields={"cliente_id", "titulo"},
        )
        if not criado:
            raise RuntimeError("A oportunidade não retornou registro após a inserção.")

        oportunidade_criada = criado[0]
        oportunidade_id = oportunidade_criada.get("id")
        avisos: list[str] = []

        if compat_cliente["removed_fields"]:
            avisos.append(f"cliente: campos não existentes preservados no contexto {list(compat_cliente['removed_fields'])}")
        if compat_oportunidade["removed_fields"]:
            avisos.append(f"oportunidade: campos não existentes preservados no histórico {list(compat_oportunidade['removed_fields'])}")

        agora = datetime.now(timezone.utc)
        etapa = "pipeline"
        _registrar_auxiliar("cti_pipeline", {
            "oportunidade_id": oportunidade_id,
            "etapa_anterior": None,
            "nova_etapa": "OPORTUNIDADE",
            "etapa": "OPORTUNIDADE",
            "usuario_id": oportunidade.responsavel_id,
            "observacao": "Primeira movimentação automática da oportunidade.",
            "data": agora.date().isoformat(),
            "hora": agora.time().replace(microsecond=0).isoformat(),
        }, avisos, "pipeline")

        etapa = "historico"
        _registrar_auxiliar("cti_oportunidade_historico", {
            "oportunidade_id": oportunidade_id,
            "tipo": "OPORTUNIDADE",
            "descricao": "Oportunidade criada pelo App CRM.",
            "usuario_id": oportunidade.responsavel_id,
            "payload": {
                "oportunidade": oportunidade_criada,
                "contexto_comercial": contexto,
                "campos_nao_persistidos": compat_oportunidade["removed_fields"],
            },
            "created_at": _now(),
        }, avisos, "histórico")

        return {
            "cliente": cliente,
            "oportunidade": oportunidade_criada,
            "contexto_comercial": contexto,
            "compatibilidade": {
                "cliente": compat_cliente,
                "oportunidade": compat_oportunidade,
            },
            "avisos": avisos,
        }
    except HTTPException:
        raise
    except Exception as erro:
        raise HTTPException(status_code=500, detail=f"Falha na etapa {etapa}: {erro}") from erro
