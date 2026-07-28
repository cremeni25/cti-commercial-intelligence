from datetime import datetime, timezone
import os
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from supabase import create_client

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


def _criar_ou_atualizar_cliente(cliente: ClienteContexto) -> dict[str, Any]:
    nome = cliente.nome.strip()
    if not nome:
        raise HTTPException(status_code=422, detail="Informe o nome do cliente.")

    base = {
        "nome": nome,
        "cidade": (cliente.cidade or "").strip() or None,
        "estado": (cliente.estado or "").strip().upper() or None,
        "segmento": (cliente.segmento or "TRANSPORTADOR").strip().upper(),
    }

    if cliente.id:
        existente = supabase.table("clientes").select("*").eq("id", cliente.id).execute().data or []
        if existente:
            atuais = existente[0]
            atualizacao = {chave: valor for chave, valor in base.items() if valor and not atuais.get(chave)}
            if atualizacao:
                try:
                    atualizacao.update({
                        "ddd": (cliente.ddd or "").strip() or None,
                        "sub_regiao": (cliente.sub_regiao or "").strip() or None,
                    })
                    resposta = supabase.table("clientes").update(atualizacao).eq("id", cliente.id).execute().data or []
                except Exception:
                    atualizacao.pop("ddd", None)
                    atualizacao.pop("sub_regiao", None)
                    resposta = supabase.table("clientes").update(atualizacao).eq("id", cliente.id).execute().data or []
                if resposta:
                    return resposta[0]
            return atuais

    candidatos = supabase.table("clientes").select("*").ilike("nome", nome).limit(1).execute().data or []
    if candidatos:
        return candidatos[0]

    try:
        payload = {
            **base,
            "ddd": (cliente.ddd or "").strip() or None,
            "sub_regiao": (cliente.sub_regiao or "").strip() or None,
        }
        criado = supabase.table("clientes").insert(payload).execute().data or []
    except Exception:
        criado = supabase.table("clientes").insert(base).execute().data or []

    if not criado:
        raise HTTPException(status_code=500, detail="O cliente não foi criado no banco de dados.")
    return criado[0]


@router.post("/cliente-oportunidade")
def criar_cliente_e_oportunidade(dados: ClienteOportunidadeCreate):
    etapa = "cliente"
    try:
        cliente = _criar_ou_atualizar_cliente(dados.cliente)
        cliente_id = str(cliente.get("id") or "")
        if not cliente_id:
            raise RuntimeError("Cliente criado sem identificador.")

        etapa = "oportunidade"
        oportunidade = dados.oportunidade
        payload = {
            "cliente_id": cliente_id,
            "responsavel_id": oportunidade.responsavel_id,
            "titulo": oportunidade.titulo.strip(),
            "descricao": oportunidade.descricao,
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
        criado = supabase.table("cti_oportunidades").insert(payload).execute().data or []
        if not criado:
            raise RuntimeError("A oportunidade não retornou registro após a inserção.")

        oportunidade_criada = criado[0]
        oportunidade_id = oportunidade_criada.get("id")
        avisos: list[str] = []

        etapa = "pipeline"
        try:
            agora = datetime.now(timezone.utc)
            supabase.table("cti_pipeline").insert({
                "oportunidade_id": oportunidade_id,
                "etapa_anterior": None,
                "nova_etapa": "OPORTUNIDADE",
                "etapa": "OPORTUNIDADE",
                "usuario_id": oportunidade.responsavel_id,
                "observacao": "Primeira movimentação automática da oportunidade.",
                "data": agora.date().isoformat(),
                "hora": agora.time().replace(microsecond=0).isoformat(),
            }).execute()
        except Exception as erro_pipeline:
            avisos.append(f"pipeline: {erro_pipeline}")

        etapa = "historico"
        try:
            supabase.table("cti_oportunidade_historico").insert({
                "oportunidade_id": oportunidade_id,
                "tipo": "OPORTUNIDADE",
                "descricao": "Oportunidade criada pelo App CRM.",
                "usuario_id": oportunidade.responsavel_id,
                "payload": {
                    **oportunidade_criada,
                    "territorio_cliente": {
                        "ddd": dados.cliente.ddd,
                        "sub_regiao": dados.cliente.sub_regiao,
                    },
                },
                "created_at": _now(),
            }).execute()
        except Exception as erro_historico:
            avisos.append(f"histórico: {erro_historico}")

        return {
            "cliente": cliente,
            "oportunidade": oportunidade_criada,
            "territorio": {
                "ddd": dados.cliente.ddd,
                "sub_regiao": dados.cliente.sub_regiao,
            },
            "avisos": avisos,
        }
    except HTTPException:
        raise
    except Exception as erro:
        raise HTTPException(status_code=500, detail=f"Falha na etapa {etapa}: {erro}") from erro
