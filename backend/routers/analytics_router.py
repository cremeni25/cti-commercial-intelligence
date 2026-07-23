from datetime import date, timedelta
from io import BytesIO, StringIO
import csv

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from repositories.cti_repository import repository
from services.base_analytics import consolidar_dashboard
from services.commercial_intelligence import consolidar_inteligencia, opcoes_filtros

router = APIRouter()


def _registros_por_contexto(contexto: str):
    if contexto == "viena-sp":
        return repository.buscar_por_origem("VIENA_SP", "VIENA")
    if contexto == "outros-dealers":
        return [r for r in repository.buscar_cti_anfir() if not (r.get("origem_base") == "VIENA_SP" or r.get("autorizado") == "VIENA")]
    return repository.buscar_cti_anfir()


def _datas(periodo: str, inicio: date | None, fim: date | None):
    hoje = date.today()
    if periodo == "HOJE": return hoje, hoje
    if periodo == "ULTIMOS_7_DIAS": return hoje - timedelta(days=6), hoje
    if periodo == "ULTIMOS_30_DIAS": return hoje - timedelta(days=29), hoje
    if periodo == "ULTIMOS_90_DIAS": return hoje - timedelta(days=89), hoje
    if periodo == "MES_ATUAL": return hoje.replace(day=1), hoje
    if periodo == "TRIMESTRE_ATUAL":
        mes = ((hoje.month - 1) // 3) * 3 + 1
        return hoje.replace(month=mes, day=1), hoje
    if periodo == "ANO_ATUAL": return hoje.replace(month=1, day=1), hoje
    return inicio, fim


def _comparacao(modo, inicio, fim, comp_inicio, comp_fim, filtros):
    if modo == "PERSONALIZADO":
        return {**filtros, "inicio": comp_inicio, "fim": comp_fim}
    if not inicio or not fim or modo == "SEM_COMPARACAO":
        return None
    if modo == "PERIODO_ANTERIOR":
        duracao = (fim - inicio).days + 1
        return {**filtros, "inicio": inicio - timedelta(days=duracao), "fim": inicio - timedelta(days=1)}
    if modo == "ANO_ANTERIOR":
        def anterior(d):
            try: return d.replace(year=d.year - 1)
            except ValueError: return d.replace(year=d.year - 1, day=28)
        return {**filtros, "inicio": anterior(inicio), "fim": anterior(fim)}
    return None


def _filtros(segmento, periodo, inicio, fim, regiao, uf, dealer, implementadora, cliente, linha, familia, produto):
    inicio, fim = _datas(periodo, inicio, fim)
    return {"segmento": segmento, "inicio": inicio, "fim": fim, "regiao": regiao, "uf": uf, "dealer": dealer,
            "implementadora": implementadora, "cliente": cliente, "linha": linha, "familia": familia, "produto": produto}


@router.get("/analytics/dashboard")
def dashboard(contexto: str = Query("brasil", pattern="^(brasil|viena-sp)$")):
    return consolidar_dashboard(_registros_por_contexto(contexto))


@router.get("/analytics/intelligence")
def intelligence(
    contexto: str = Query("brasil", pattern="^(brasil|viena-sp|outros-dealers)$"),
    segmento: str = Query("GERAL", pattern="^(GERAL|TR|DT|DD|UNKNOWN)$"),
    periodo: str = Query("ULTIMOS_90_DIAS"), inicio: date | None = None, fim: date | None = None,
    comparacao: str = Query("PERIODO_ANTERIOR"), comparacao_inicio: date | None = None, comparacao_fim: date | None = None,
    regiao: str | None = None, uf: str | None = None, dealer: str | None = None,
    implementadora: str | None = None, cliente: str | None = None, linha: str | None = None,
    familia: str | None = None, produto: str | None = None,
):
    filtros = _filtros(segmento, periodo, inicio, fim, regiao, uf, dealer, implementadora, cliente, linha, familia, produto)
    comparativo = _comparacao(comparacao, filtros["inicio"], filtros["fim"], comparacao_inicio, comparacao_fim, filtros)
    return consolidar_inteligencia(_registros_por_contexto(contexto), contexto, segmento, filtros, comparativo)


@router.get("/analytics/intelligence/filter-options")
def filter_options(
    contexto: str = Query("brasil", pattern="^(brasil|viena-sp|outros-dealers)$"), segmento: str = "GERAL",
    periodo: str = "ULTIMOS_90_DIAS", inicio: date | None = None, fim: date | None = None,
    regiao: str | None = None, uf: str | None = None, dealer: str | None = None,
    implementadora: str | None = None, cliente: str | None = None, linha: str | None = None,
    familia: str | None = None, produto: str | None = None,
):
    filtros = _filtros(segmento, periodo, inicio, fim, regiao, uf, dealer, implementadora, cliente, linha, familia, produto)
    return {"opcoes": opcoes_filtros(_registros_por_contexto(contexto), filtros)}


@router.get("/analytics/intelligence/export")
def export_intelligence(request: Request, formato: str = Query("csv", pattern="^(csv|xlsx)$")):
    qp = request.query_params
    def data_param(nome):
        valor = qp.get(nome)
        return date.fromisoformat(valor) if valor else None
    payload = intelligence(
        contexto=qp.get("contexto", "brasil"), segmento=qp.get("segmento", "GERAL"),
        periodo=qp.get("periodo", "ULTIMOS_90_DIAS"), inicio=data_param("inicio"), fim=data_param("fim"),
        comparacao=qp.get("comparacao", "PERIODO_ANTERIOR"), comparacao_inicio=data_param("comparacao_inicio"),
        comparacao_fim=data_param("comparacao_fim"), regiao=qp.get("regiao"), uf=qp.get("uf"),
        dealer=qp.get("dealer"), implementadora=qp.get("implementadora"), cliente=qp.get("cliente"),
        linha=qp.get("linha"), familia=qp.get("familia"), produto=qp.get("produto"),
    )
    registros = payload["registros"]
    colunas = sorted({chave for registro in registros for chave in registro})
    if formato == "xlsx":
        from openpyxl import Workbook
        arquivo = BytesIO(); wb = Workbook(); ws = wb.active; ws.title = "Inteligencia"
        ws.append(colunas)
        for registro in registros: ws.append([registro.get(c) for c in colunas])
        wb.save(arquivo); arquivo.seek(0)
        return StreamingResponse(arquivo, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": "attachment; filename=inteligencia-comercial.xlsx"})
    arquivo_texto = StringIO(); writer = csv.DictWriter(arquivo_texto, fieldnames=colunas); writer.writeheader()
    for registro in registros: writer.writerow({c: registro.get(c) for c in colunas})
    return StreamingResponse(iter([arquivo_texto.getvalue()]), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": "attachment; filename=inteligencia-comercial.csv"})
