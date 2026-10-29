from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from postgrest.exceptions import APIError

from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase
from routers.crm_scope_clientes_router import _cliente_no_escopo, _exigir_permissao
from services.cnpj_enrichment_service import cnpj_valido, consultar_cnpj_publico, somente_digitos

router = APIRouter(prefix="/crm-app/clientes", tags=["CRM App"])


def _cadastro(item: dict, cnpj: str, tabela: str) -> dict:
    aliases = {
        "nome": ("nome", "razao_social", "cliente", "nome_fantasia"),
        "endereco": ("endereco", "logradouro"),
        "cidade": ("cidade", "municipio"),
        "estado": ("estado", "uf"),
        "fone": ("fone", "telefone"),
    }
    campos = ("id", "inscricao_estadual", "numero", "complemento", "bairro", "cep", "email", "ddd")
    dados = {campo: item.get(campo) for campo in campos}
    for campo, nomes in aliases.items():
        dados[campo] = next((item[n] for n in nomes if str(item.get(n) or "").strip()), None)
    return {**dados, "cnpj": cnpj, "origem_cadastro": tabela}


def _existente(cnpj: str):
    formatado = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    for tabela in ("clientes", "cti_clientes"):
        try:
            itens = supabase.table(tabela).select("*").in_("cnpj", [cnpj, formatado]).limit(1).execute().data or []
        except APIError as exc:
            # Apenas a ausência da fonte legada é compatibilidade esperada.
            if tabela == "cti_clientes" and exc.code in {"42P01", "PGRST205"}:
                continue
            raise HTTPException(503, "Não foi possível conferir o cadastro existente. Tente novamente.") from exc
        if itens:
            return itens[0], tabela
    return None


def _consulta_publica(cnpj: str) -> dict:
    resultado = consultar_cnpj_publico(cnpj)
    if not resultado.get("ok"):
        tipo = resultado.get("tipo")
        status_code = 422 if tipo == "CNPJ_INVALIDO" else 404 if tipo == "NAO_ENCONTRADO" else 503
        raise HTTPException(status_code=status_code, detail=resultado.get("detail") or "Não foi possível consultar o CNPJ.")
    return resultado["dados"]


@router.get("/cnpj/{cnpj}")
def consultar_cnpj_cliente(
    cnpj: str,
    cliente_id: str | None = None,
    usuario: UsuarioAutenticado = Depends(usuario_atual),
):
    _exigir_permissao(usuario, "clientes_editar")
    normalizado = somente_digitos(cnpj)
    if not cnpj_valido(normalizado):
        raise HTTPException(422, "CNPJ inválido.")
    encontrado = _existente(normalizado)
    if encontrado:
        item, tabela = encontrado
        if not _cliente_no_escopo(item, usuario):
            raise HTTPException(403, "Cliente fora do seu escopo comercial.")
        existente = _cadastro(item, normalizado, tabela)
        fonte = "CTI"
        # A consulta externa na edição só complementa o mesmo cadastro selecionado.
        if cliente_id and str(item.get("id")) == cliente_id:
            publicos = _consulta_publica(normalizado)
            for campo in existente:
                if campo not in {"id", "origem_cadastro"} and (existente[campo] is None or not str(existente[campo]).strip()):
                    existente[campo] = publicos.get(campo)
            fonte = publicos.get("fonte") or "CTI"
        return {"status": "CLIENTE_EXISTENTE", "cnpj": normalizado, "cliente": existente, "fonte": fonte}

    dados = _consulta_publica(normalizado)
    return {"status": "ENCONTRADO", "cnpj": normalizado, "dados": dados, "fonte": dados.get("fonte")}
