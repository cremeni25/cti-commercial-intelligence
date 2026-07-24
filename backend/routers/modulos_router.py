from collections import Counter
from datetime import date, datetime, timezone
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException

from core.supabase_client import supabase
from repositories.cti_repository import repository
from services.base_analytics import consolidar_implementadoras, valor_float
from services.operational_filters import filtrar_registros, resolver_periodo

router = APIRouter(prefix="/modulos", tags=["Módulos CTI"])

EQUIPAMENTOS = {
    "trailer": {"nome": "TR • Trailer", "termos": ("TRAILER", "VECTOR", "X4")},
    "diesel-truck": {"nome": "DT • Diesel Truck", "termos": ("DIESEL", "SUPRA")},
    "direct-drive": {"nome": "DD • Direct Drive", "termos": ("DIRECT", "CITIMAX", "XARIOS", "D6", "D7")},
}


def _todos_registros(contexto="brasil", periodo="TODO_HISTORICO", uf=None, ddd=None, inicio=None, fim=None):
    inicio, fim = resolver_periodo(periodo, inicio, fim)
    return filtrar_registros(repository.buscar_cti_anfir(), contexto=contexto, uf=uf, ddd=ddd, inicio=inicio, fim=fim), inicio, fim


def _texto_registro(registro):
    return " ".join(str(registro.get(campo) or "") for campo in ("linha", "modelo", "tipo_veiculo", "fabricante_equipamento")).upper()


CAMPOS_EMPRESA = ("empresa", "cliente", "transportadora", "razao_social", "razão social", "nome_cliente", "nome_proprietario")


def _nome_empresa(registro):
    for campo in CAMPOS_EMPRESA:
        valor = registro.get(campo)
        if valor:
            return str(valor).strip()
    return ""


def _valor_texto(registro, *campos):
    for campo in campos:
        valor = registro.get(campo)
        if valor is not None and str(valor).strip():
            return str(valor).strip()
    return ""


def _lista_segura(tabela):
    try:
        return supabase.table(tabela).select("*").execute().data or []
    except Exception:
        return []


def _data_iso(valor):
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(valor)[:10])
        except ValueError:
            return None


def _situacao_atividade(atividade):
    status = str(atividade.get("status") or "PENDENTE").upper()
    if status in {"CONCLUIDA", "CONCLUÍDA"}:
        return "CONCLUIDA"
    if status == "CANCELADA":
        return "CANCELADA"
    data_atividade = _data_iso(atividade.get("data"))
    hoje = datetime.now(timezone.utc).date()
    if not data_atividade:
        return "SEM_DATA"
    if data_atividade < hoje:
        return "ATRASADA"
    if data_atividade == hoje:
        return "HOJE"
    return "FUTURA"


def _consolidar_empresas(contexto="brasil", periodo="TODO_HISTORICO", uf=None, ddd=None, inicio=None, fim=None):
    base, _, _ = _todos_registros(contexto, periodo, uf, ddd, inicio, fim)
    registros = [r for r in base if _nome_empresa(r)]
    agrupado = {}

    for registro in registros:
        nome = _nome_empresa(registro)
        chave = nome.upper()
        item = agrupado.setdefault(
            chave,
            {
                "nome": nome,
                "quantidade_registros": 0,
                "valor_total": 0,
                "estados": set(),
                "municipios": set(),
                "linhas": set(),
                "status": Counter(),
                "chassis": set(),
                "placas": set(),
                "implementadoras": set(),
                "equipamentos": set(),
            },
        )
        item["quantidade_registros"] += 1
        item["valor_total"] += valor_float(registro.get("valor"))

        estado = _valor_texto(registro, "estado", "uf")
        municipio = _valor_texto(registro, "cidade", "municipio")
        linha = _valor_texto(registro, "linha", "produto")
        chassi = _valor_texto(registro, "chassi")
        placa = _valor_texto(registro, "placa")
        implementadora = _valor_texto(registro, "implementadora", "implementador")
        equipamento = _valor_texto(registro, "modelo_equipamento", "modelo", "linha", "produto")

        if estado:
            item["estados"].add(estado)
        if municipio:
            item["municipios"].add(municipio)
        if linha:
            item["linhas"].add(linha)
        if chassi:
            item["chassis"].add(chassi)
        if placa:
            item["placas"].add(placa)
        if implementadora:
            item["implementadoras"].add(implementadora)
        if equipamento:
            item["equipamentos"].add(equipamento)
        item["status"][registro.get("status") or "OUTROS"] += 1

    resultado = []
    for item in agrupado.values():
        item["valor_total"] = round(item["valor_total"], 2)
        item["estados"] = sorted(item["estados"])
        item["municipios"] = sorted(item["municipios"])
        item["linhas"] = sorted(item["linhas"])
        item["chassis"] = sorted(item["chassis"])
        item["placas"] = sorted(item["placas"])
        item["implementadoras"] = sorted(item["implementadoras"])
        item["equipamentos"] = sorted(item["equipamentos"])
        item["quantidade_chassis"] = len(item["chassis"])
        item["quantidade_placas"] = len(item["placas"])
        item["status"] = dict(item["status"])
        resultado.append(item)

    return sorted(resultado, key=lambda item: item["quantidade_registros"], reverse=True)


@router.get("/empresas")
def listar_empresas(contexto: str = "brasil", periodo: str = "TODO_HISTORICO", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None):
    return _consolidar_empresas(contexto, periodo, uf, ddd, inicio, fim)


@router.get("/clientes")
def listar_clientes(contexto: str = "brasil", periodo: str = "TODO_HISTORICO", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None):
    return _consolidar_empresas(contexto, periodo, uf, ddd, inicio, fim)


@router.get("/clientes/{nome_cliente}")
def detalhe_comercial_cliente(nome_cliente: str, contexto: str = "brasil", periodo: str = "TODO_HISTORICO", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None):
    nome = unquote(nome_cliente).strip()
    clientes = _consolidar_empresas(contexto, periodo, uf, ddd, inicio, fim)
    cliente = next((item for item in clientes if item["nome"].casefold() == nome.casefold()), None)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    oportunidades = [
        item for item in _lista_segura("cti_oportunidades")
        if str(item.get("cliente_id") or item.get("cliente") or item.get("nome_cliente") or "").casefold() == nome.casefold()
    ]
    ids_oportunidades = {item.get("id") for item in oportunidades if item.get("id")}
    atividades = [
        item for item in _lista_segura("cti_atividades")
        if item.get("oportunidade_id") in ids_oportunidades
        or str(item.get("cliente_id") or item.get("cliente") or "").casefold() == nome.casefold()
    ]
    for atividade in atividades:
        atividade["situacao"] = _situacao_atividade(atividade)

    abertas = [item for item in oportunidades if str(item.get("status") or "").upper() not in {"GANHO", "PERDIDO", "CANCELADO"}]
    atrasadas = [item for item in atividades if item["situacao"] == "ATRASADA"]
    futuras = [item for item in atividades if item["situacao"] in {"HOJE", "FUTURA"}]
    futuras.sort(key=lambda item: (item.get("data") or "9999-12-31", item.get("horario") or "23:59"))

    if atrasadas:
        prioridade = "ALTA"
        proxima_acao = atrasadas[0]
    elif abertas:
        prioridade = "MEDIA"
        proxima_acao = futuras[0] if futuras else {"titulo": "Agendar próximo follow-up", "situacao": "SEM_DATA"}
    else:
        prioridade = "BAIXA"
        proxima_acao = futuras[0] if futuras else None

    return {
        "cliente": cliente,
        "inteligencia": {
            "prioridade": prioridade,
            "oportunidades_abertas": len(abertas),
            "atividades_atrasadas": len(atrasadas),
            "valor_pipeline": round(sum(valor_float(item.get("valor_estimado")) for item in abertas), 2),
            "proxima_acao": proxima_acao,
        },
        "oportunidades": sorted(oportunidades, key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True),
        "atividades": sorted(atividades, key=lambda item: item.get("data") or "9999-12-31"),
    }


@router.get("/transportadoras")
def listar_transportadoras(contexto: str = "brasil", periodo: str = "TODO_HISTORICO", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None):
    return _consolidar_empresas(contexto, periodo, uf, ddd, inicio, fim)


@router.get("/implementadoras")
def listar_implementadoras(contexto: str = "brasil", periodo: str = "TODO_HISTORICO", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None):
    base, _, _ = _todos_registros(contexto, periodo, uf, ddd, inicio, fim)
    return consolidar_implementadoras(base)


@router.get("/equipamentos/{slug}")
def detalhe_equipamento(slug: str, contexto: str = "brasil", periodo: str = "TODO_HISTORICO", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None):
    config = EQUIPAMENTOS.get(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Equipamento não configurado")
    base, inicio_efetivo, fim_efetivo = _todos_registros(contexto, periodo, uf, ddd, inicio, fim)
    registros = [r for r in base if any(t in _texto_registro(r) for t in config["termos"])]
    estados = Counter(r.get("estado") for r in registros if r.get("estado"))
    implementadoras = Counter(r.get("implementadora") for r in registros if r.get("implementadora"))
    linhas = Counter(r.get("linha") for r in registros if r.get("linha"))
    empresas = Counter(_nome_empresa(r) for r in registros if _nome_empresa(r))
    valor_total = sum(valor_float(r.get("valor")) for r in registros)
    return {
        "slug": slug,
        "nome": config["nome"],
        "total_registros": len(registros),
        "valor_total": round(valor_total, 2),
        "metadata": {"contexto": contexto, "periodo": periodo, "uf": uf, "ddd": ddd, "inicio": inicio_efetivo.isoformat() if inicio_efetivo else None, "fim": fim_efetivo.isoformat() if fim_efetivo else None},
        "estados": [{"nome": n, "quantidade_registros": q} for n, q in estados.most_common()],
        "implementadoras": [{"nome": n, "quantidade_registros": q} for n, q in implementadoras.most_common()],
        "linhas": [{"nome": n, "quantidade_registros": q} for n, q in linhas.most_common()],
        "empresas": [{"nome": n, "quantidade_registros": q} for n, q in empresas.most_common(20)],
    }
