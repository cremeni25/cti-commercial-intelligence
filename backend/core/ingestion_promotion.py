from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from core.supabase_client import supabase
from repositories.cti_repository import repository
from backend.services.schema_compat import insert_schema_compatible, update_schema_compatible


SUPORTE = {
    ("CTI_ANFIR", "ANFIR"),
    ("CRM_COMERCIAL", "CLIENTE"),
}

CAMPOS_TECNICOS_MERGE = {
    "updated_at",
    "created_at",
    "pipeline",
    "arquivo_origem",
    "origem_dado",
    "hash_registro",
    "ativo",
}


class DivergenciaPromocao(ValueError):
    """Bloqueio controlado com divergências estruturadas do merge seguro."""

    def __init__(self, mensagem: str, conflitos: list[dict[str, Any]]):
        super().__init__(mensagem)
        self.conflitos = [dict(item) for item in conflitos if isinstance(item, dict)]


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _digitos(valor: Any) -> str:
    return re.sub(r"\D", "", _texto(valor))


def _preenchido(valor: Any) -> bool:
    return valor not in (None, "", "nan")


def planejar_merge_sem_sobrescrita(
    existente: dict[str, Any],
    novo: dict[str, Any],
    *,
    ignorar_conflito: set[str] | None = None,
) -> dict[str, Any]:
    """Monta enriquecimento conservador: preenche vazios e nunca troca valor de negócio existente."""
    ignorados = CAMPOS_TECNICOS_MERGE | set(ignorar_conflito or set())
    mesclado = dict(existente or {})
    conflitos: list[dict[str, Any]] = []
    preenchidos: list[str] = []

    for campo, valor_novo in (novo or {}).items():
        if not _preenchido(valor_novo):
            continue
        valor_existente = mesclado.get(campo)
        if not _preenchido(valor_existente):
            mesclado[campo] = valor_novo
            preenchidos.append(campo)
            continue
        if campo in ignorados:
            continue
        if str(valor_existente).strip().casefold() != str(valor_novo).strip().casefold():
            conflitos.append({
                "campo": campo,
                "valor_existente": valor_existente,
                "valor_recebido": valor_novo,
            })

    return {
        "seguro": not conflitos,
        "mesclado": mesclado,
        "conflitos": conflitos,
        "campos_preenchidos": preenchidos,
        "regra": "CTI_MERGE_SEGURO_SEM_SOBRESCRITA_V1",
    }


def suporte_promocao(dominio: str, entidade: str) -> dict[str, Any]:
    chave = (str(dominio or "").upper(), str(entidade or "").upper())
    if chave in SUPORTE:
        return {"suportado": True, "dominio": chave[0], "entidade": chave[1], "regra": "CTI_PROMOCAO_CONTROLADA_V3_MERGE_SEGURO"}
    motivo = {
        "CTI_TERRITORIAL": "Domínio territorial ainda não possui estrutura canônica suficiente para promoção de CEP/cidade/região.",
        "CTI_FINANCEIRO": "Domínio financeiro ainda não possui tabela canônica operacional própria.",
        "CRM_COMERCIAL": "Entidade comercial exige relacionamentos operacionais próprios antes da promoção.",
    }.get(chave[0], "Domínio/entidade sem adaptador canônico de promoção.")
    return {"suportado": False, "dominio": chave[0], "entidade": chave[1], "motivo": motivo, "regra": "CTI_PROMOCAO_CONTROLADA_V3_MERGE_SEGURO"}


def selecionar_itens_promocao(itens: list[dict[str, Any]], natureza_alvo: str | None = None) -> list[dict[str, Any]]:
    natureza = str(natureza_alvo or "").upper().strip()
    if not natureza:
        return list(itens)
    return [
        item for item in itens
        if str(item.get("natureza_canonica") or "").upper() == natureza
    ]


def naturezas_prontas(itens: list[dict[str, Any]]) -> list[str]:
    return sorted({
        str(item.get("natureza_canonica") or "").upper()
        for item in itens
        if str(item.get("status_item") or "") == "PRONTO_PROMOCAO"
        and str(item.get("natureza_canonica") or "").strip()
    })


def validar_lote(
    reconciliacao: dict[str, Any],
    itens: list[dict[str, Any]],
    natureza_alvo: str | None = None,
) -> dict[str, Any]:
    if str(reconciliacao.get("status") or "") not in {"PRONTO_PROMOCAO", "PROMOCAO_PARCIAL"}:
        raise ValueError("Reconciliação não está pronta para promoção.")
    if not itens:
        raise ValueError("Reconciliação sem itens para promover.")

    prontas = naturezas_prontas(itens)
    alvo = str(natureza_alvo or "").upper().strip() or None
    if len(prontas) > 1 and not alvo:
        return {
            "aprovado": False,
            "bloqueios": [{
                "motivo": "LOTE_MISTO_REQUER_NATUREZA_ALVO",
                "naturezas_disponiveis": prontas,
            }],
            "total": len(itens),
            "natureza_alvo": None,
            "regra": "CTI_PROMOCAO_CONTROLADA_V3_MERGE_SEGURO",
        }

    if not alvo and len(prontas) == 1:
        alvo = prontas[0]

    selecionados = selecionar_itens_promocao(itens, alvo)
    selecionados = [item for item in selecionados if str(item.get("status_item") or "") == "PRONTO_PROMOCAO"]
    if not selecionados:
        return {
            "aprovado": False,
            "bloqueios": [{"motivo": "NATUREZA_SEM_ITENS", "natureza_alvo": alvo}],
            "total": 0,
            "natureza_alvo": alvo,
            "regra": "CTI_PROMOCAO_CONTROLADA_V3_MERGE_SEGURO",
        }

    bloqueios = []
    for item in selecionados:
        suporte = suporte_promocao(str(reconciliacao.get("dominio_alvo") or ""), str(item.get("entidade_sugerida") or ""))
        if not suporte["suportado"]:
            bloqueios.append({
                "item_id": item.get("id"),
                "entidade": item.get("entidade_sugerida"),
                "natureza": item.get("natureza_canonica"),
                "motivo": suporte.get("motivo"),
            })
    return {
        "aprovado": not bloqueios,
        "bloqueios": bloqueios,
        "total": len(selecionados),
        "natureza_alvo": alvo,
        "itens": selecionados,
        "naturezas_disponiveis": prontas,
        "regra": "CTI_PROMOCAO_CONTROLADA_V3_MERGE_SEGURO",
    }


def _payload_cliente(dados: dict[str, Any]) -> dict[str, Any]:
    nome = _texto(dados.get("nome") or dados.get("razao_social") or dados.get("cliente") or dados.get("empresa"))
    if len(nome) < 2:
        raise ValueError("Cliente sem nome/razão social válido.")
    categoria = _texto(dados.get("categoria") or dados.get("segmento") or "TRANSPORTADORA").upper()
    return {
        "nome": nome,
        "cnpj": _digitos(dados.get("cnpj") or dados.get("cpf_cnpj")) or None,
        "inscricao_estadual": _texto(dados.get("inscricao_estadual")) or None,
        "endereco": _texto(dados.get("endereco") or dados.get("logradouro")) or None,
        "numero": _texto(dados.get("numero")) or None,
        "complemento": _texto(dados.get("complemento")) or None,
        "bairro": _texto(dados.get("bairro")) or None,
        "cidade": _texto(dados.get("cidade") or dados.get("municipio")) or None,
        "estado": _texto(dados.get("estado") or dados.get("uf")).upper() or None,
        "cep": _digitos(dados.get("cep")) or None,
        "contato": _texto(dados.get("contato") or dados.get("responsavel")) or None,
        "fone": _texto(dados.get("fone") or dados.get("telefone")) or None,
        "email": _texto(dados.get("email")).lower() or None,
        "email_xml": _texto(dados.get("email_xml")).lower() or None,
        "categoria": categoria,
        "segmento": categoria,
        "ddd": _digitos(dados.get("ddd")) or None,
        "sub_regiao": _texto(dados.get("sub_regiao")) or None,
        "status": "ATIVO",
        "updated_at": _agora(),
    }


def promover_cliente(dados: dict[str, Any]) -> dict[str, Any]:
    payload = _payload_cliente(dados)
    cnpj = payload.get("cnpj")

    if cnpj:
        existentes = supabase.table("clientes").select("*").eq("cnpj", cnpj).limit(2).execute().data or []
        if len(existentes) > 1:
            raise ValueError("CNPJ corresponde a mais de um cliente; promoção bloqueada para reconciliação manual.")
        if existentes:
            existente = existentes[0]
            plano = planejar_merge_sem_sobrescrita(existente, payload, ignorar_conflito={"cnpj"})
            if not plano["seguro"]:
                raise DivergenciaPromocao(
                    "Cliente existente possui divergências; promoção não sobrescreveu dados.",
                    plano["conflitos"],
                )
            if not plano["campos_preenchidos"]:
                return {
                    "acao": "SEM_ALTERACAO",
                    "registro": existente,
                    "tabela": "clientes",
                    "regra_merge": plano["regra"],
                }
            registro_id = str(existente["id"])
            dados_atualizados, compat = update_schema_compatible(
                supabase,
                "clientes",
                registro_id,
                plano["mesclado"],
            )
            return {
                "acao": "ENRIQUECIDO_SEM_SOBRESCRITA",
                "registro": (dados_atualizados or [plano["mesclado"]])[0],
                "compatibilidade": compat,
                "tabela": "clientes",
                "campos_preenchidos": plano["campos_preenchidos"],
                "regra_merge": plano["regra"],
            }
    else:
        por_nome = supabase.table("clientes").select("id,nome,cnpj").ilike("nome", payload["nome"]).limit(2).execute().data or []
        if por_nome:
            raise ValueError("Cliente sem CNPJ coincide por nome com cadastro existente; promoção bloqueada para reconciliação manual.")

    criado, compat = insert_schema_compatible(supabase, "clientes", payload, protected_fields={"nome"})
    if not criado:
        raise RuntimeError("Falha ao criar cliente canônico.")
    return {"acao": "INSERIDO", "registro": criado[0], "compatibilidade": compat, "tabela": "clientes"}


def promover_anfir(dados: dict[str, Any], *, chave_canonica: str, fonte_nome: str | None = None) -> dict[str, Any]:
    registro = dict(dados)
    registro["hash_registro"] = _texto(registro.get("hash_registro")) or chave_canonica
    registro["origem_dado"] = _texto(registro.get("origem_dado")) or "BACKOFFICE_FONTES"
    registro["arquivo_origem"] = _texto(registro.get("arquivo_origem")) or _texto(fonte_nome) or None
    registro["pipeline"] = _texto(registro.get("pipeline")) or "CTI_PROMOCAO_CONTROLADA_V3_MERGE_SEGURO"
    registro["ativo"] = True if registro.get("ativo") is None else bool(registro.get("ativo"))

    existente = repository.buscar_por_hash(registro["hash_registro"])
    if existente:
        plano = planejar_merge_sem_sobrescrita(existente, registro, ignorar_conflito={"hash_registro"})
        if not plano["seguro"]:
            raise DivergenciaPromocao(
                "Registro ANFIR existente possui divergências; promoção não sobrescreveu dados.",
                plano["conflitos"],
            )
        if not plano["campos_preenchidos"]:
            return {
                "acao": "SEM_ALTERACAO",
                "tabela": "cti_anfir",
                "hash_registro": registro["hash_registro"],
                "regra_merge": plano["regra"],
            }
        registro = plano["mesclado"]

    resultado = repository.persistir_registros_idempotente([registro])
    if resultado.get("erros"):
        raise RuntimeError(str(resultado.get("amostra_erros") or "Erro ao promover registro ANFIR."))
    acao = "INSERIDO" if resultado.get("inseridos") else "ENRIQUECIDO_SEM_SOBRESCRITA" if resultado.get("atualizados") else "DUPLICADO_IGNORADO"
    return {
        "acao": acao,
        "resultado": resultado,
        "tabela": "cti_anfir",
        "hash_registro": registro["hash_registro"],
        "regra_merge": "CTI_MERGE_SEGURO_SEM_SOBRESCRITA_V1",
    }


def promover_item(dominio: str, item: dict[str, Any], *, fonte_nome: str | None = None) -> dict[str, Any]:
    entidade = str(item.get("entidade_sugerida") or "").upper()
    suporte = suporte_promocao(dominio, entidade)
    if not suporte["suportado"]:
        raise ValueError(str(suporte.get("motivo")))
    dados = item.get("dados_normalizados") if isinstance(item.get("dados_normalizados"), dict) else {}
    if dominio == "CRM_COMERCIAL" and entidade == "CLIENTE":
        return promover_cliente(dados)
    if dominio == "CTI_ANFIR" and entidade == "ANFIR":
        return promover_anfir(dados, chave_canonica=str(item.get("chave_canonica") or ""), fonte_nome=fonte_nome)
    raise ValueError("Adaptador de promoção não resolvido.")
