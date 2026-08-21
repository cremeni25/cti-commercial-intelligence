from datetime import datetime, timezone
import unicodedata

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.supabase_client import supabase

router = APIRouter()


class Venda(BaseModel):
    cliente_id: str
    tipo_venda: str
    valor: float
    data_venda: str
    observacao: str | None = None
    equipamento_id: str | None = None
    implementador_id: str | None = None
    pedido_id: str | None = None
    oportunidade_id: str | None = None
    item_oportunidade_id: str | None = None
    equipamento_codigo: str | None = None
    implementadora_id: str | None = None


class ConcluirVendaPedidoRequest(BaseModel):
    confirmar: bool = False
    tipo_venda: str = "EQUIPAMENTO"
    observacao: str | None = None


def _opcional(tabela: str, registro_id: str | None):
    if not registro_id:
        return None
    try:
        dados = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    except Exception:
        return None
    return dados[0] if dados else None


def _normalizar(valor: object) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return "".join(caractere for caractere in texto.upper() if caractere.isalnum())


def _resolver_equipamento_codigo(item: dict, snapshot: dict) -> str | None:
    candidatos = [
        item.get("equipamento_codigo"),
        item.get("equipamento"),
        item.get("modelo_base"),
        item.get("nome_comercial"),
        snapshot.get("equipamento_codigo"),
        snapshot.get("equipamento"),
        snapshot.get("modelo_base"),
        snapshot.get("nome_comercial"),
    ]
    termos = {_normalizar(valor) for valor in candidatos if _normalizar(valor)}
    if not termos:
        return None

    try:
        catalogo = supabase.table("cti_catalogo_equipamentos").select("codigo,modelo_base,nome_comercial").eq("ativo", True).execute().data or []
    except Exception:
        catalogo = []

    for registro in catalogo:
        valores = {
            _normalizar(registro.get("codigo")),
            _normalizar(registro.get("modelo_base")),
            _normalizar(registro.get("nome_comercial")),
        }
        if termos.intersection(valores):
            return str(registro.get("codigo"))

    for registro in catalogo:
        valores = [
            _normalizar(registro.get("codigo")),
            _normalizar(registro.get("modelo_base")),
            _normalizar(registro.get("nome_comercial")),
        ]
        if any((termo in valor or valor in termo) for termo in termos for valor in valores if valor and len(valor) >= 3):
            return str(registro.get("codigo"))
    return None


def _resolver_implementadora(pedido: dict, proposta: dict, oportunidade: dict, item: dict, snapshot: dict) -> str | None:
    ids = [
        pedido.get("implementadora_id"),
        pedido.get("implementador_id"),
        proposta.get("implementadora_id"),
        proposta.get("implementador_id"),
        oportunidade.get("implementadora_id"),
        oportunidade.get("implementador_id"),
        item.get("implementadora_id"),
        item.get("implementador_id"),
        snapshot.get("implementadora_id"),
        snapshot.get("implementador_id"),
    ]
    for valor in ids:
        if valor and _opcional("implementadoras", str(valor)):
            return str(valor)
    return None


def _enriquecer_venda(venda: dict) -> dict:
    enriquecida = dict(venda)

    cliente = _opcional("clientes", str(venda.get("cliente_id") or "")) or {}
    enriquecida["cliente_nome"] = cliente.get("nome") or venda.get("cliente_id") or "-"

    equipamento_codigo = venda.get("equipamento_codigo")
    if equipamento_codigo:
        enriquecida["equipamento_nome"] = equipamento_codigo
    else:
        equipamento = _opcional("equipamentos", str(venda.get("equipamento_id") or "")) or {}
        enriquecida["equipamento_nome"] = equipamento.get("modelo") or venda.get("equipamento_id") or "-"

    implementadora = {}
    if venda.get("implementadora_id") is not None:
        implementadora = _opcional("implementadoras", str(venda.get("implementadora_id"))) or {}
    if not implementadora and venda.get("implementador_id"):
        implementadora = _opcional("implementadores", str(venda.get("implementador_id"))) or {}
    enriquecida["implementadora_nome"] = implementadora.get("nome") or None

    pedido = _opcional("cti_pedidos", str(venda.get("pedido_id") or "")) or {}
    enriquecida["pedido_numero"] = pedido.get("numero") or venda.get("pedido_id") or "-"
    return enriquecida


@router.get("/vendas")
def listar_vendas():
    try:
        response = (
            supabase.table("vendas")
            .select("*")
            .or_("registro_teste.is.null,registro_teste.eq.false")
            .is_("arquivado_em", "null")
            .order("data_venda", desc=True)
            .execute()
        )
        return [_enriquecer_venda(venda) for venda in (response.data or [])]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vendas")
def criar_venda(venda: Venda):
    try:
        response = supabase.table("vendas").insert(venda.model_dump(exclude_none=True)).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vendas/pedidos/{pedido_id}/concluir")
def concluir_pedido_em_venda(pedido_id: str, dados: ConcluirVendaPedidoRequest):
    if not dados.confirmar:
        raise HTTPException(status_code=409, detail="Confirme expressamente a conclusão do pedido como venda.")

    pedido = _opcional("cti_pedidos", pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    try:
        existentes = supabase.table("vendas").select("*").eq("pedido_id", pedido_id).limit(1).execute().data or []
    except Exception:
        marcador = f"CTI_PEDIDO:{pedido_id}"
        try:
            existentes = supabase.table("vendas").select("*").ilike("observacao", f"%{marcador}%").limit(1).execute().data or []
        except Exception:
            existentes = []
    if existentes:
        return {"status": "JA_REGISTRADA", "venda": existentes[0]}

    proposta_id = pedido.get("proposta_id") or pedido.get("proposta_aceita_id")
    proposta = _opcional("cti_propostas", str(proposta_id or "")) or {}
    item_id = pedido.get("item_oportunidade_id") or proposta.get("item_oportunidade_id")
    item = _opcional("cti_oportunidade_itens", str(item_id or "")) or {}
    oportunidade_id = pedido.get("oportunidade_id") or proposta.get("oportunidade_id") or item.get("oportunidade_id")
    oportunidade = _opcional("cti_oportunidades", str(oportunidade_id or "")) or {}

    snapshot = proposta.get("snapshot_dados") if isinstance(proposta, dict) else {}
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    snapshot_item = snapshot.get("item") if isinstance(snapshot.get("item"), dict) else {}
    snapshot_contexto = {**snapshot, **snapshot_item}

    cliente_id = pedido.get("cliente_id") or proposta.get("cliente_id") or oportunidade.get("cliente_id")
    equipamento_codigo = _resolver_equipamento_codigo(item, snapshot_contexto)
    implementadora_id = _resolver_implementadora(pedido, proposta, oportunidade, item, snapshot_contexto)

    faltantes = []
    if not cliente_id:
        faltantes.append("cliente")
    if not equipamento_codigo:
        faltantes.append("equipamento do catálogo comercial")
    if faltantes:
        raise HTTPException(status_code=409, detail="O pedido ainda não possui vínculo suficiente para registrar a venda: " + ", ".join(faltantes) + ".")

    valor = float(pedido.get("valor") or proposta.get("valor") or item.get("valor_total") or 0)
    numero = str(pedido.get("numero") or pedido_id)
    equipamento = str(item.get("equipamento") or snapshot_contexto.get("equipamento") or equipamento_codigo)
    marcador = f"CTI_PEDIDO:{pedido_id}"
    observacoes = [marcador, f"Pedido {numero}", f"Equipamento {equipamento}"]
    if dados.observacao:
        observacoes.append(dados.observacao.strip())

    payload = {
        "cliente_id": str(cliente_id),
        "pedido_id": pedido_id,
        "oportunidade_id": str(oportunidade_id) if oportunidade_id else None,
        "item_oportunidade_id": str(item_id) if item_id else None,
        "equipamento_codigo": equipamento_codigo,
        "implementadora_id": implementadora_id,
        "tipo_venda": dados.tipo_venda.strip().upper() or "EQUIPAMENTO",
        "valor": valor,
        "data_venda": datetime.now(timezone.utc).date().isoformat(),
        "observacao": " | ".join(observacoes),
    }

    try:
        criado = supabase.table("vendas").insert({k: v for k, v in payload.items() if v is not None}).execute().data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível registrar a venda do pedido: {e}")

    if not criado:
        raise HTTPException(status_code=500, detail="A venda não confirmou gravação na base.")

    return {"status": "REGISTRADA", "venda": criado[0]}
