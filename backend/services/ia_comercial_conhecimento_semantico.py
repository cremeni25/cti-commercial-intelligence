from __future__ import annotations

import json
import re
from typing import Any

from core.supabase_client import supabase


MAX_FRAGMENTO = 12_000
MAX_CONTEXTO = 18_000

_TERMOS_DOMINIO = {
    "carrier", "transicold", "thermo king", "refrigera", "frigor", "cadeia fria", "cadeia do frio",
    "temperatura", "telemetria", "telemática", "telematica", "frota", "caminhão", "caminhao",
    "semirreboque", "trailer", "implementadora", "implemento", "evaporador", "condensador", "compressor",
    "diesel truck", "direct drive", "lynx", "tracking", "connected", "reefer", "cold chain",
    "alimento", "bebida", "farmac", "congelado", "resfriado", "logística refrigerada", "logistica refrigerada",
    "anfir", "set point", "sensor de temperatura", "controle remoto", "e-cool", "ecool", "pulsor",
}

_STOPWORDS = {
    "para", "como", "com", "sem", "uma", "uns", "das", "dos", "que", "por", "nos", "nas", "este",
    "esta", "esse", "essa", "arquivo", "documento", "analise", "análise", "compare", "sobre", "entre",
    "mercado", "produto", "produtos", "informações", "informacoes", "dados", "carrier", "transicold",
}


def _dados(resposta: Any) -> list[dict[str, Any]]:
    dados = getattr(resposta, "data", None)
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]
    if isinstance(dados, dict):
        return [dados]
    return []


def _normalizar(texto: Any) -> str:
    return str(texto or "").strip().casefold()


def _termos(texto: str) -> list[str]:
    candidatos = re.findall(r"[a-zA-ZÀ-ÿ0-9][a-zA-ZÀ-ÿ0-9._/-]{2,}", _normalizar(texto))
    vistos: set[str] = set()
    resultado: list[str] = []
    for termo in candidatos:
        if termo in _STOPWORDS or termo in vistos:
            continue
        vistos.add(termo)
        resultado.append(termo)
    return resultado[:24]


def eh_dominio_frio(anexo: dict[str, Any], mensagem: str = "") -> bool:
    alvo = _normalizar(
        " ".join(
            [
                str(anexo.get("nome") or ""),
                mensagem,
                str(anexo.get("conteudo_extraido") or "")[:40_000],
            ]
        )
    )
    return any(termo in alvo for termo in _TERMOS_DOMINIO)


def _fragmentar(texto: str) -> list[str]:
    texto = str(texto or "").strip()
    if not texto:
        return []
    fragmentos: list[str] = []
    inicio = 0
    while inicio < len(texto):
        fim = min(len(texto), inicio + MAX_FRAGMENTO)
        if fim < len(texto):
            quebra = texto.rfind("\n", inicio, fim)
            if quebra > inicio + 2000:
                fim = quebra
        fragmento = texto[inicio:fim].strip()
        if fragmento:
            fragmentos.append(fragmento)
        inicio = fim
    return fragmentos[:12]


def persistir_anexos_como_conhecimento(
    anexos: list[dict[str, Any]],
    *,
    conversa_id: str,
    usuario_id: str,
    tipo_usuario: str,
    mensagem: str,
) -> list[dict[str, Any]]:
    resultados: list[dict[str, Any]] = []
    escopo = "GLOBAL_CTI" if str(tipo_usuario or "").upper() == "ADMIN_MASTER" else "USUARIO"

    for anexo in anexos:
        if not eh_dominio_frio(anexo, mensagem):
            resultados.append({
                "sha256": anexo.get("sha256"),
                "nome": anexo.get("nome"),
                "persistido": False,
                "motivo": "fora_dominio_frio",
            })
            continue

        sha = str(anexo.get("sha256") or "")
        existentes = _dados(
            supabase.table("cti_ia_conhecimento_documentos")
            .select("id,sha256,nome_arquivo,escopo")
            .eq("sha256", sha)
            .limit(1)
            .execute()
        )
        payload_doc = {
            "sha256": sha,
            "nome_arquivo": str(anexo.get("nome") or "arquivo"),
            "tipo": str(anexo.get("tipo") or "DESCONHECIDO"),
            "mime_type": str(anexo.get("mime_type") or "application/octet-stream"),
            "tamanho_bytes": int(anexo.get("tamanho_bytes") or 0),
            "estrutura": anexo.get("estrutura") or {},
            "origem": "ANEXO_CONVERSACIONAL",
            "dominio": "CADEIA_FRIA",
            "status": "ATIVO_SEMANTICO",
            "escopo": escopo,
            "criado_por": usuario_id,
            "conversa_origem_id": conversa_id,
            "metadados": {
                "verdade_operacional": False,
                "escrita_crm_autorizada": False,
                "fonte_rastreavel": True,
                "mensagem_origem": mensagem[:1000],
            },
        }

        if existentes:
            documento_id = str(existentes[0]["id"])
            supabase.table("cti_ia_conhecimento_documentos").update({
                "nome_arquivo": payload_doc["nome_arquivo"],
                "estrutura": payload_doc["estrutura"],
                "status": "ATIVO_SEMANTICO",
                "updated_at": "now()",
            }).eq("id", documento_id).execute()
            criado = False
        else:
            criados = _dados(supabase.table("cti_ia_conhecimento_documentos").insert(payload_doc).execute())
            if not criados:
                raise RuntimeError("Não foi possível registrar o conhecimento semântico do anexo.")
            documento_id = str(criados[0]["id"])
            criado = True

        if criado:
            fragmentos = _fragmentar(str(anexo.get("conteudo_extraido") or ""))
            linhas = [
                {
                    "documento_id": documento_id,
                    "indice": indice,
                    "conteudo_texto": fragmento,
                    "metadados": {"sha256": sha, "nome_arquivo": payload_doc["nome_arquivo"]},
                }
                for indice, fragmento in enumerate(fragmentos, start=1)
            ]
            if linhas:
                supabase.table("cti_ia_conhecimento_fragmentos").insert(linhas).execute()

        resultados.append({
            "documento_id": documento_id,
            "sha256": sha,
            "nome": payload_doc["nome_arquivo"],
            "persistido": True,
            "novo": criado,
            "escopo": escopo,
            "verdade_operacional": False,
        })

    return resultados


def buscar_conhecimento_relevante(
    pergunta: str,
    *,
    usuario_id: str,
    tipo_usuario: str,
    limite_documentos: int = 4,
) -> tuple[str, list[dict[str, Any]]]:
    termos = _termos(pergunta)
    if not termos:
        return "", []

    try:
        consulta = (
            supabase.table("cti_ia_conhecimento_documentos")
            .select("id,sha256,nome_arquivo,tipo,estrutura,escopo,criado_por,updated_at")
            .eq("status", "ATIVO_SEMANTICO")
            .order("updated_at", desc=True)
            .limit(200)
        )
        documentos = _dados(consulta.execute())
    except Exception:
        return "", []

    candidatos: list[tuple[int, dict[str, Any], list[dict[str, Any]]]] = []
    for doc in documentos:
        escopo = str(doc.get("escopo") or "")
        if escopo != "GLOBAL_CTI" and str(doc.get("criado_por") or "") != str(usuario_id):
            continue
        fragmentos = _dados(
            supabase.table("cti_ia_conhecimento_fragmentos")
            .select("indice,conteudo_texto,metadados")
            .eq("documento_id", doc.get("id"))
            .order("indice")
            .limit(12)
            .execute()
        )
        texto_busca = _normalizar(str(doc.get("nome_arquivo") or "") + " " + " ".join(str(f.get("conteudo_texto") or "")[:4000] for f in fragmentos))
        score = sum(3 if termo in _normalizar(doc.get("nome_arquivo")) else 1 for termo in termos if termo in texto_busca)
        if score > 0:
            candidatos.append((score, doc, fragmentos))

    candidatos.sort(key=lambda item: item[0], reverse=True)
    selecionados = candidatos[:max(1, min(limite_documentos, 6))]
    if not selecionados:
        return "", []

    partes = [
        "CONTEXTO INTERNO DA IA CTI: MEMÓRIA SEMÂNTICA ACUMULADA DA CADEIA FRIA.",
        "Use apenas quando for relevante à pergunta. Esta memória é conhecimento documental rastreável, não verdade operacional do CRM.",
        "Não diga que algo está ausente do CTI apenas porque não há registro operacional correspondente. Preserve a origem documental e o SHA-256.",
    ]
    fontes: list[dict[str, Any]] = []
    total = 0
    for indice, (_, doc, fragmentos) in enumerate(selecionados, start=1):
        cabecalho = f"\n### MEMORIA {indice}: {doc.get('nome_arquivo')} | sha256={doc.get('sha256')} | estrutura={json.dumps(doc.get('estrutura') or {}, ensure_ascii=False)}"
        partes.append(cabecalho)
        total += len(cabecalho)
        for fragmento in fragmentos:
            trecho = str(fragmento.get("conteudo_texto") or "").strip()
            if not trecho:
                continue
            restante = MAX_CONTEXTO - total
            if restante <= 0:
                break
            trecho = trecho[:min(6000, restante)]
            partes.append(trecho)
            total += len(trecho)
        fontes.append({
            "tipo": "CONHECIMENTO_IA",
            "documento_id": str(doc.get("id")),
            "nome": str(doc.get("nome_arquivo") or ""),
            "sha256": str(doc.get("sha256") or ""),
            "escopo": str(doc.get("escopo") or ""),
        })
        if total >= MAX_CONTEXTO:
            break

    return "\n".join(partes), fontes
