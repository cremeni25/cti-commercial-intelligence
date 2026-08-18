from __future__ import annotations

import base64
import os

from openai import OpenAI

PDF_VISUAL_MODEL = os.getenv("OPENAI_DOCUMENT_MODEL", os.getenv("OPENAI_AGENT_MODEL", "gpt-5.2"))
MAX_PDF_VISUAL_OUTPUT_TOKENS = max(2000, min(int(os.getenv("OPENAI_DOCUMENT_MAX_OUTPUT_TOKENS", "12000")), 24000))

_INSTRUCAO_EXTRACAO = """Extraia fielmente o conteúdo deste PDF para uso documental e auditável.
- Leia também conteúdo visual de páginas sem camada de texto, incluindo tabelas, quadros, legendas e rótulos.
- Preserve fabricantes, modelos, unidades, temperaturas, volumes, capacidades e relações de tabela.
- Não compare, não recomende, não complete lacunas e não invente valores.
- Quando houver tabela, represente-a em Markdown com cabeçalhos e células legíveis.
- Se algum campo não puder ser lido com segurança, escreva [ilegível].
- Retorne somente a transcrição/estrutura extraída, sem introdução ou conclusão.
"""


def extrair_pdf_visual(conteudo: bytes, nome_arquivo: str) -> str:
    if not conteudo:
        return ""
    cliente = OpenAI()
    dado = base64.b64encode(conteudo).decode("ascii")
    resposta = cliente.responses.create(
        model=PDF_VISUAL_MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "filename": nome_arquivo or "documento.pdf",
                        "file_data": f"data:application/pdf;base64,{dado}",
                    },
                    {"type": "input_text", "text": _INSTRUCAO_EXTRACAO},
                ],
            }
        ],
        max_output_tokens=MAX_PDF_VISUAL_OUTPUT_TOKENS,
    )
    return str(getattr(resposta, "output_text", "") or "").strip()
