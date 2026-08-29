from __future__ import annotations

import unicodedata
from datetime import date, datetime, timedelta
from typing import Iterable

VIENA_DDDS = {"011", "012", "013", "014", "015", "018"}

# Municípios efetivamente observados na fonte Carrier/JOV 2026 e reconciliados
# na auditoria ANFIR. A fonte bruta não fornece DDD, então o recorte territorial
# precisa ser resolvido antes de publicar inteligência Viena. O mapa é apenas
# territorial: não atribui vendedor quando o DDD 011 é compartilhado.
MUNICIPIO_DDD_SP = {
    "ANDRADINA": "018", "ANGATUBA": "015", "APARECIDA": "012", "ARACARIGUAMA": "011",
    "ARACATUBA": "018", "ARUJA": "011", "ATIBAIA": "011", "BARIRI": "014",
    "BARUERI": "011", "BAURU": "014", "BERNARDINO DE CAMPOS": "014", "BIRIGUI": "018",
    "BOITUVA": "015", "BOM JESUS DOS PERDOES": "011", "BORACEIA": "014", "CABREUVA": "011",
    "CAJAMAR": "011", "CANDIDO MOTA": "018", "CAPAO BONITO": "015", "CARAGUATATUBA": "012",
    "CARAPICUIBA": "011", "CONCHAS": "014", "COTIA": "011", "CUBATAO": "013",
    "DIADEMA": "011", "EMBU DAS ARTES": "011", "EMBU-GUACU": "011", "FRANCO DA ROCHA": "011",
    "GALIA": "014", "GARCA": "014", "GUARAREMA": "011", "GUARATINGUETA": "012",
    "GUARUJA": "013", "GUARULHOS": "011", "IACRI": "014", "IBIUNA": "015",
    "ITANHAEM": "013", "ITAPECERICA DA SERRA": "011", "ITAPETININGA": "015", "ITAPEVA": "015",
    "ITAPEVI": "011", "ITAPUI": "014", "ITAQUAQUECETUBA": "011", "ITATIBA": "011",
    "ITU": "011", "ITUPEVA": "011", "JACAREI": "012", "JANDIRA": "011",
    "JARINU": "011", "JAU": "014", "JUNDIAI": "011", "LENCOIS PAULISTA": "014",
    "LINS": "014", "LOUVEIRA": "019", "MARILIA": "014", "MAUA": "011",
    "MOGI DAS CRUZES": "011", "MONTE CASTELO": "018", "OSASCO": "011", "OURINHOS": "014",
    "PARAGUACU PAULISTA": "018", "PARANAPANEMA": "014", "PEDERNEIRAS": "014", "PEREIRA BARRETO": "018",
    "PIEDADE": "015", "PRAIA GRANDE": "013", "PRESIDENTE BERNARDES": "018", "PRESIDENTE EPITACIO": "018",
    "RANCHARIA": "018", "REGISTRO": "013", "SANTA CRUZ DO RIO PARDO": "014", "SANTANA DE PARNAIBA": "011",
    "SANTO ANDRE": "011", "SANTOS": "013", "SAO BERNARDO DO CAMPO": "011", "SAO CAETANO DO SUL": "011",
    "SAO JOSE DOS CAMPOS": "012", "SAO PAULO": "011", "SAO VICENTE": "013", "SOROCABA": "015",
    "SUZANO": "011", "TAGUAI": "014", "TATUI": "015", "TAUBATE": "012",
    "TREMEMBE": "012", "TUPA": "014", "UBATUBA": "012", "VARZEA PAULISTA": "011",
    "VOTORANTIM": "015",
}


def _sem_acento(valor) -> str:
    texto = str(valor or "").strip().upper()
    return "".join(
        caractere for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )


def normalizar_ddd(valor) -> str | None:
    if valor in (None, ""):
        return None
    digitos = "".join(c for c in str(valor) if c.isdigit())
    if not digitos:
        return None
    return digitos[-3:].zfill(3)


def resolver_ddd_registro(registro: dict) -> str | None:
    explicito = normalizar_ddd(registro.get("ddd") or registro.get("codigo_ddd"))
    if explicito:
        return explicito
    estado = str(registro.get("estado") or registro.get("uf") or "").strip().upper()
    if estado != "SP":
        return None
    cidade = _sem_acento(registro.get("cidade") or registro.get("municipio"))
    return MUNICIPIO_DDD_SP.get(cidade)


def resolver_periodo(periodo: str = "TODO_HISTORICO", inicio: date | None = None, fim: date | None = None):
    hoje = date.today()
    if periodo == "TODO_HISTORICO": return None, None
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


def _competencia_referencia(registro: dict) -> date | None:
    """Resolve a competência declarada pela própria fonte ANFIR."""
    try:
        ano = int(registro.get("ano_referencia") or 0)
        mes = int(registro.get("mes") or 0)
        if ano >= 2000 and 1 <= mes <= 12:
            return date(ano, mes, 1)
    except (TypeError, ValueError):
        pass
    return None


def data_registro(registro: dict) -> date | None:
    # Para ANFIR, competência de referência prevalece sobre uma data comercial
    # conflitante. Em registros sem ano_referencia válido, preservamos a ordem
    # histórica de datas reais e somente depois recorremos a ano/mês.
    competencia = _competencia_referencia(registro)
    if competencia:
        return competencia

    for campo in ("data_venda", "data", "data_emissao", "data_pedido"):
        valor = registro.get(campo)
        if not valor:
            continue
        if isinstance(valor, datetime): return valor.date()
        if isinstance(valor, date): return valor
        texto = str(valor).strip()
        for candidato in (texto[:10], texto):
            try: return date.fromisoformat(candidato)
            except ValueError: pass
        for formato in ("%d/%m/%Y", "%d-%m-%Y"):
            try: return datetime.strptime(texto[:10], formato).date()
            except ValueError: pass

    try:
        ano = int(registro.get("ano") or 0)
        mes = int(registro.get("mes") or 0)
        if ano >= 2000 and 1 <= mes <= 12:
            return date(ano, mes, 1)
    except (TypeError, ValueError):
        pass

    for campo in ("created_at", "updated_at"):
        valor = registro.get(campo)
        if not valor:
            continue
        if isinstance(valor, datetime): return valor.date()
        if isinstance(valor, date): return valor
        try: return date.fromisoformat(str(valor).strip()[:10])
        except ValueError: pass
    return None


def _fonte_carrier_jov(registro: dict) -> bool:
    aba = _sem_acento(registro.get("aba_origem"))
    versao = str(registro.get("versao_parser") or "").strip()
    pipeline = str(registro.get("pipeline") or "").strip().upper()
    return aba.startswith("RELATORIO PERFORMANCE ") or versao.startswith("3.1") or (
        pipeline == "UPLOAD_ANFIR_OPERACIONAL" and "REPRESENTACAO: JOV" in _sem_acento(registro.get("ocorrencia"))
    )


def _ano_snapshot(registro: dict) -> int | None:
    """Obtém o ano de referência sem recorrer a created_at/data de upload."""
    for campo in ("ano_referencia", "ano"):
        try:
            ano = int(registro.get(campo) or 0)
            if ano >= 2000:
                return ano
        except (TypeError, ValueError):
            pass
    competencia = _competencia_referencia(registro)
    return competencia.year if competencia else None


def selecionar_snapshot_viena(registros: Iterable[dict]) -> list[dict]:
    """Evita somar snapshots redundantes da ANFIR no contexto Viena.

    Quando existe uma fonte Carrier/JOV autoritativa para determinado ano, ela
    substitui analiticamente apenas os snapshots anteriores da própria base
    Viena daquele mesmo ano. Nada é apagado do banco e fontes de outros dealers
    não são descartadas. Anos sem fonte Carrier/JOV permanecem inalterados.
    """
    base = list(registros or [])
    anos_autoritativos = {
        ano for registro in base
        if _fonte_carrier_jov(registro) and (ano := _ano_snapshot(registro)) is not None
    }
    if not anos_autoritativos:
        return base

    resultado = []
    for registro in base:
        ano = _ano_snapshot(registro)
        origem = str(registro.get("origem_base") or "").strip().upper()
        autorizado = str(registro.get("autorizado") or registro.get("dealer") or "").strip().upper()
        pertence_cluster_viena = origem == "VIENA_SP" or autorizado == "VIENA"
        if ano in anos_autoritativos and pertence_cluster_viena and not _fonte_carrier_jov(registro):
            continue
        resultado.append(registro)
    return resultado


def _registro_viena(registro: dict, origem: str, autorizado: str) -> bool:
    if origem != "VIENA_SP" and autorizado != "VIENA":
        return False

    # Bases VIENA_SP históricas/canônicas já eram previamente autorizadas e
    # permanecem compatíveis. O recorte geográfico rígido é exigido somente na
    # fonte Carrier/JOV bruta, que contém registros externos ao território.
    if not _fonte_carrier_jov(registro):
        return True

    estado = str(registro.get("estado") or registro.get("uf") or "").strip().upper()
    if estado and estado != "SP":
        return False
    ddd = resolver_ddd_registro(registro)
    return bool(ddd and ddd in VIENA_DDDS)


def filtrar_registros(registros: Iterable[dict], contexto: str = "brasil", uf: str | None = None, ddd: str | None = None, inicio: date | None = None, fim: date | None = None) -> list[dict]:
    uf_normalizada = str(uf).strip().upper() if uf else None
    ddd_normalizado = normalizar_ddd(ddd)
    base = list(registros or [])
    if contexto == "viena-sp" or contexto.startswith("ddd-"):
        base = selecionar_snapshot_viena(base)

    resultado = []
    for registro in base:
        estado = str(registro.get("estado") or registro.get("uf") or "").strip().upper()
        origem = str(registro.get("origem_base") or "").strip().upper()
        autorizado = str(registro.get("autorizado") or registro.get("dealer") or "").strip().upper()
        registro_ddd = resolver_ddd_registro(registro)
        pertence_viena = _registro_viena(registro, origem, autorizado)

        if contexto == "viena-sp" and not pertence_viena: continue
        if contexto.startswith("uf-") and estado != contexto[3:].upper(): continue
        if contexto.startswith("ddd-"):
            contexto_ddd = normalizar_ddd(contexto[4:])
            if contexto_ddd not in VIENA_DDDS or not pertence_viena or registro_ddd != contexto_ddd: continue
        if uf_normalizada and estado != uf_normalizada: continue
        if ddd_normalizado and registro_ddd != ddd_normalizado: continue

        data = data_registro(registro)
        if inicio and (not data or data < inicio): continue
        if fim and (not data or data > fim): continue
        registro_saida = dict(registro)
        if registro_ddd and not registro_saida.get("ddd"):
            registro_saida["ddd"] = registro_ddd
        resultado.append(registro_saida)

    return resultado


def opcoes_contexto(registros: Iterable[dict]) -> dict:
    base = list(registros or [])
    ufs = sorted({str(r.get("estado") or r.get("uf") or "").strip().upper() for r in base if r.get("estado") or r.get("uf")})
    ddds = sorted({d for r in base if (d := resolver_ddd_registro(r))})
    return {"ufs": ufs, "ddds": ddds, "viena_ddds": sorted(VIENA_DDDS)}
