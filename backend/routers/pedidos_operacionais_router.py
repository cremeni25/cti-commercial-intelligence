from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.supabase_client import supabase
from routers.propostas_pedidos_router import ConverterPedidoRequest, converter_em_pedido
from services.email_transport_service import (
    TransporteEmailNaoConfigurado,
    configuracao_email,
    enviar_email,
)

router = APIRouter(prefix="/crm-documentos", tags=["CRM Pedidos Operacionais"])


class ConverterPedidoOperacionalRequest(BaseModel):
    destinatarios: list[str] = Field(min_length=1)
    cc: list[str] = Field(default_factory=list)
    cco: list[str] = Field(default_factory=list)
    observacoes_envio: str | None = None
    responsavel_id: str | None = None
    data_pedido: str | None = None


class AtualizarDestinatariosPedidoRequest(BaseModel):
    destinatarios: list[str] = Field(min_length=1)
    cc: list[str] = Field(default_factory=list)
    cco: list[str] = Field(default_factory=list)
    observacoes_envio: str | None = None


class EnviarPedidoRequest(BaseModel):
    confirmar: bool = False


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _primeiro(tabela: str, registro_id: str, detalhe: str) -> dict[str, Any]:
    dados = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    if not dados:
        raise HTTPException(status_code=404, detail=detalhe)
    return dados[0]


def _opcional(tabela: str, registro_id: str | None) -> dict[str, Any] | None:
    if not registro_id:
        return None
    try:
        dados = supabase.table(tabela).select("*").eq("id", registro_id).limit(1).execute().data or []
    except Exception:
        return None
    return dados[0] if dados else None


def _cliente_opcional(cliente_id: str | None) -> tuple[dict[str, Any] | None, str | None]:
    if not cliente_id:
        return None, None
    for tabela in ("cti_clientes", "clientes"):
        cliente = _opcional(tabela, cliente_id)
        if cliente:
            return cliente, tabela
    return None, None


def _equipamento_pedido(pacote: dict[str, Any]) -> str:
    item = pacote.get("item") or {}
    proposta = pacote.get("proposta") or {}
    pedido = pacote.get("pedido") or {}
    snapshot = proposta.get("snapshot_dados") if isinstance(proposta, dict) else {}
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    item_snapshot = snapshot.get("item") if isinstance(snapshot.get("item"), dict) else {}
    itens_snapshot = snapshot.get("itens") if isinstance(snapshot.get("itens"), list) else []
    primeiro_item_snapshot = itens_snapshot[0] if itens_snapshot and isinstance(itens_snapshot[0], dict) else {}

    for fonte in (item, item_snapshot, primeiro_item_snapshot, proposta, pedido, snapshot):
        if not isinstance(fonte, dict):
            continue
        valor = (
            fonte.get("equipamento")
            or fonte.get("modelo_equipamento")
            or fonte.get("equipamentos")
            or fonte.get("produto")
            or fonte.get("modelo")
        )
        if valor:
            return str(valor)
    return "A definir"


def _emails_validos(
    valores: list[str], *, obrigatorio: bool = True, campo: str = "Para"
) -> list[str]:
    emails: list[str] = []
    for valor in valores:
        email = str(valor or "").strip().lower()
        if not email:
            continue
        if "@" not in email or "." not in email.split("@")[-1]:
            raise HTTPException(status_code=422, detail=f"E-mail inválido em {campo}: {valor}")
        if email not in emails:
            emails.append(email)
    if obrigatorio and not emails:
        raise HTTPException(status_code=422, detail="Informe ao menos um destinatário principal do pedido.")
    return emails


def _dossie_normalizado(valor: Any) -> list[dict[str, Any]]:
    if not isinstance(valor, list):
        return []
    return [registro for registro in valor if isinstance(registro, dict)]


def _ultimo_registro(pedido: dict[str, Any], tipo: str) -> dict[str, Any] | None:
    return next(
        (
            registro
            for registro in reversed(_dossie_normalizado(pedido.get("dossie_documentos")))
            if registro.get("tipo") == tipo
        ),
        None,
    )


def _registrar_destinatarios(
    pedido: dict[str, Any],
    destinatarios: list[str],
    cc: list[str],
    cco: list[str],
    observacoes: str | None,
) -> dict[str, Any]:
    dossie = [
        registro
        for registro in _dossie_normalizado(pedido.get("dossie_documentos"))
        if registro.get("tipo") != "DESTINATARIOS_PEDIDO"
    ]
    dossie.append(
        {
            "tipo": "DESTINATARIOS_PEDIDO",
            "destinatarios": destinatarios,
            "cc": cc,
            "cco": cco,
            "observacoes_envio": observacoes,
            "status_envio": "PENDENTE",
            "registrado_em": _agora(),
        }
    )
    atualizado = (
        supabase.table("cti_pedidos")
        .update({"dossie_documentos": dossie})
        .eq("id", pedido["id"])
        .execute()
        .data
        or []
    )
    if not atualizado:
        raise HTTPException(status_code=500, detail="O pedido não confirmou a gravação dos destinatários.")
    return atualizado[0]


def _pacote_pedido(pedido_id: str) -> dict[str, Any]:
    pedido = _primeiro("cti_pedidos", pedido_id, "Pedido não encontrado")
    proposta_id = pedido.get("proposta_id") or pedido.get("proposta_aceita_id")
    proposta = _opcional("cti_propostas", str(proposta_id or ""))
    item = _opcional("cti_oportunidade_itens", str(pedido.get("item_oportunidade_id") or ""))
    oportunidade_id = (proposta or {}).get("oportunidade_id") or pedido.get("oportunidade_id")
    oportunidade = _opcional("cti_oportunidades", str(oportunidade_id or ""))
    cliente_id = (
        pedido.get("cliente_id")
        or (proposta or {}).get("cliente_id")
        or (oportunidade or {}).get("cliente_id")
        or (item or {}).get("cliente_id")
    )
    cliente_cadastrado, cliente_tabela = _cliente_opcional(str(cliente_id or ""))
    cliente = cliente_cadastrado

    snapshot = (proposta or {}).get("snapshot_dados") or {}
    cliente_snapshot = snapshot.get("cliente") if isinstance(snapshot, dict) else None
    oportunidade_snapshot = snapshot.get("oportunidade") if isinstance(snapshot, dict) else None
    if not cliente and isinstance(cliente_snapshot, dict):
        cliente = cliente_snapshot
    if not oportunidade and isinstance(oportunidade_snapshot, dict):
        oportunidade = oportunidade_snapshot

    nome_cliente = None
    fontes = [
        cliente,
        oportunidade,
        oportunidade_snapshot if isinstance(oportunidade_snapshot, dict) else None,
        cliente_snapshot if isinstance(cliente_snapshot, dict) else None,
        snapshot if isinstance(snapshot, dict) else None,
        proposta,
        item,
        pedido,
    ]
    for fonte in fontes:
        if not isinstance(fonte, dict):
            continue
        nome_cliente = (
            fonte.get("razao_social")
            or fonte.get("nome_fantasia")
            or fonte.get("nome")
            or fonte.get("cliente_nome")
            or fonte.get("empresa_nome")
            or fonte.get("empresa")
        )
        if nome_cliente:
            break
    if not cliente and nome_cliente:
        cliente = {
            "nome": nome_cliente,
            "razao_social": nome_cliente,
            "origem": "DOSSIE_COMERCIAL",
        }

    pacote_base = {
        "pedido": pedido,
        "proposta": proposta,
        "item": item,
    }
    equipamento = _equipamento_pedido(pacote_base)
    if not item and equipamento != "A definir":
        item = {"equipamento": equipamento, "origem": "DOSSIE_COMERCIAL"}
    elif item and not item.get("equipamento") and equipamento != "A definir":
        item = {**item, "equipamento": equipamento}

    envio = _ultimo_registro(pedido, "DESTINATARIOS_PEDIDO")
    protocolo = _ultimo_registro(pedido, "ENVIO_PEDIDO")
    return {
        "pedido": pedido,
        "proposta": proposta,
        "item": item,
        "oportunidade": oportunidade,
        "cliente": cliente,
        "envio": envio,
        "protocolo_envio": protocolo,
        "transporte_email": configuracao_email(),
        "integridade": {
            "cliente_cadastrado": bool(cliente_cadastrado),
            "cliente_tabela": cliente_tabela,
            "cliente_recuperado_snapshot": bool(cliente and not cliente_cadastrado),
            "equipamento_recuperado": equipamento != "A definir",
        },
    }


def _nome_cliente(pacote: dict[str, Any]) -> str:
    cliente = pacote.get("cliente") or {}
    oportunidade = pacote.get("oportunidade") or {}
    proposta = pacote.get("proposta") or {}
    pedido = pacote.get("pedido") or {}
    return str(
        cliente.get("razao_social")
        or cliente.get("nome_fantasia")
        or cliente.get("nome")
        or oportunidade.get("cliente_nome")
        or proposta.get("cliente_nome")
        or pedido.get("cliente_nome")
        or "Cliente não identificado"
    )


def _html_pedido(pacote: dict[str, Any]) -> tuple[str, str, str]:
    pedido = pacote["pedido"]
    proposta = pacote.get("proposta") or {}
    item = pacote.get("item") or {}
    envio = pacote.get("envio") or {}
    numero = str(pedido.get("numero") or pedido.get("id") or "Pedido CTI")
    cliente = _nome_cliente(pacote)
    equipamento = _equipamento_pedido(pacote)
    quantidade = str(item.get("quantidade") or pedido.get("quantidade") or "1")
    valor = float(pedido.get("valor") or 0)
    valor_br = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    observacoes = str(envio.get("observacoes_envio") or "Sem observações adicionais.")
    proposta_numero = str(proposta.get("numero") or "—")
    assunto = f"Pedido comercial {numero} — {cliente}"
    html = f"""
    <div style="font-family:Arial,sans-serif;color:#10223f;max-width:720px;margin:auto">
      <div style="background:#06152d;color:white;padding:24px;border-radius:14px 14px 0 0">
        <div style="font-size:12px;letter-spacing:2px;color:#22d3ee">CTI / VIENA SÃO PAULO</div>
        <h1 style="margin:8px 0 0">Pedido comercial {escape(numero)}</h1>
      </div>
      <div style="border:1px solid #d7e1ee;border-top:0;padding:24px;border-radius:0 0 14px 14px">
        <p>Segue o pedido comercial registrado e aprovado no CTI.</p>
        <table style="width:100%;border-collapse:collapse">
          <tr><td style="padding:9px;border-bottom:1px solid #e5edf5"><b>Cliente</b></td><td style="padding:9px;border-bottom:1px solid #e5edf5">{escape(cliente)}</td></tr>
          <tr><td style="padding:9px;border-bottom:1px solid #e5edf5"><b>Equipamento</b></td><td style="padding:9px;border-bottom:1px solid #e5edf5">{escape(equipamento)}</td></tr>
          <tr><td style="padding:9px;border-bottom:1px solid #e5edf5"><b>Quantidade</b></td><td style="padding:9px;border-bottom:1px solid #e5edf5">{escape(quantidade)}</td></tr>
          <tr><td style="padding:9px;border-bottom:1px solid #e5edf5"><b>Valor</b></td><td style="padding:9px;border-bottom:1px solid #e5edf5">{escape(valor_br)}</td></tr>
          <tr><td style="padding:9px;border-bottom:1px solid #e5edf5"><b>Proposta de origem</b></td><td style="padding:9px;border-bottom:1px solid #e5edf5">{escape(proposta_numero)}</td></tr>
        </table>
        <h3 style="margin-top:24px">Observações</h3>
        <p style="white-space:pre-line">{escape(observacoes)}</p>
        <p style="margin-top:28px;font-size:12px;color:#64748b">Mensagem enviada pelo CTI — Centro de Tecnologia e Inteligência Comercial.</p>
      </div>
    </div>
    """
    texto = (
        f"Pedido comercial {numero}\nCliente: {cliente}\nEquipamento: {equipamento}\n"
        f"Quantidade: {quantidade}\nValor: {valor_br}\nProposta: {proposta_numero}\n\n"
        f"Observações: {observacoes}"
    )
    return assunto, html, texto


@router.post("/propostas/{proposta_id}/converter-pedido-operacional")
def converter_pedido_operacional(proposta_id: str, dados: ConverterPedidoOperacionalRequest):
    destinatarios = _emails_validos(dados.destinatarios, campo="Para")
    cc = _emails_validos(dados.cc, obrigatorio=False, campo="CC")
    cco = _emails_validos(dados.cco, obrigatorio=False, campo="CCO")
    pedidos = converter_em_pedido(
        proposta_id,
        ConverterPedidoRequest(
            responsavel_id=dados.responsavel_id,
            data_pedido=dados.data_pedido,
            origem_comercial="CRM_APP",
        ),
    )
    pedido = pedidos[0] if isinstance(pedidos, list) and pedidos else pedidos
    if not isinstance(pedido, dict) or not pedido.get("id"):
        raise HTTPException(status_code=500, detail="Pedido criado sem identificação válida.")
    return _registrar_destinatarios(pedido, destinatarios, cc, cco, dados.observacoes_envio)


@router.post("/pedidos/{pedido_id}/destinatarios")
def atualizar_destinatarios_pedido(pedido_id: str, dados: AtualizarDestinatariosPedidoRequest):
    pedido = _primeiro("cti_pedidos", pedido_id, "Pedido não encontrado")
    return _registrar_destinatarios(
        pedido,
        _emails_validos(dados.destinatarios, campo="Para"),
        _emails_validos(dados.cc, obrigatorio=False, campo="CC"),
        _emails_validos(dados.cco, obrigatorio=False, campo="CCO"),
        dados.observacoes_envio,
    )


@router.post("/pedidos/{pedido_id}/enviar")
def enviar_pedido_operacional(pedido_id: str, dados: EnviarPedidoRequest):
    if not dados.confirmar:
        raise HTTPException(status_code=409, detail="Confirme expressamente o envio do pedido.")

    pacote = _pacote_pedido(pedido_id)
    pedido = pacote["pedido"]
    envio = pacote.get("envio") or {}
    protocolo_existente = pacote.get("protocolo_envio") or {}
    if protocolo_existente.get("status_envio") == "ENVIADO":
        return pacote

    destinatarios = _emails_validos(list(envio.get("destinatarios") or []), campo="Para")
    cc = _emails_validos(list(envio.get("cc") or []), obrigatorio=False, campo="CC")
    cco = _emails_validos(list(envio.get("cco") or []), obrigatorio=False, campo="CCO")
    assunto, html, texto = _html_pedido(pacote)
    try:
        resultado = enviar_email(
            destinatarios=destinatarios,
            cc=cc,
            cco=cco,
            assunto=assunto,
            html=html,
            texto=texto,
        )
    except TransporteEmailNaoConfigurado as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Não foi possível enviar o pedido: {exc}") from exc

    enviado_em = _agora()
    dossie = _dossie_normalizado(pedido.get("dossie_documentos"))
    for registro in reversed(dossie):
        if registro.get("tipo") == "DESTINATARIOS_PEDIDO":
            registro["status_envio"] = "ENVIADO"
            registro["enviado_em"] = enviado_em
            break
    dossie.append(
        {
            "tipo": "ENVIO_PEDIDO",
            "status_envio": "ENVIADO",
            "provider": resultado.provider,
            "message_id": resultado.message_id,
            "remetente": resultado.remetente,
            "destinatarios": resultado.destinatarios,
            "cc": resultado.cc,
            "cco": resultado.cco,
            "assunto": assunto,
            "enviado_em": enviado_em,
        }
    )
    atualizado = (
        supabase.table("cti_pedidos")
        .update({"dossie_documentos": dossie})
        .eq("id", pedido_id)
        .execute()
        .data
        or []
    )
    if not atualizado:
        raise HTTPException(
            status_code=500,
            detail=(
                "O e-mail foi aceito pelo provedor, mas o CTI não conseguiu registrar o protocolo. "
                f"Protocolo externo: {resultado.message_id}"
            ),
        )
    return _pacote_pedido(pedido_id)


@router.get("/pedidos/{pedido_id}")
def consultar_pedido_operacional(pedido_id: str):
    return _pacote_pedido(pedido_id)
