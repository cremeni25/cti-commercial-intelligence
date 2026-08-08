from datetime import datetime, timezone
import os
import re
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client

from backend.services.schema_compat import insert_schema_compatible, update_schema_compatible

router = APIRouter(prefix="/crm-app", tags=["CRM App"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CRM_APP_BACKEND_VERSION = "2026.08.08-clientes-cadastro-completo-v2"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase não configurado")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class ClienteContexto(BaseModel):
    id: Optional[str] = None
    nome: str
    cidade: Optional[str] = None
    estado: Optional[str] = None
    segmento: Optional[str] = None
    categoria: Optional[str] = None
    ddd: Optional[str] = None
    sub_regiao: Optional[str] = None


class ClienteCreate(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    contato: Optional[str] = None
    fone: Optional[str] = None
    email: Optional[str] = None
    email_xml: Optional[str] = None
    categoria: Optional[str] = "TRANSPORTADORA"
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


def _so_digitos(valor: Any) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def _chave_nome(valor: Any) -> str:
    return re.sub(r"\s+", " ", str(valor or "").strip()).casefold()


def _normalizar_probabilidade(valor: Any) -> int:
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError):
        return 0
    if 0 < numero <= 1:
        numero *= 100
    return int(round(max(0, min(100, numero))))


def _normalizar_valor(valor: Any) -> float:
    try:
        numero = float(valor or 0)
    except (TypeError, ValueError) as erro:
        raise HTTPException(status_code=422, detail="Valor estimado inválido.") from erro
    if numero < 0:
        raise HTTPException(status_code=422, detail="O valor estimado não pode ser negativo.")
    return round(numero, 2)


def _validar_titulo(titulo: str) -> str:
    titulo_normalizado = (titulo or "").strip()
    if not titulo_normalizado:
        raise HTTPException(status_code=422, detail="Informe o título da oportunidade.")
    return titulo_normalizado


def _nome_cliente(item: dict[str, Any]) -> str:
    return str(
        item.get("razao_social")
        or item.get("nome_fantasia")
        or item.get("nome")
        or item.get("cliente")
        or item.get("empresa")
        or ""
    ).strip()


def _clientes_unificados() -> list[dict[str, Any]]:
    por_chave: dict[str, dict[str, Any]] = {}

    # A tabela clientes é o cadastro operacional atual e tem prioridade de ID/campos.
    # cti_clientes complementa registros históricos que ainda não foram materializados.
    for tabela in ("cti_clientes", "clientes"):
        try:
            registros = supabase.table(tabela).select("*").execute().data or []
        except Exception:
            registros = []

        for item in registros:
            nome = _nome_cliente(item)
            if not nome:
                continue
            cnpj = _so_digitos(item.get("cnpj"))
            chave = f"cnpj:{cnpj}" if cnpj else f"nome:{_chave_nome(nome)}"
            atual = por_chave.get(chave, {})
            normalizado = {
                **atual,
                **item,
                "nome": nome,
                "cnpj": cnpj or item.get("cnpj"),
                "cidade": item.get("cidade") or item.get("municipio") or atual.get("cidade"),
                "estado": item.get("estado") or item.get("uf") or atual.get("estado"),
                "categoria": item.get("categoria") or item.get("segmento") or atual.get("categoria"),
                "origem_cadastro": tabela,
            }
            por_chave[chave] = normalizado

    return sorted(por_chave.values(), key=lambda item: _nome_cliente(item).casefold())


def _payload_cliente(cliente: ClienteCreate | ClienteContexto) -> dict[str, Any]:
    dados = cliente.model_dump()
    nome = str(dados.get("nome") or "").strip()
    categoria = str(dados.get("categoria") or dados.get("segmento") or "TRANSPORTADORA").strip().upper()
    payload = {
        "nome": nome,
        "cnpj": _so_digitos(dados.get("cnpj")) or None,
        "inscricao_estadual": str(dados.get("inscricao_estadual") or "").strip() or None,
        "endereco": str(dados.get("endereco") or "").strip() or None,
        "numero": str(dados.get("numero") or "").strip() or None,
        "complemento": str(dados.get("complemento") or "").strip() or None,
        "bairro": str(dados.get("bairro") or "").strip() or None,
        "cidade": str(dados.get("cidade") or "").strip() or None,
        "estado": str(dados.get("estado") or "").strip().upper() or None,
        "cep": _so_digitos(dados.get("cep")) or None,
        "contato": str(dados.get("contato") or "").strip() or None,
        "fone": str(dados.get("fone") or "").strip() or None,
        "email": str(dados.get("email") or "").strip().lower() or None,
        "email_xml": str(dados.get("email_xml") or "").strip().lower() or None,
        "categoria": categoria,
        "segmento": categoria,
        "ddd": _so_digitos(dados.get("ddd")) or None,
        "sub_regiao": str(dados.get("sub_regiao") or "").strip() or None,
        "status": "ATIVO",
        "updated_at": _now(),
    }
    return payload


def _criar_ou_atualizar_cliente(cliente: ClienteCreate | ClienteContexto) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = _payload_cliente(cliente)
    nome = payload["nome"]
    if not nome:
        raise HTTPException(status_code=422, detail="Informe o nome / razão social do cliente.")

    cliente_id = str(getattr(cliente, "id", None) or "").strip()
    if cliente_id:
        existente = supabase.table("clientes").select("*").eq("id", cliente_id).limit(1).execute().data or []
        if existente:
            resposta, compat = update_schema_compatible(supabase, "clientes", cliente_id, payload)
            return (resposta or existente)[0], compat

    candidatos: list[dict[str, Any]] = []
    if payload.get("cnpj"):
        try:
            candidatos = supabase.table("clientes").select("*").eq("cnpj", payload["cnpj"]).limit(1).execute().data or []
        except Exception:
            candidatos = []
    if not candidatos:
        candidatos = supabase.table("clientes").select("*").ilike("nome", nome).limit(1).execute().data or []

    if candidatos:
        existente = candidatos[0]
        resposta, compat = update_schema_compatible(supabase, "clientes", str(existente["id"]), payload)
        return (resposta or existente)[0], compat

    criado, compat = insert_schema_compatible(supabase, "clientes", payload, protected_fields={"nome"})
    if not criado:
        raise HTTPException(status_code=500, detail="O cliente não foi criado no banco de dados.")
    return criado[0], compat


def _contexto_comercial(dados: ClienteOportunidadeCreate) -> dict[str, Any]:
    return {
        "linhas": dados.oportunidade.linha_equipamentos,
        "equipamentos": dados.oportunidade.equipamento,
        "municipio": dados.oportunidade.municipio or dados.cliente.cidade,
        "uf": dados.oportunidade.estado or dados.cliente.estado,
        "ddd": dados.cliente.ddd or dados.oportunidade.ddd,
        "sub_regiao": dados.cliente.sub_regiao or dados.oportunidade.sub_regiao,
        "segmento": dados.cliente.segmento or dados.cliente.categoria,
    }


def _descricao_com_contexto(descricao: Optional[str], contexto: dict[str, Any]) -> str:
    base = (descricao or "").strip()
    linhas = [base] if base else []
    linhas.append("[CONTEXTO CTI]")
    for chave, valor in contexto.items():
        if valor:
            linhas.append(f"{chave}: {valor}")
    return "\n".join(linhas)


def _registrar_auxiliar(table: str, payload: dict[str, Any], avisos: list[str], nome: str) -> None:
    try:
        _, compat = insert_schema_compatible(supabase, table, payload)
        if compat["removed_fields"]:
            avisos.append(f"{nome}: campos não existentes ignorados {list(compat['removed_fields'])}")
    except Exception as erro:
        avisos.append(f"{nome}: {erro}")


@router.get("/version")
def versao_crm_app():
    return {
        "version": CRM_APP_BACKEND_VERSION,
        "status": "ready",
        "opportunity_write_mode": "integer-percentage-contract",
        "probability_storage": "integer-0-100",
    }


@router.get("/clientes")
def listar_clientes_crm_app():
    return _clientes_unificados()


@router.post("/clientes")
def criar_cliente_crm_app(dados: ClienteCreate):
    cliente, compat = _criar_ou_atualizar_cliente(dados)
    return {"cliente": cliente, "compatibilidade": compat, "backend_version": CRM_APP_BACKEND_VERSION}


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
        probabilidade = _normalizar_probabilidade(oportunidade.probabilidade)
        valor_estimado = _normalizar_valor(oportunidade.valor_estimado)
        payload = {
            "cliente_id": cliente_id,
            "responsavel_id": oportunidade.responsavel_id,
            "titulo": _validar_titulo(oportunidade.titulo),
            "descricao": _descricao_com_contexto(oportunidade.descricao, contexto),
            "origem": "CRM_APP",
            "status": "OPORTUNIDADE",
            "valor_estimado": valor_estimado,
            "probabilidade": probabilidade,
            "data_fechamento_prevista": oportunidade.data_fechamento_prevista,
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
        agora = datetime.now(timezone.utc)
        etapa = "pipeline"
        _registrar_auxiliar(
            "cti_pipeline",
            {
                "oportunidade_id": oportunidade_id,
                "etapa_anterior": None,
                "nova_etapa": "OPORTUNIDADE",
                "etapa": "OPORTUNIDADE",
                "usuario_id": oportunidade.responsavel_id,
                "observacao": "Primeira movimentação automática da oportunidade.",
                "data": agora.date().isoformat(),
                "hora": agora.time().replace(microsecond=0).isoformat(),
            },
            avisos,
            "pipeline",
        )
        etapa = "historico"
        _registrar_auxiliar(
            "cti_oportunidade_historico",
            {
                "oportunidade_id": oportunidade_id,
                "tipo": "OPORTUNIDADE",
                "descricao": "Oportunidade criada pelo App CRM.",
                "usuario_id": oportunidade.responsavel_id,
                "payload": {
                    "oportunidade": oportunidade_criada,
                    "contexto_comercial": contexto,
                    "backend_version": CRM_APP_BACKEND_VERSION,
                },
                "created_at": _now(),
            },
            avisos,
            "histórico",
        )
        return {
            "cliente": cliente,
            "oportunidade": oportunidade_criada,
            "contexto_comercial": contexto,
            "normalizacao": {"valor_estimado": valor_estimado, "probabilidade": probabilidade},
            "compatibilidade": {"cliente": compat_cliente, "oportunidade": compat_oportunidade},
            "backend_version": CRM_APP_BACKEND_VERSION,
            "avisos": avisos,
        }
    except HTTPException:
        raise
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Não foi possível gravar a oportunidade na etapa {etapa}. backend={CRM_APP_BACKEND_VERSION}",
        ) from erro
