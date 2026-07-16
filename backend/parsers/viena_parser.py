import hashlib
import re
import uuid
from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd

from models.cti_record import CTIRecord

ABAS_PROCESSADAS = {
    "BRASIL": {
        "origem_base": "BRASIL",
        "autorizado": None,
        "ano_referencia": None,
        "escopo_operacional": "NACIONAL",
    },
    "VIENA SP 2025": {
        "origem_base": "VIENA_SP",
        "autorizado": "VIENA",
        "ano_referencia": 2025,
        "escopo_operacional": "AUTORIZADO",
    },
    "VIENA SP 2026": {
        "origem_base": "VIENA_SP",
        "autorizado": "VIENA",
        "ano_referencia": 2026,
        "escopo_operacional": "AUTORIZADO",
    },
}

COLUNAS = {
    "data_venda": ["DATA", "DATA VENDA", "DT VENDA", "EMISSAO"],
    "responsavel": ["RESPONSAVEL", "RESPONSÁVEL", "VENDEDOR", "CONSULTOR"],
    "regiao": ["REGIAO", "REGIÃO"],
    "estado": ["ESTADO", "UF"],
    "ddd": ["DDD"],
    "cidade": ["MUNICIPIO", "MUNICÍPIO", "CIDADE"],
    "sub_regiao": ["SUB REGIAO", "SUB-REGIAO", "SUBREGIAO", "SUB REGIÃO"],
    "cliente": ["NOME_PROPRIETARIO", "NOME PROPRIETARIO", "CLIENTE", "PROPRIETARIO", "RAZAO SOCIAL", "RAZAO_SOCIAL"],
    "cnpj": ["CNPJ_FATURADO", "CNPJ FATURADO", "CNPJ"],
    "fabricante_caminhao": ["FABRICANTE CAMINHAO", "FABRICANTE_CAMINHAO", "FABRICANTE_CAMINHÃO"],
    "modelo_caminhao": ["MODELO CAMINHAO", "MODELO_CAMINHAO", "MODELO_CAMINHÃO"],
    "eixo": ["EIXO"],
    "tipo_veiculo": ["TIPO_VEICULO", "TIPO VEICULO"],
    "placa": ["PLACA"],
    "chassi": ["CHASSI"],
    "implementadora": ["IMPLEMENTADORA", "IMPLEMENTADOR"],
    "status": ["STATUS"],
    "motivo": ["MOTIVO"],
    "ocorrencia": ["OCORRENCIA", "OCORRÊNCIA"],
    "fabricante_equipamento": ["FABRICANTE EQUIPAMENTO", "FABRICANTE_EQUIPAMENTO"],
    "linha": ["LINHA DE PRODUTO", "LINHA", "PRODUTO"],
    "modelo": ["MODELO DE PRODUTO", "MODELO"],
    "modelo_carrier": ["MODELO DE PRODUTO - CARRIER"],
    "modelo_concorrencia": ["MODELO DE PRODUTO - CONCORRÊNCIA", "MODELO DE PRODUTO - CONCORRENCIA"],
    "valor": ["VALOR"],
    "valor_carrier": ["VALOR - CARRIER"],
    "valor_concorrencia": ["VALOR - CONCORRÊNCIA", "VALOR - CONCORRENCIA"],
}


def limpar_nome_coluna(nome):
    nome = "" if pd.isna(nome) else str(nome)
    nome = re.sub(r"\s+", " ", nome.strip().upper())
    return nome


def texto(valor):
    if pd.isna(valor):
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def texto_identificador(valor):
    return texto(valor).replace(".0", "")


def numero(valor):
    if pd.isna(valor) or valor == "":
        return 0.0
    if isinstance(valor, str):
        valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def normalizar_data(valor):
    if pd.isna(valor) or valor == "":
        return ""
    if isinstance(valor, (int, float)):
        try:
            return (datetime(1899, 12, 30) + timedelta(days=float(valor))).date().isoformat()
        except (TypeError, ValueError, OverflowError):
            return texto(valor)
    try:
        return pd.to_datetime(valor).date().isoformat()
    except Exception:
        return texto(valor)


def extrair_ano(data):
    try:
        return pd.to_datetime(data).year
    except Exception:
        return None


def extrair_mes(data):
    try:
        return pd.to_datetime(data).month
    except Exception:
        return None


def normalizar_chassi(chassi):
    return re.sub(r"[^A-Z0-9]", "", texto(chassi).upper())


def normalizar_placa(placa):
    return re.sub(r"[^A-Z0-9]", "", texto(placa).upper())


def localizar_cabecalho(df):
    melhor_linha = None
    maior_pontuacao = -1
    aliases = {alias for lista in COLUNAS.values() for alias in lista}
    for indice in range(min(len(df), 30)):
        linha = [limpar_nome_coluna(c) for c in df.iloc[indice].tolist()]
        pontuacao = sum(1 for coluna in linha if coluna in aliases)
        if pontuacao > maior_pontuacao:
            maior_pontuacao = pontuacao
            melhor_linha = indice
    return melhor_linha if maior_pontuacao > 0 else None


def normalizar_dataframe(df):
    cabecalho = localizar_cabecalho(df)
    if cabecalho is None:
        return None
    nomes = [limpar_nome_coluna(coluna) for coluna in df.iloc[cabecalho]]
    dados = df.iloc[cabecalho + 1:].copy()
    dados.columns = nomes
    return dados.reset_index(drop=True).fillna("")


def localizar_coluna(df, aliases):
    for alias in aliases:
        if alias in df.columns:
            return alias
    return None


def campo(df, row, nome):
    coluna = localizar_coluna(df, COLUNAS[nome])
    if coluna is None:
        return ""
    return row[coluna]


def chave_deduplicacao(registro):
    chassi = normalizar_chassi(registro.get("chassi"))
    placa = normalizar_placa(registro.get("placa"))
    origem = registro.get("origem_base") or "SEM_ORIGEM"
    ano = registro.get("ano_referencia") if origem == "VIENA_SP" else ""
    if chassi:
        chave = f"{origem}|{ano}|CHASSI|{chassi}"
    elif placa:
        chave = f"{origem}|{ano}|PLACA|{placa}"
    else:
        chave = f"{origem}|{ano}|TEMP|{uuid.uuid4()}"
    return chave


def gerar_hash(registro):
    return hashlib.sha256(chave_deduplicacao(registro).encode("utf-8")).hexdigest()


def gerar_id_operacional(registro):
    return gerar_hash(registro)


def valor_operacional(df, row):
    valor = numero(campo(df, row, "valor"))
    if valor:
        return valor
    status_motivo = f"{texto(campo(df, row, 'status'))} {texto(campo(df, row, 'motivo'))}".upper()
    if "CARRIER" in status_motivo:
        return numero(campo(df, row, "valor_carrier"))
    return numero(campo(df, row, "valor_concorrencia"))


def linha_valida(registro):
    if not registro.get("chassi") and not registro.get("placa") and not registro.get("cliente"):
        return False
    cliente = texto(registro.get("cliente")).upper()
    return cliente not in {"TOTAL", "TOTAL GERAL", "SUBTOTAL", "GERAL", "RESUMO"}


def converter_registro(df, row, nome_aba, contexto, arquivo_origem):
    data_venda = normalizar_data(campo(df, row, "data_venda"))
    ano_referencia = contexto["ano_referencia"] or extrair_ano(data_venda)
    registro = CTIRecord(
        ano=extrair_ano(data_venda),
        mes=extrair_mes(data_venda),
        data_venda=data_venda,
        responsavel=texto(campo(df, row, "responsavel")),
        regiao=texto(campo(df, row, "regiao")),
        estado=texto(campo(df, row, "estado")),
        ddd=texto_identificador(campo(df, row, "ddd")),
        cidade=texto(campo(df, row, "cidade")),
        sub_regiao=texto(campo(df, row, "sub_regiao")),
        cliente=texto(campo(df, row, "cliente")),
        cnpj=texto_identificador(campo(df, row, "cnpj")),
        fabricante_caminhao=texto(campo(df, row, "fabricante_caminhao")),
        modelo_caminhao=texto(campo(df, row, "modelo_caminhao")),
        eixo=texto(campo(df, row, "eixo")),
        tipo_veiculo=texto(campo(df, row, "tipo_veiculo")),
        placa=texto_identificador(campo(df, row, "placa")),
        chassi=texto_identificador(campo(df, row, "chassi")),
        implementadora=texto(campo(df, row, "implementadora")),
        fabricante_equipamento=texto(campo(df, row, "fabricante_equipamento")),
        linha=texto(campo(df, row, "linha")),
        modelo=texto(campo(df, row, "modelo")),
        status=texto(campo(df, row, "status")),
        motivo=texto(campo(df, row, "motivo")),
        ocorrencia=texto(campo(df, row, "ocorrencia")),
        valor=valor_operacional(df, row),
        origem_dado=contexto["origem_base"],
        arquivo_origem=arquivo_origem,
        aba_origem=nome_aba,
        versao_parser="3.0.0",
        pipeline="UPLOAD_ANFIR_OPERACIONAL",
        ativo=True,
        created_at=datetime.utcnow().isoformat(),
    ).to_dict()
    registro["modelo_carrier"] = texto(campo(df, row, "modelo_carrier"))
    registro["modelo_concorrencia"] = texto(campo(df, row, "modelo_concorrencia"))
    registro["origem_base"] = contexto["origem_base"]
    registro["autorizado"] = contexto["autorizado"]
    registro["ano_referencia"] = ano_referencia
    registro["escopo_operacional"] = contexto["escopo_operacional"]
    registro["hash_registro"] = gerar_hash(registro)
    registro["id_operacional"] = gerar_id_operacional(registro)
    return registro


def processar_aba(df, nome_aba, arquivo_origem="PLANILHA_ANFIR"):
    chave_aba = limpar_nome_coluna(nome_aba)
    contexto = ABAS_PROCESSADAS.get(chave_aba)
    if not contexto:
        return [], 0
    df = normalizar_dataframe(df)
    if df is None:
        return [], 0
    registros = []
    vistos = set()
    linhas_lidas = 0
    for _, row in df.iterrows():
        registro = converter_registro(df, row, nome_aba, contexto, arquivo_origem)
        if not linha_valida(registro):
            continue
        linhas_lidas += 1
        chave = registro["hash_registro"]
        if chave in vistos:
            continue
        vistos.add(chave)
        registros.append(registro)
    return registros, linhas_lidas


def criar_relatorio(arquivo):
    return {
        "arquivo": arquivo,
        "bases_processadas": {
            "BRASIL": {"abas": [], "linhas_lidas": 0, "inseridos": 0, "atualizados": 0, "duplicados_ignorados": 0, "erros": 0},
            "VIENA_SP": {"abas": [], "linhas_lidas": 0, "inseridos": 0, "atualizados": 0, "duplicados_ignorados": 0, "erros": 0},
        },
        "status": "PROCESSADO",
    }


def processar_planilha_viena_com_relatorio(contents, arquivo_origem="PLANILHA_ANFIR"):
    abas = pd.read_excel(BytesIO(contents), sheet_name=None, header=None, dtype=object)
    registros = []
    relatorio = criar_relatorio(arquivo_origem)
    for nome_aba, df in abas.items():
        chave_aba = limpar_nome_coluna(nome_aba)
        contexto = ABAS_PROCESSADAS.get(chave_aba)
        if not contexto:
            continue
        try:
            registros_aba, linhas_lidas = processar_aba(df, nome_aba, arquivo_origem)
            base = contexto["origem_base"]
            relatorio["bases_processadas"][base]["abas"].append(nome_aba)
            relatorio["bases_processadas"][base]["linhas_lidas"] += linhas_lidas
            relatorio["bases_processadas"][base]["duplicados_ignorados"] += max(linhas_lidas - len(registros_aba), 0)
            registros.extend(registros_aba)
        except Exception:
            relatorio["bases_processadas"][contexto["origem_base"]]["erros"] += 1
    if not registros:
        relatorio["status"] = "SEM_REGISTROS_PROCESSADOS"
    return registros, relatorio


def processar_planilha_viena(contents):
    registros, _ = processar_planilha_viena_com_relatorio(contents)
    return registros
