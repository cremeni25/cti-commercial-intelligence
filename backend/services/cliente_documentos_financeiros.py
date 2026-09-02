from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from core.supabase_client import supabase

BUCKET = "documentos-financeiros-clientes"
MAX_FILE_BYTES = 20 * 1024 * 1024
ALLOWED_MIME = {
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg", "image/png",
}
CATEGORIAS = {
    "CONTRATO_SOCIAL", "ULTIMA_ALTERACAO", "FATURAMENTO_12_MESES",
    "DRE_ASSINADA", "BALANCO_ASSINADO", "OUTRO",
}


def _dados(resposta):
    dados = getattr(resposta, "data", None)
    return dados if isinstance(dados, list) else []


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validade_12_meses(validado_em: date) -> date:
    try:
        return validado_em.replace(year=validado_em.year + 1)
    except ValueError:
        return validado_em.replace(year=validado_em.year + 1, day=28)


def _status_temporal(registro: dict | None) -> dict | None:
    if not registro:
        return None
    saida = dict(registro)
    valido_ate = saida.get("valido_ate")
    status = str(saida.get("status") or "EM_PREPARACAO")
    if valido_ate:
        vencimento = date.fromisoformat(str(valido_ate)[:10])
        dias = (vencimento - date.today()).days
        if dias < 0 and status == "VALIDADO_CARRIER":
            saida["status_calculado"] = "VENCIDO"
        elif 0 <= dias <= 45 and status == "VALIDADO_CARRIER":
            saida["status_calculado"] = "PROXIMO_VENCIMENTO"
        else:
            saida["status_calculado"] = status
        saida["dias_para_vencer"] = dias
    else:
        saida["status_calculado"] = status
        saida["dias_para_vencer"] = None
    return saida


def _listar_ciclos(cliente_id: str) -> list[dict]:
    ciclos = _dados(
        supabase.table("cti_cliente_cadastro_financeiro_carrier")
        .select("*").eq("cliente_id", cliente_id)
        .order("ciclo_numero", desc=True).execute()
    )
    return [_status_temporal(item) or item for item in ciclos]


def _ciclo_atual(cliente_id: str) -> dict | None:
    dados = _dados(
        supabase.table("cti_cliente_cadastro_financeiro_carrier")
        .select("*").eq("cliente_id", cliente_id).eq("ciclo_atual", True)
        .limit(1).execute()
    )
    return dados[0] if dados else None


def _garantir_ciclo_atual(cliente_id: str, usuario_id: str) -> dict:
    atual = _ciclo_atual(cliente_id)
    if atual:
        return atual
    ciclos = _listar_ciclos(cliente_id)
    numero = max((int(c.get("ciclo_numero") or 0) for c in ciclos), default=0) + 1
    inseridos = _dados(
        supabase.table("cti_cliente_cadastro_financeiro_carrier").insert({
            "cliente_id": cliente_id,
            "status": "EM_PREPARACAO",
            "ciclo_numero": numero,
            "ciclo_atual": True,
            "criado_por": usuario_id,
            "atualizado_por": usuario_id,
        }).execute()
    )
    if not inseridos:
        raise HTTPException(status_code=502, detail="Não foi possível iniciar o ciclo financeiro do cliente.")
    return inseridos[0]


def listar_dossie(cliente_id: str, proposta_id: str | None = None) -> dict:
    docs = _dados(
        supabase.table("cti_cliente_documentos_financeiros")
        .select("*").eq("cliente_id", cliente_id).is_("arquivado_em", "null")
        .order("created_at", desc=True).execute()
    )
    vinculados: set[str] = set()
    if proposta_id:
        links = _dados(
            supabase.table("cti_proposta_documentos_financeiros").select("documento_id")
            .eq("proposta_id", proposta_id).execute()
        )
        vinculados = {str(item.get("documento_id")) for item in links}
    ciclos = _listar_ciclos(cliente_id)
    mapa_ciclos = {str(c.get("id")): c for c in ciclos if c.get("id")}
    for doc in docs:
        doc["vinculado_proposta"] = str(doc.get("id")) in vinculados
        ciclo = mapa_ciclos.get(str(doc.get("ciclo_financeiro_id") or ""))
        doc["ciclo_numero"] = ciclo.get("ciclo_numero") if ciclo else None
    cadastro = next((c for c in ciclos if bool(c.get("ciclo_atual"))), None)
    return {
        "cliente_id": cliente_id,
        "proposta_id": proposta_id,
        "cadastro": cadastro,
        "ciclos": ciclos,
        "documentos": docs,
    }


async def anexar_documento(
    *, cliente_id: str, proposta_id: str, categoria: str, observacao: str | None,
    arquivo: UploadFile, usuario_id: str,
) -> dict:
    categoria = categoria.strip().upper()
    if categoria not in CATEGORIAS:
        raise HTTPException(status_code=422, detail="Categoria documental inválida.")
    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(status_code=422, detail="Arquivo vazio.")
    if len(conteudo) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="O arquivo excede o limite de 20 MB.")
    mime = str(arquivo.content_type or "application/octet-stream").lower()
    if mime not in ALLOWED_MIME:
        raise HTTPException(status_code=415, detail="Formato não permitido. Use PDF, Word, Excel, JPG ou PNG.")

    ciclo = _garantir_ciclo_atual(cliente_id, usuario_id)
    nome_original = Path(arquivo.filename or "documento").name
    extensao = Path(nome_original).suffix.lower()
    caminho = f"clientes/{cliente_id}/ciclo-{int(ciclo.get('ciclo_numero') or 1)}/{datetime.now(timezone.utc).strftime('%Y/%m')}/{uuid4().hex}{extensao}"
    digest = sha256(conteudo).hexdigest()
    try:
        supabase.storage.from_(BUCKET).upload(caminho, conteudo, {"content-type": mime, "upsert": "false"})
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Não foi possível armazenar o documento financeiro.") from exc

    try:
        inseridos = _dados(
            supabase.table("cti_cliente_documentos_financeiros").insert({
                "cliente_id": cliente_id,
                "ciclo_financeiro_id": ciclo.get("id"),
                "categoria": categoria,
                "nome_arquivo": nome_original,
                "storage_bucket": BUCKET,
                "storage_path": caminho,
                "mime_type": mime,
                "tamanho_bytes": len(conteudo),
                "sha256": digest,
                "observacao": observacao.strip() if observacao else None,
                "criado_por": usuario_id,
            }).execute()
        )
        if not inseridos:
            raise RuntimeError("Documento não persistido")
        documento = inseridos[0]
        supabase.table("cti_proposta_documentos_financeiros").insert({
            "proposta_id": proposta_id,
            "documento_id": documento["id"],
            "vinculado_por": usuario_id,
        }).execute()
        return documento
    except Exception as exc:
        try:
            supabase.storage.from_(BUCKET).remove([caminho])
        except Exception:
            pass
        raise HTTPException(status_code=502, detail="Não foi possível registrar o documento no dossiê.") from exc


def vincular_documento(*, proposta_id: str, documento_id: str, cliente_id: str, usuario_id: str) -> dict:
    docs = _dados(
        supabase.table("cti_cliente_documentos_financeiros").select("id,cliente_id,arquivado_em")
        .eq("id", documento_id).eq("cliente_id", cliente_id).limit(1).execute()
    )
    if not docs or docs[0].get("arquivado_em"):
        raise HTTPException(status_code=404, detail="Documento financeiro não encontrado para este cliente.")
    existentes = _dados(
        supabase.table("cti_proposta_documentos_financeiros").select("id")
        .eq("proposta_id", proposta_id).eq("documento_id", documento_id).limit(1).execute()
    )
    if not existentes:
        supabase.table("cti_proposta_documentos_financeiros").insert({
            "proposta_id": proposta_id, "documento_id": documento_id, "vinculado_por": usuario_id,
        }).execute()
    return {"ok": True, "proposta_id": proposta_id, "documento_id": documento_id}


def desvincular_documento(*, proposta_id: str, documento_id: str) -> dict:
    supabase.table("cti_proposta_documentos_financeiros").delete().eq("proposta_id", proposta_id).eq("documento_id", documento_id).execute()
    return {"ok": True}


def url_temporaria(*, documento_id: str, cliente_id: str) -> dict:
    docs = _dados(
        supabase.table("cti_cliente_documentos_financeiros")
        .select("id,cliente_id,nome_arquivo,storage_bucket,storage_path,arquivado_em")
        .eq("id", documento_id).eq("cliente_id", cliente_id).limit(1).execute()
    )
    if not docs or docs[0].get("arquivado_em"):
        raise HTTPException(status_code=404, detail="Documento financeiro não encontrado.")
    doc = docs[0]
    try:
        resposta = supabase.storage.from_(str(doc.get("storage_bucket") or BUCKET)).create_signed_url(str(doc["storage_path"]), 600)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Não foi possível gerar acesso temporário ao documento.") from exc
    url = resposta.get("signedURL") or resposta.get("signedUrl") if isinstance(resposta, dict) else None
    if not url:
        raise HTTPException(status_code=502, detail="O storage não retornou uma URL temporária válida.")
    return {"url": url, "expires_in": 600, "nome_arquivo": doc.get("nome_arquivo")}


def atualizar_cadastro_financeiro(
    *, cliente_id: str, status: str, validado_carrier_em: date | None,
    observacao: str | None, usuario_id: str,
) -> dict:
    status = status.strip().upper()
    permitidos = {"EM_PREPARACAO", "EM_ANALISE", "VALIDADO_CARRIER", "RENOVACAO_EM_ANALISE"}
    if status not in permitidos:
        raise HTTPException(status_code=422, detail="Status financeiro inválido.")
    valido_ate = None
    if status == "VALIDADO_CARRIER":
        if not validado_carrier_em:
            raise HTTPException(status_code=422, detail="Informe a data de validação pela Carrier.")
        valido_ate = _validade_12_meses(validado_carrier_em)

    atual = _ciclo_atual(cliente_id)
    if not atual:
        atual = _garantir_ciclo_atual(cliente_id, usuario_id)

    # Renovação abre um novo ciclo e encerra o anterior sem apagá-lo ou reescrevê-lo.
    if status == "RENOVACAO_EM_ANALISE" and str(atual.get("status") or "") != "RENOVACAO_EM_ANALISE":
        agora = _agora()
        supabase.table("cti_cliente_cadastro_financeiro_carrier").update({
            "ciclo_atual": False,
            "encerrado_em": agora,
            "updated_at": agora,
            "atualizado_por": usuario_id,
        }).eq("id", atual["id"]).execute()
        numero = int(atual.get("ciclo_numero") or 1) + 1
        inseridos = _dados(
            supabase.table("cti_cliente_cadastro_financeiro_carrier").insert({
                "cliente_id": cliente_id,
                "status": "RENOVACAO_EM_ANALISE",
                "ciclo_numero": numero,
                "ciclo_atual": True,
                "ciclo_anterior_id": atual["id"],
                "observacao": observacao.strip() if observacao else None,
                "criado_por": usuario_id,
                "atualizado_por": usuario_id,
            }).execute()
        )
        if not inseridos:
            raise HTTPException(status_code=502, detail="Não foi possível iniciar o novo ciclo financeiro.")
        return _status_temporal(inseridos[0]) or inseridos[0]

    payload = {
        "status": status,
        "validado_carrier_em": validado_carrier_em.isoformat() if validado_carrier_em else None,
        "valido_ate": valido_ate.isoformat() if valido_ate else None,
        "observacao": observacao.strip() if observacao else None,
        "atualizado_por": usuario_id,
        "updated_at": _agora(),
    }
    resposta = supabase.table("cti_cliente_cadastro_financeiro_carrier").update(payload).eq("id", atual["id"]).execute()
    dados = _dados(resposta)
    return _status_temporal(dados[0]) if dados else payload
