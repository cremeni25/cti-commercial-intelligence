from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase

router = APIRouter(prefix="/crm-seguro/feiras", tags=["feiras-eventos"])

class ItemIntencao(BaseModel):
    codigo_produto: str | None = None
    linha_produto: str = Field(min_length=2)
    nome_produto: str = Field(min_length=2)
    quantidade: int = Field(ge=1, le=100000)

class Atendimento(BaseModel):
    feira_id: str
    empresa: str = Field(min_length=2)
    cnpj: str | None = None
    visitante: str = Field(min_length=2)
    contato: str | None = None
    email: str | None = None
    cidade: str | None = None
    uf: str | None = None
    regiao: str = "A_CONFIRMAR"
    autorizado_destino: str | None = None
    interesse: str | None = None
    observacoes: str | None = None
    moeda: str | None = None
    valor_referencia: float | None = None
    itens: list[ItemIntencao] = Field(default_factory=list)

@router.get("")
def listar_feiras(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return supabase.table("cti_feiras").select("*").order("inicio", desc=True).execute().data or []

@router.get("/catalogo")
def catalogo(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return supabase.table("cti_catalogo_equipamentos").select("codigo,linha_produto,nome_comercial").eq("ativo",True).order("linha_produto").execute().data or []

@router.get("/{feira_id}/atendimentos")
def listar_atendimentos(feira_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    rows = supabase.table("cti_feira_atendimentos").select("*").eq("feira_id",feira_id).order("criado_em",desc=True).limit(1000).execute().data or []
    if rows:
        ids = [r["id"] for r in rows]
        itens = supabase.table("cti_feira_itens").select("*").in_("atendimento_id",ids).execute().data or []
        for r in rows:
            r["itens"] = [i for i in itens if i["atendimento_id"] == r["id"]]
    return rows

@router.post("/{feira_id}/atendimentos", status_code=201)
def registrar_atendimento(feira_id: str, entrada: Atendimento, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    if entrada.feira_id != feira_id:
        raise HTTPException(422,"Feira inconsistente.")
    if entrada.regiao not in {"VIENA","OUTRA","A_CONFIRMAR"}:
        raise HTTPException(422,"Região inválida.")
    if entrada.moeda not in {None,"BRL","USD"}:
        raise HTTPException(422,"Moeda inválida.")
    if entrada.valor_referencia is not None and entrada.valor_referencia < 0:
        raise HTTPException(422,"Valor inválido.")
    if not entrada.itens:
        raise HTTPException(422,"Informe ao menos um equipamento.")
    feiras = supabase.table("cti_feiras").select("id").eq("id",feira_id).limit(1).execute().data or []
    if not feiras:
        raise HTTPException(404,"Feira não localizada.")
    payload = entrada.model_dump(exclude={"itens","feira_id"})
    payload["feira_id"] = feira_id
    payload["criado_por"] = str(usuario.id)
    registro = supabase.table("cti_feira_atendimentos").insert(payload).execute().data
    if not registro:
        raise HTTPException(503,"Atendimento não confirmado.")
    atendimento = registro[0]
    try:
        itens = [dict(i.model_dump(),atendimento_id=atendimento["id"]) for i in entrada.itens]
        supabase.table("cti_feira_itens").insert(itens).execute()
    except Exception:
        supabase.table("cti_feira_atendimentos").delete().eq("id",atendimento["id"]).execute()
        raise HTTPException(503,"Itens não gravados; atendimento revertido.")
    return {"id":atendimento["id"],"status":"REGISTRADO"}
