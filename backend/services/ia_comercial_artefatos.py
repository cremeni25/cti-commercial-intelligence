from __future__ import annotations

import io
import re
import unicodedata
from datetime import datetime, timezone
from html import escape
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


_RE_ITEM_NUMERICO = re.compile(
    r"^\s*(?:\d+[.)-]?\s*)?(?P<label>[A-Za-zÀ-ÿ0-9 .&'()/\-]+?)\s*[—–-]\s*(?P<valor>\d[\d\.\s]*(?:,\d+)?)\s*(?P<unidade>[A-Za-zÀ-ÿ% ]*)\s*$"
)


def _normalizar(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(ch for ch in bruto if not unicodedata.combining(ch)).casefold()


def detectar_intencao_artefato(mensagem: str) -> set[str]:
    texto = _normalizar(mensagem)
    solicitados: set[str] = set()
    if any(termo in texto for termo in ("grafico", "chart", "visualizacao grafica", "visualize em barras")):
        solicitados.add("GRAFICO")
    if any(termo in texto for termo in ("relatorio", "report", "documento executivo", "relatorio executivo")):
        solicitados.add("RELATORIO")
    if any(termo in texto for termo in ("pdf", "arquivo para baixar", "download", "baixar", "imprimir", "compartilhar")):
        solicitados.add("PDF")
    if "RELATORIO" in solicitados:
        solicitados.add("PDF")
    return solicitados


def _numero_ptbr(valor: str) -> float | None:
    texto = valor.strip().replace(" ", "")
    if not texto:
        return None
    if "." in texto and "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "." in texto:
        partes = texto.split(".")
        if len(partes) > 1 and all(len(p) == 3 for p in partes[1:]):
            texto = "".join(partes)
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def extrair_serie_numerica(texto: str, limite: int = 20) -> list[dict[str, Any]]:
    dados: list[dict[str, Any]] = []
    for linha in str(texto or "").splitlines():
        match = _RE_ITEM_NUMERICO.match(linha.strip())
        if not match:
            continue
        valor = _numero_ptbr(match.group("valor"))
        if valor is None:
            continue
        label = match.group("label").strip(" .:-")
        unidade = match.group("unidade").strip()
        if not label or len(label) > 90:
            continue
        dados.append({"label": label, "valor": valor, "unidade": unidade})
        if len(dados) >= limite:
            break
    return dados


def _titulo_grafico(pergunta: str, fonte_texto: str) -> str:
    normalizado = _normalizar(pergunta)
    if "implementador" in normalizado or "implementadora" in _normalizar(fonte_texto):
        return "Implementadoras — frequência de registros no CTI"
    return "Análise gráfica — IA Comercial CTI"


def construir_artefatos(
    mensagem: str,
    resposta_texto: str,
    historico: list[dict[str, str]],
    fontes: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    solicitados = detectar_intencao_artefato(mensagem)
    if not solicitados:
        return []

    resposta_anterior = ""
    for item in reversed(historico):
        if item.get("role") == "assistant" and str(item.get("content") or "").strip():
            resposta_anterior = str(item["content"])
            break

    candidatos = [resposta_anterior, resposta_texto]
    serie: list[dict[str, Any]] = []
    fonte_serie = "resposta_atual"
    for indice, candidato in enumerate(candidatos):
        serie = extrair_serie_numerica(candidato)
        if len(serie) >= 2:
            fonte_serie = "resposta_anterior" if indice == 0 else "resposta_atual"
            break

    artefatos: list[dict[str, Any]] = []
    if "GRAFICO" in solicitados:
        if serie:
            artefatos.append(
                {
                    "tipo": "GRAFICO",
                    "formato": "BAR",
                    "titulo": _titulo_grafico(mensagem, resposta_anterior or resposta_texto),
                    "dados": serie,
                    "fonte_dados": fonte_serie,
                    "auditavel": True,
                }
            )
        else:
            artefatos.append(
                {
                    "tipo": "GRAFICO",
                    "status": "SEM_SERIE_NUMERICA",
                    "titulo": "Gráfico não gerado",
                    "mensagem": "A resposta de referência não contém uma série numérica suficiente para gerar um gráfico sem inventar dados.",
                    "auditavel": True,
                }
            )

    if "PDF" in solicitados or "RELATORIO" in solicitados:
        artefatos.append(
            {
                "tipo": "RELATORIO_PDF",
                "titulo": "Relatório — IA Comercial CTI",
                "fonte_dados": fonte_serie if serie else "resposta_atual",
                "inclui_grafico": bool(serie),
                "fontes": [
                    {"tipo": f.get("tipo"), "descricao": f.get("descricao"), "url": f.get("url")}
                    for f in (fontes or [])
                    if isinstance(f, dict)
                ],
                "auditavel": True,
            }
        )
    return artefatos


def _grafico_do_metadado(metadados: dict[str, Any]) -> dict[str, Any] | None:
    for artefato in metadados.get("artefatos") or []:
        if isinstance(artefato, dict) and artefato.get("tipo") == "GRAFICO" and artefato.get("dados"):
            return artefato
    return None


def gerar_svg_grafico(metadados: dict[str, Any]) -> bytes:
    grafico = _grafico_do_metadado(metadados)
    if not grafico:
        raise ValueError("Mensagem sem gráfico disponível.")
    dados = grafico.get("dados") or []
    largura, altura = 1000, max(420, 120 + len(dados) * 64)
    margem_esq, margem_dir = 250, 70
    area = largura - margem_esq - margem_dir
    maximo = max(float(item.get("valor") or 0) for item in dados) or 1
    linhas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}">',
        '<rect width="100%" height="100%" fill="#071427"/>',
        f'<text x="40" y="48" fill="#e2e8f0" font-family="Arial" font-size="24" font-weight="700">{escape(str(grafico.get("titulo") or "Gráfico CTI"))}</text>',
    ]
    y = 95
    for item in dados:
        label = escape(str(item.get("label") or ""))
        valor = float(item.get("valor") or 0)
        comprimento = max(2, area * valor / maximo)
        exibicao = f"{valor:,.0f}".replace(",", ".") if valor.is_integer() else f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        unidade = escape(str(item.get("unidade") or ""))
        linhas.extend(
            [
                f'<text x="40" y="{y + 25}" fill="#cbd5e1" font-family="Arial" font-size="18">{label}</text>',
                f'<rect x="{margem_esq}" y="{y}" width="{comprimento:.1f}" height="34" rx="7" fill="#06b6d4"/>',
                f'<text x="{min(margem_esq + comprimento + 12, largura - 120):.1f}" y="{y + 24}" fill="#e2e8f0" font-family="Arial" font-size="17">{exibicao} {unidade}</text>',
            ]
        )
        y += 64
    linhas.append('</svg>')
    return "".join(linhas).encode("utf-8")


def gerar_pdf_relatorio(conteudo: str, metadados: dict[str, Any], usuario_nome: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Relatório — IA Comercial CTI",
        author=usuario_nome,
    )
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("TituloCTI", parent=estilos["Title"], fontSize=18, leading=22, alignment=TA_CENTER, textColor=colors.HexColor("#0f172a"))
    corpo = ParagraphStyle("CorpoCTI", parent=estilos["BodyText"], fontSize=9.5, leading=14, spaceAfter=7)
    elementos: list[Any] = [
        Paragraph("Relatório — IA Comercial CTI", titulo),
        Spacer(1, 5 * mm),
        Paragraph(f"Gerado por: {escape(usuario_nome)}", corpo),
        Paragraph(f"Data: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}", corpo),
        Spacer(1, 3 * mm),
    ]
    for bloco in str(conteudo or "").split("\n\n"):
        texto = escape(bloco.strip()).replace("\n", "<br/>")
        if texto:
            elementos.append(Paragraph(texto, corpo))

    grafico = _grafico_do_metadado(metadados)
    if grafico:
        elementos.extend([Spacer(1, 4 * mm), Paragraph(escape(str(grafico.get("titulo") or "Gráfico")), estilos["Heading2"])])
        dados = [["Item", "Valor"]]
        for item in grafico.get("dados") or []:
            valor = float(item.get("valor") or 0)
            exibicao = f"{valor:,.0f}".replace(",", ".") if valor.is_integer() else str(valor)
            unidade = str(item.get("unidade") or "")
            dados.append([str(item.get("label") or ""), f"{exibicao} {unidade}".strip()])
        tabela = Table(dados, colWidths=[115 * mm, 45 * mm], repeatRows=1)
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.append(tabela)

    fontes = [f for f in (metadados.get("fontes") or []) if isinstance(f, dict)]
    if fontes:
        elementos.extend([Spacer(1, 5 * mm), Paragraph("Fontes", estilos["Heading2"])])
        for fonte in fontes:
            descricao = escape(str(fonte.get("descricao") or fonte.get("tipo") or "Fonte"))
            url = escape(str(fonte.get("url") or ""))
            elementos.append(Paragraph(f"• {descricao}{' — ' + url if url else ''}", corpo))

    doc.build(elementos)
    return buffer.getvalue()
