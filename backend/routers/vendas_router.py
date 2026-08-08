from datetime import datetime, timezone
import unicodedata

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.supabase_client import supabase

router = APIRouter()


class Venda(BaseModel):
    cliente_id: str
    equipamento_id: str
    implementador_id: str
    tipo_venda: str
    valor: float
    data_venda: str
    observacao: str | None = None


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


def _resolver_fk_textual(tabela: str, candidatos: list[object]) -> str | None:
    termos = [_normalizar(valor) for valor in candidatos if _normalizar(valor)]
    if not termos:
        return None
    try:
        registros = supabase.table(tabela).select("*").limit(500).execute().data or []
    except Exception:
        return None

    for registro in registros:
        registro_id = registro.get("id")
        if not registro_id:
            continue
        valores = [_normalizar(valor) for valor in registro.values() if isinstance(valor, (str, int, float))]
        if any(termo == valor for termo in termos for valor in valores if valor):
            return str(registro_id)

    for registro in registros:
        registro_id = registro.get("id")
        if not registro_id:
            continue
        valores = [_normalizar(valor) for valor in registro.values() if isinstance(valor, (str, int, float))]
        if any((termo in valor or valor in termo) for termo in termos for valor in valores if valor and len(valor) >= 3):
            return str(registro_id)
    return None


def _resolver_equipamento(item: dict, snapshot: dict) -> str | None:
    equipamento_id = item.get("equipamento_id")
    if equipamento_id and _opcional("equipamentos", str(equipamento_id)):
        return str(equipamento_id)

    return _resolver_fk_textual(
        "equipamentos",
        [
            item.get("equipamento_codigo"),
            item.get("equipamento"),
            item.get("modelo_base"),
            item.get("nome_comercial"),
            snapshot.get("equipamento_codigo"),
            snapshot.get("equipamento"),
            snapshot.get("modelo_base"),
            snapshot.get("nome_comercial"),
        ],
    )


def _resolver_implementador(pedido: dict, proposta: dict, oportunidade: dict, item: dict, snapshot: dict) -> str | None:
    ids = [
        pedido.get("implementador_id"),
        proposta.get("implementador_id"),
        oportunidade.get("implementador_id"),
        item.get("implementador_id"),
        snapshot.get("implementador_id"),
    ]
    for valor in ids:
        if valor and _opcional("implementadoras", str(valor)):
            return str(valor)

    return _resolver_fk_textual(
        "implementadoras",
        [
            pedido.get("implementador"),
            pedido.get("implementadora"),
            proposta.get("implementador"),
            proposta.get("implementadora"),
            oportunidade.get("implementador"),
            oportunidade.get("implementadora"),
            oportunidade.get("implementadora_nome"),
            item.get("implementador"),
            item.get("implementadora"),
            snapshot.get("implementador"),
            snapshot.get("implementadora"),
            snapshot.get("implementadora_nome"),
        ],
    )


@router.get("/vendas")
def listar_vendas():
    try:
        response = (
            supabase.table("vendas")
            .select("*")
            .order("data_venda", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vendas")
def criar_venda(venda: Venda):
    try:
        data = venda.model_dump()
        response = supabase.table("vendas").insert(data).execute()
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

    marcador = f"CTI_PEDIDO:{pedido_id}"
    try:
        existentes = (
            supabase.table("vendas")
            .select("*")
            .ilike("observacao", f"%{marcador}%")
            .limit(1)
            .execute()
            .data
            or []
        )
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
    equipamento_id = _resolver_equipamento(item, snapshot_contexto)
    implementador_id = _resolver_implementador(pedido, proposta, oportunidade, item, snapshot_contexto)

    faltantes = []
    if not cliente_id:
        faltantes.append("cliente")
    if not equipamento_id:
        faltantes.append("equipamento cadastrado na base de vendas")
    if not implementador_id:
        faltantes.append("implementadora vinculada ao pedido")
    if faltantes:
        raise HTTPException(
            status_code=409,
            detail="O pedido ainda não possui vínculo suficiente para registrar a venda: " + ", ".join(faltantes) + ".",
        )

    valor = float(pedido.get("valor") or proposta.get("valor") or item.get("valor_total") or 0)
    numero = str(pedido.get("numero") or pedido_id)
    equipamento = str(item.get("equipamento") or snapshot_contexto.get("equipamento") or "")
    observacoes = [marcador, f"Pedido {numero}"]
    if equipamento:
        observacoes.append(f"Equipamento {equipamento}")
    if dados.observacao:
        observacoes.append(dados.observacao.strip())

    payload = {
        "cliente_id": str(cliente_id),
        "equipamento_id": equipamento_id,
        "implementador_id": implementador_id,
        "tipo_venda": dados.tipo_venda.strip().upper() or "EQUIPAMENTO",
        "valor": valor,
        "data_venda": datetime.now(timezone.utc).date().isoformat(),
        "observacao": " | ".join(observacoes),
    }

    try:
        criado = supabase.table("vendas").insert(payload).execute().data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível registrar a venda do pedido: {e}")

    if not criado:
        raise HTTPException(status_code=500, detail="A venda não confirmou gravação na base.")

    return {"status": "REGISTRADA", "venda": criado[0]}
