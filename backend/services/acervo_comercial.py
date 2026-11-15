"""Acervo comercial: o histórico pertence à empresa, não a quem o registrou.

Três garantias:

1. **Transferência de carteira que preserva a autoria.** Ao trocar o
   responsável de um cliente, uma regra do banco reatribui ao novo
   responsável TODAS as atividades e os negócios não arquivados daquele
   cliente, inclusive visitas já feitas e negócios ganhos/perdidos. Aqui a
   troca leva só o que está em aberto; o que já aconteceu volta ao autor
   original logo depois da troca.
2. **Exportação completa** (planilha com todas as tabelas comerciais).
3. **Cópias de segurança** no cofre privado, automáticas toda semana e antes
   de cada transferência de carteira.
"""
from __future__ import annotations

import io
import unicodedata
from datetime import datetime, timezone
from typing import Any, Iterable

from uuid import uuid4

from openpyxl import Workbook

STATUS_ATIVIDADE_FEITA = {
    "CONCLUIDA", "CONCLUIDO", "REALIZADA", "REALIZADO", "FINALIZADA", "FINALIZADO",
    "CANCELADA", "CANCELADO", "ARQUIVADA", "NAO_REALIZADA",
}
STATUS_NEGOCIO_ENCERRADO = {
    "GANHO", "PERDIDO", "CANCELADO", "CANCELADA", "FATURADO", "ENCERRADO", "ENCERRADA", "CONCLUIDO",
}
PERFIS_INATIVOS = {"INATIVO", "BLOQUEADO", "REJEITADO"}
CAMPOS_SENSIVEIS = ("senha", "password", "token", "secret", "api_key", "apikey", "hash")

# Tabelas do acervo comercial (nome da aba, tabela, colunas).
TABELAS_EXPORTACAO: tuple[tuple[str, str, str], ...] = (
    ("Clientes", "clientes", "*"),
    ("Oportunidades", "cti_oportunidades", "*"),
    ("Itens de oportunidade", "cti_oportunidade_itens", "*"),
    ("Propostas", "cti_propostas", "*"),
    ("Pedidos", "cti_pedidos", "*"),
    ("Atividades", "cti_atividades", "*"),
    ("Vendas", "vendas", "*"),
    ("Feiras - atendimentos", "cti_feira_atendimentos", "*"),
    ("Histórico de responsáveis", "cti_cliente_responsabilidade_historico", "*"),
    ("Usuários", "cti_users", "id,nome,email,tipo_usuario,cargo,funcao,codigo_regional,ativo,status_acesso,created_at"),
)
PASTA_BACKUP = "acervo"
LIMITE_PAGINA = 1000


class AcervoErro(ValueError):
    """Pedido inválido (destino inativo, mesma pessoa etc.)."""


class AcervoIncompleto(RuntimeError):
    """Uma tabela obrigatória não pôde ser lida: a cópia não é gerada."""


def _tabela_inexistente(erro: Exception) -> bool:
    texto = str(erro).lower()
    return "pgrst205" in texto or "42p01" in texto or ("relation" in texto and "does not exist" in texto) or "could not find the table" in texto


def _supabase():
    from core.supabase_client import supabase

    return supabase


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _fold(valor: Any) -> str:
    texto = str(valor or "").strip().upper().replace(" ", "_")
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def paginar(tabela: str, campos: str = "*", filtro=None) -> list[dict[str, Any]]:
    saida: list[dict[str, Any]] = []
    inicio = 0
    while True:
        consulta = _supabase().table(tabela).select(campos)
        if filtro:
            consulta = filtro(consulta)
        dados = consulta.range(inicio, inicio + LIMITE_PAGINA - 1).execute().data or []
        saida.extend(dados)
        if len(dados) < LIMITE_PAGINA:
            return saida
        inicio += LIMITE_PAGINA


def _em_lotes(ids: Iterable[str], tamanho: int = 200) -> Iterable[list[str]]:
    lista = list(ids)
    for i in range(0, len(lista), tamanho):
        yield lista[i:i + tamanho]


def usuario_inativo(perfil: dict[str, Any]) -> bool:
    return perfil.get("ativo") is False or _fold(perfil.get("status_acesso")) in PERFIS_INATIVOS


def atividade_feita(atividade: dict[str, Any]) -> bool:
    return _fold(atividade.get("status")) in STATUS_ATIVIDADE_FEITA


def negocio_encerrado(oportunidade: dict[str, Any]) -> bool:
    return bool(oportunidade.get("data_fechamento_real")) or _fold(oportunidade.get("status")) in STATUS_NEGOCIO_ENCERRADO


# --------------------------------------------------------------- autoria ---

def fotografar_autoria(cliente_ids: list[str]) -> dict[str, dict[str, str]]:
    """Quem é o autor de cada atividade feita e de cada negócio encerrado dos clientes.

    Todas as consultas são paginadas: um lote de clientes pode ter mais registros
    do que o limite de uma resposta do banco.
    """
    campos_atividade = "id,usuario_id,status,cliente_id,oportunidade_id"
    oportunidades: list[dict[str, Any]] = []
    atividades: list[dict[str, Any]] = []
    for lote in _em_lotes(cliente_ids):
        oportunidades += paginar("cti_oportunidades", "*", lambda q, l=lote: q.in_("cliente_id", l))
        atividades += paginar("cti_atividades", campos_atividade, lambda q, l=lote: q.in_("cliente_id", l))
    ids_oportunidade = [str(o["id"]) for o in oportunidades if o.get("id")]
    vistos = {str(a.get("id")) for a in atividades}
    for lote in _em_lotes(ids_oportunidade):
        for atividade in paginar("cti_atividades", campos_atividade, lambda q, l=lote: q.in_("oportunidade_id", l)):
            if str(atividade.get("id")) not in vistos:
                atividades.append(atividade)
                vistos.add(str(atividade.get("id")))
    return {
        "atividades": {str(a["id"]): str(a["usuario_id"]) for a in atividades if a.get("id") and a.get("usuario_id") and atividade_feita(a)},
        "oportunidades": {str(o["id"]): str(o["responsavel_id"]) for o in oportunidades if o.get("id") and o.get("responsavel_id") and negocio_encerrado(o)},
    }


# Diário de autoria: a fotografia fica gravada no cofre ANTES de qualquer troca de
# responsável. Se a troca ou a restauração cair no meio, a próxima operação do
# acervo (ou a cópia semanal) devolve a autoria a partir do diário.
PASTA_DIARIO = "autoria"


def _caminho_diario(operacao_id: str) -> str:
    from services import cofre_agente

    return cofre_agente.caminho(PASTA_BACKUP, PASTA_DIARIO, f"{operacao_id}.json")


def abrir_diario(foto: dict[str, dict[str, str]], descricao: str) -> str:
    from services import cofre_agente

    operacao_id = f"{_agora().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    cofre_agente.gravar(_caminho_diario(operacao_id), {"status": "pendente", "descricao": descricao, "criado_em": _agora().isoformat(), "foto": foto})
    return operacao_id


def fechar_diario(operacao_id: str, foto: dict[str, dict[str, str]], descricao: str) -> None:
    from services import cofre_agente

    cofre_agente.gravar(_caminho_diario(operacao_id), {"status": "concluida", "descricao": descricao, "concluida_em": _agora().isoformat(), "foto": foto})


def reparar_autoria_pendente() -> int:
    """Reaplica a autoria de operações que não terminaram. Retorna quantas foram reparadas."""
    from services import cofre_agente

    reparadas = 0
    for nome, registro in cofre_agente.ler_pasta(f"{PASTA_BACKUP}/{PASTA_DIARIO}").items():
        if isinstance(registro, dict) and registro.get("status") == "pendente":
            restaurar_autoria(registro.get("foto") or {})
            fechar_diario(nome.removesuffix(".json"), registro.get("foto") or {}, f"{registro.get('descricao')} (reparada)")
            reparadas += 1
    return reparadas


def trocar_responsavel_preservando(cliente_ids: list[str], atualizar, descricao: str) -> int:
    """Executa `atualizar()` (que troca o responsável dos clientes) sem perder a autoria.

    A fotografia é gravada no diário antes; a restauração roda mesmo se a troca falhar
    no meio; se a própria restauração falhar, o diário fica pendente para reparo.
    """
    foto = fotografar_autoria(cliente_ids)
    operacao_id = abrir_diario(foto, descricao)
    try:
        atualizar()
    finally:
        preservados = restaurar_autoria(foto)
        fechar_diario(operacao_id, foto, descricao)
    return preservados


def restaurar_autoria(foto: dict[str, dict[str, str]]) -> int:
    """Devolve ao autor original o que já tinha acontecido. Retorna quantos registros."""
    sb = _supabase()
    total = 0
    for tabela, campo, mapa in (("cti_atividades", "usuario_id", foto.get("atividades", {})), ("cti_oportunidades", "responsavel_id", foto.get("oportunidades", {}))):
        por_autor: dict[str, list[str]] = {}
        for registro_id, autor in mapa.items():
            por_autor.setdefault(autor, []).append(registro_id)
        for autor, ids in por_autor.items():
            for lote in _em_lotes(ids):
                sb.table(tabela).update({campo: autor}).in_("id", lote).execute()
                total += len(lote)
    return total


# ------------------------------------------------------------- carteiras ---

def carteiras() -> dict[str, Any]:
    """Quanto cada pessoa tem em aberto; destaque para quem está desativado."""
    sb = _supabase()
    usuarios = sb.table("cti_users").select("id,nome,email,tipo_usuario,ativo,status_acesso").execute().data or []
    clientes = paginar("clientes", "id,responsavel_comercial_id")
    oportunidades = paginar("cti_oportunidades", "*", lambda q: q.is_("arquivado_em", "null"))
    atividades = paginar("cti_atividades", "id,usuario_id,status")

    contagem: dict[str, dict[str, int]] = {}

    def somar(usuario_id: Any, chave: str) -> None:
        if usuario_id:
            contagem.setdefault(str(usuario_id), {"clientes": 0, "negocios_abertos": 0, "atividades_pendentes": 0})[chave] += 1

    for cliente in clientes:
        somar(cliente.get("responsavel_comercial_id"), "clientes")
    for oportunidade in oportunidades:
        if not negocio_encerrado(oportunidade):
            somar(oportunidade.get("responsavel_id"), "negocios_abertos")
    for atividade in atividades:
        if not atividade_feita(atividade):
            somar(atividade.get("usuario_id"), "atividades_pendentes")

    pessoas = []
    for perfil in usuarios:
        numeros = contagem.get(str(perfil.get("id")), {"clientes": 0, "negocios_abertos": 0, "atividades_pendentes": 0})
        if not any(numeros.values()) and not usuario_inativo(perfil):
            continue
        pessoas.append({
            "usuario_id": perfil.get("id"), "nome": perfil.get("nome"), "email": perfil.get("email"),
            "tipo_usuario": perfil.get("tipo_usuario"), "ativo": not usuario_inativo(perfil), **numeros,
        })
    pessoas.sort(key=lambda p: (p["ativo"], -(p["clientes"] + p["negocios_abertos"]), str(p["nome"] or "")))
    sem_dono = sum(1 for c in clientes if not c.get("responsavel_comercial_id"))
    return {
        "pessoas": pessoas,
        "clientes_sem_responsavel": sem_dono,
        "carteiras_paradas": sum(1 for p in pessoas if not p["ativo"] and (p["clientes"] or p["negocios_abertos"] or p["atividades_pendentes"])),
    }


def transferir_carteira(de_id: str, para_id: str, motivo: str, ator_id: str) -> dict[str, Any]:
    """Leva a carteira em aberto de uma pessoa para outra, preservando a autoria do histórico."""
    if de_id == para_id:
        raise AcervoErro("Origem e destino são a mesma pessoa.")
    sb = _supabase()
    perfis = {str(p["id"]): p for p in (sb.table("cti_users").select("id,nome,ativo,status_acesso").in_("id", [de_id, para_id]).execute().data or [])}
    if para_id not in perfis or usuario_inativo(perfis[para_id]):
        raise AcervoErro("O destino precisa ser um usuário ativo.")
    if de_id not in perfis:
        raise AcervoErro("Usuário de origem não encontrado.")

    backup = salvar_backup(f"antes da transferência da carteira de {perfis[de_id].get('nome') or de_id}")

    reparar_autoria_pendente()
    clientes = paginar("clientes", "id,responsavel_comercial_id,responsabilidade_tipo", lambda q: q.eq("responsavel_comercial_id", de_id))
    cliente_ids = [str(c["id"]) for c in clientes if c.get("id")]
    agora = _agora().isoformat()

    def atualizar() -> None:
        for lote in _em_lotes(cliente_ids):
            sb.table("clientes").update({
                "responsavel_comercial_id": para_id, "responsabilidade_tipo": "ATRIBUICAO_MASTER",
                "responsabilidade_atualizada_em": agora, "responsabilidade_atualizada_por": ator_id,
            }).in_("id", lote).execute()

    preservados = trocar_responsavel_preservando(cliente_ids, atualizar, f"transferência {de_id} -> {para_id}")
    historico = [{
        "cliente_id": c["id"], "responsavel_anterior_id": de_id, "responsavel_novo_id": para_id,
        "tipo_anterior": c.get("responsabilidade_tipo"), "tipo_novo": "ATRIBUICAO_MASTER",
        "motivo": f"Transferência de carteira: {motivo}".strip(), "alterado_por": ator_id,
    } for c in clientes if c.get("id")]
    for i in range(0, len(historico), 200):
        sb.table("cti_cliente_responsabilidade_historico").insert(historico[i:i + 200]).execute()

    # Negócios e atividades em aberto que não vieram junto com os clientes.
    negocios = [o for o in paginar("cti_oportunidades", "*", lambda q: q.eq("responsavel_id", de_id).is_("arquivado_em", "null")) if not negocio_encerrado(o)]
    for lote in _em_lotes([str(o["id"]) for o in negocios]):
        sb.table("cti_oportunidades").update({"responsavel_id": para_id}).in_("id", lote).execute()
    pendentes = [a for a in paginar("cti_atividades", "id,usuario_id,status", lambda q: q.eq("usuario_id", de_id)) if not atividade_feita(a)]
    for lote in _em_lotes([str(a["id"]) for a in pendentes]):
        sb.table("cti_atividades").update({"usuario_id": para_id}).in_("id", lote).execute()

    return {
        "clientes": len(cliente_ids), "negocios_abertos": len(negocios), "atividades_pendentes": len(pendentes),
        "historico_preservado": preservados, "backup": backup.get("arquivo"),
    }


# ------------------------------------------------------------ exportação ---

def _celula(valor: Any) -> Any:
    if valor is None or isinstance(valor, (int, float, bool)):
        return valor
    if isinstance(valor, (dict, list)):
        import json

        return json.dumps(valor, ensure_ascii=False, default=str)[:32000]
    return str(valor)[:32000]


def _linhas_planilha(nome: str, linhas: list[dict[str, Any]]):
    colunas: list[str] = []
    for linha in linhas:
        for chave in linha:
            if chave not in colunas and not any(s in chave.lower() for s in CAMPOS_SENSIVEIS):
                colunas.append(chave)
    return nome[:31], colunas, [[_celula(linha.get(c)) for c in colunas] for linha in linhas]


def gerar_exportacao() -> tuple[bytes, dict[str, int]]:
    """Planilha com todo o acervo comercial (sem senhas nem chaves)."""
    wb = Workbook(write_only=True)
    totais: dict[str, int] = {}
    abas: list[tuple[str, list[dict[str, Any]]]] = []
    ausentes: list[str] = []
    for nome, tabela, campos in TABELAS_EXPORTACAO:
        try:
            abas.append((nome, paginar(tabela, campos)))
        except Exception as erro:
            # Só a tabela que não existe neste ambiente é tolerada (e fica registrada no
            # resumo). Qualquer outra falha (tempo esgotado, permissão, rede) interrompe a
            # cópia: uma cópia incompleta não pode passar por completa.
            if not _tabela_inexistente(erro):
                raise AcervoIncompleto(f"Não foi possível ler {nome}: {erro}") from erro
            ausentes.append(nome)
    try:
        from services import planilhas_comerciais

        for nome, fonte in (("Funil (planilha)", "funil_vendas_atual"), ("Negociações (planilha)", "negociacoes_andamento"), ("Vendas (planilha)", "vendas_realizadas")):
            abas.append((nome, planilhas_comerciais.registros(fonte)))
    except Exception:
        pass
    resumo = wb.create_sheet("Resumo")
    resumo.append(["Acervo comercial CTI", _agora().isoformat()])
    if ausentes:
        resumo.append(["Tabelas inexistentes neste ambiente", ", ".join(ausentes)])
    resumo.append(["Aba", "Registros"])
    for nome, linhas in abas:
        titulo, colunas, valores = _linhas_planilha(nome, linhas)
        aba = wb.create_sheet(titulo)
        aba.append(colunas or ["(sem registros)"])
        for linha in valores:
            aba.append(linha)
        totais[nome] = len(linhas)
        resumo.append([nome, len(linhas)])
    saida = io.BytesIO()
    wb.save(saida)
    return saida.getvalue(), totais


# --------------------------------------------------------------- backups ---

def salvar_backup(motivo: str) -> dict[str, Any]:
    from services import cofre_agente

    conteudo, totais = gerar_exportacao()
    momento = _agora()
    arquivo = f"backup-{momento.strftime('%Y-%m-%d-%H%M%S')}.xlsx"
    cofre_agente.gravar_binario(cofre_agente.caminho(PASTA_BACKUP, arquivo), conteudo, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    registro = {"arquivo": arquivo, "criado_em": momento.isoformat(), "motivo": motivo, "bytes": len(conteudo), "totais": totais}
    cofre_agente.gravar(cofre_agente.caminho(PASTA_BACKUP, arquivo.replace(".xlsx", ".json")), registro)
    return registro


def listar_backups(limite: int = 30) -> list[dict[str, Any]]:
    from services import cofre_agente

    registros = [r for r in cofre_agente.ler_pasta(PASTA_BACKUP).values() if isinstance(r, dict) and r.get("arquivo")]
    registros.sort(key=lambda r: str(r.get("criado_em") or ""), reverse=True)
    saida = []
    for registro in registros[:limite]:
        saida.append({**registro, "url": cofre_agente.url_assinada(cofre_agente.caminho(PASTA_BACKUP, registro["arquivo"]), 3600)})
    return saida
