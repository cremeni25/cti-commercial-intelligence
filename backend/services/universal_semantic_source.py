from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import re
from typing import Any

from openpyxl import load_workbook

MAX_REGISTROS = 5000
MAX_TEXTO_REGISTRO = 6000

CLASSIFICACOES = {
    "COMERCIAL": ("cliente", "oportunidade", "venda", "pedido", "proposta", "comissao", "preco", "preço", "faturamento"),
    "MERCADO_ANFIR": ("anfir", "implementadora", "emplacamento", "frota", "carroceria", "implemento"),
    "TECNICO_PRODUTO": ("equipamento", "modelo", "compressor", "refrigeracao", "refrigeração", "carrier", "transicold", "temperatura"),
    "TERRITORIAL": ("ddd", "territorio", "território", "regiao", "região", "cidade", "estado", "municipio", "município"),
    "FINANCEIRO": ("financeiro", "custo", "margem", "receita", "imposto", "valor", "pagamento"),
    "CONTRATUAL_DOCUMENTAL": ("contrato", "clausula", "cláusula", "termo", "assinatura", "proposta comercial"),
}


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _classificar(texto: str, tipo: str) -> tuple[str, float]:
    alvo = texto.casefold()
    placar: list[tuple[int, str]] = []
    for nome, termos in CLASSIFICACOES.items():
        pontos = sum(alvo.count(termo.casefold()) for termo in termos)
        placar.append((pontos, nome))
    placar.sort(reverse=True)
    pontos, nome = placar[0]
    if pontos <= 0:
        if tipo == "IMAGEM":
            return "DOCUMENTAL_VISUAL", 0.55
        return "DOCUMENTAL_GERAL", 0.50
    confianca = min(0.98, 0.60 + pontos * 0.035)
    return nome, round(confianca, 4)


def _chunks_texto(texto: str, *, origem: str) -> list[dict[str, Any]]:
    texto = re.sub(r"\s+", " ", texto or "").strip()
    if not texto:
        return []
    registros: list[dict[str, Any]] = []
    indice = 0
    for inicio in range(0, len(texto), MAX_TEXTO_REGISTRO):
        trecho = texto[inicio:inicio + MAX_TEXTO_REGISTRO].strip()
        if not trecho:
            continue
        registros.append({
            "indice": indice,
            "tipo_registro": "TRECHO_TEXTUAL",
            "conteudo_texto": trecho,
            "dados": {"texto": trecho},
            "metadados": {"origem": origem, "inicio_caractere": inicio},
        })
        indice += 1
    return registros[:MAX_REGISTROS]


def _planilha(conteudo: bytes) -> tuple[list[dict[str, Any]], list[str], str]:
    wb = load_workbook(BytesIO(conteudo), read_only=True, data_only=True)
    saida: list[dict[str, Any]] = []
    campos: set[str] = set()
    amostras: list[str] = []
    indice = 0
    for ws in wb.worksheets:
        linhas = ws.iter_rows(values_only=True)
        cabecalho = None
        for linha_num, linha in enumerate(linhas, start=1):
            valores = list(linha)
            if not any(v not in (None, "") for v in valores):
                continue
            if cabecalho is None:
                cabecalho = [(_texto(v) or f"coluna_{i+1}")[:120] for i, v in enumerate(valores)]
                continue
            dados = {cabecalho[i]: valores[i] for i in range(min(len(cabecalho), len(valores))) if valores[i] not in (None, "")}
            if not dados:
                continue
            campos.update(dados.keys())
            amostras.append(json.dumps(dados, ensure_ascii=False, default=str)[:1000])
            saida.append({
                "indice": indice,
                "tipo_registro": "LINHA_PLANILHA",
                "conteudo_texto": " | ".join(f"{k}: {v}" for k, v in dados.items())[:MAX_TEXTO_REGISTRO],
                "dados": dados,
                "metadados": {"aba": ws.title, "linha": linha_num},
            })
            indice += 1
            if indice >= MAX_REGISTROS:
                break
        if indice >= MAX_REGISTROS:
            break
    return saida, sorted(campos), "\n".join(amostras[:40])


def _json(conteudo: bytes) -> tuple[list[dict[str, Any]], list[str], str]:
    valor = json.loads(conteudo.decode("utf-8"))
    itens = valor if isinstance(valor, list) else [valor]
    saida = []
    campos: set[str] = set()
    for indice, item in enumerate(itens[:MAX_REGISTROS]):
        dados = item if isinstance(item, dict) else {"valor": item}
        campos.update(str(k) for k in dados.keys())
        saida.append({
            "indice": indice,
            "tipo_registro": "REGISTRO_JSON",
            "conteudo_texto": json.dumps(dados, ensure_ascii=False, default=str)[:MAX_TEXTO_REGISTRO],
            "dados": dados,
            "metadados": {},
        })
    return saida, sorted(campos), json.dumps(itens[:20], ensure_ascii=False, default=str)[:12000]


def gerar_semantica(nome: str, tipo: str, conteudo: bytes, resumo_estrutural: dict[str, Any]) -> dict[str, Any]:
    extensao = Path(nome).suffix.lower()
    registros: list[dict[str, Any]] = []
    campos: list[str] = []
    texto_classificacao = _texto(resumo_estrutural.get("amostra_textual"))

    if tipo == "PLANILHA" and extensao in {".xlsx", ".xlsm"}:
        registros, campos, texto_planilha = _planilha(conteudo)
        texto_classificacao = texto_planilha or texto_classificacao
    elif tipo == "DADOS_ESTRUTURADOS" and extensao == ".json":
        registros, campos, texto_json = _json(conteudo)
        texto_classificacao = texto_json or texto_classificacao
    else:
        registros = _chunks_texto(texto_classificacao, origem=tipo)
        campos = ["texto"] if registros else []

    if not registros:
        registros = [{
            "indice": 0,
            "tipo_registro": "METADADO_DOCUMENTAL",
            "conteudo_texto": f"Arquivo {nome}; tipo {tipo}; tamanho {len(conteudo)} bytes.",
            "dados": {
                "nome_arquivo": nome,
                "tipo_arquivo": tipo,
                "tamanho_bytes": len(conteudo),
                "resumo_estrutural": resumo_estrutural,
            },
            "metadados": {"sem_texto_extraivel": True},
        }]
        campos = ["nome_arquivo", "tipo_arquivo", "tamanho_bytes", "resumo_estrutural"]

    classificacao, confianca = _classificar(texto_classificacao + " " + nome, tipo)
    descricao = (
        f"Fonte dinâmica homologável '{nome}', classificada como {classificacao}. "
        f"Contém {len(registros)} registro(s) semântico(s) derivados do original preservado."
    )
    return {
        "classificacao_sugerida": classificacao,
        "confianca_classificacao": confianca,
        "descricao_semantica": descricao,
        "campos_semanticos": campos,
        "registros": registros,
        "total_registros": len(registros),
        "limite_registros_aplicado": len(registros) >= MAX_REGISTROS,
    }
