from __future__ import annotations

from io import BytesIO
import os

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

    # Import tardio: o SDK só entra em memória quando um PDF realmente
    # precisa do fallback visual. PDFs textuais e demais rotas do backend
    # não pagam esse custo de memória em repouso.
    from openai import OpenAI

    cliente = OpenAI()
    arquivo = None
    try:
        # Evita a cópia base64 do PDF inteiro em memória. O arquivo é enviado
        # pelo endpoint /files e referenciado na Responses API por file_id.
        stream = BytesIO(conteudo)
        stream.name = nome_arquivo or "documento.pdf"
        arquivo = cliente.files.create(
            file=stream,
            purpose="user_data",
            expires_after={"anchor": "created_at", "seconds": 3600},
        )

        resposta = cliente.responses.create(
            model=PDF_VISUAL_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "file_id": arquivo.id,
                        },
                        {"type": "input_text", "text": _INSTRUCAO_EXTRACAO},
                    ],
                }
            ],
            max_output_tokens=MAX_PDF_VISUAL_OUTPUT_TOKENS,
        )
        return str(getattr(resposta, "output_text", "") or "").strip()
    finally:
        if arquivo is not None:
            try:
                cliente.files.delete(arquivo.id)
            except Exception:
                pass
