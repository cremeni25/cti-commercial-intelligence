from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Padrão ausente em {label}: {old[:100]}")
    return text.replace(old, new, 1)


router_path = "backend/routers/ia_comercial_artefatos_router.py"
router = read(router_path)
if "gerar_xlsx_resposta" not in router:
    router = replace_once(
        router,
        "from services.ia_comercial_artefatos import gerar_pdf_relatorio, gerar_svg_grafico\n",
        "from services.ia_comercial_artefatos import gerar_pdf_relatorio, gerar_svg_grafico\nfrom services.ia_comercial_arquivos import gerar_docx_resposta, gerar_pptx_resposta, gerar_xlsx_resposta\n",
        router_path,
    )
    router += '''\n\ndef _possui_tipo(mensagem: dict, tipo: str) -> bool:\n    return any(item.get("tipo") == tipo for item in _artefatos(mensagem))\n\n\n@router.get("/{mensagem_id}/planilha.xlsx")\ndef baixar_planilha_xlsx(\n    mensagem_id: str,\n    usuario: UsuarioAutenticado = Depends(usuario_atual),\n):\n    mensagem = _mensagem_do_usuario(mensagem_id, usuario)\n    if not _possui_tipo(mensagem, "PLANILHA_XLSX"):\n        raise HTTPException(status_code=404, detail="Esta mensagem não possui planilha solicitada.")\n    metadados = dict(mensagem.get("metadados") or {})\n    if mensagem.get("fontes") and not metadados.get("fontes"):\n        metadados["fontes"] = mensagem.get("fontes")\n    conteudo = gerar_xlsx_resposta(str(mensagem.get("conteudo") or ""), metadados)\n    return Response(\n        content=conteudo,\n        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",\n        headers={"Content-Disposition": f'attachment; filename="cti-planilha-{mensagem_id[:8]}.xlsx"'},\n    )\n\n\n@router.get("/{mensagem_id}/apresentacao.pptx")\ndef baixar_apresentacao_pptx(\n    mensagem_id: str,\n    usuario: UsuarioAutenticado = Depends(usuario_atual),\n):\n    mensagem = _mensagem_do_usuario(mensagem_id, usuario)\n    if not _possui_tipo(mensagem, "APRESENTACAO_PPTX"):\n        raise HTTPException(status_code=404, detail="Esta mensagem não possui apresentação solicitada.")\n    metadados = dict(mensagem.get("metadados") or {})\n    if mensagem.get("fontes") and not metadados.get("fontes"):\n        metadados["fontes"] = mensagem.get("fontes")\n    conteudo = gerar_pptx_resposta(str(mensagem.get("conteudo") or ""), metadados)\n    return Response(\n        content=conteudo,\n        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",\n        headers={"Content-Disposition": f'attachment; filename="cti-apresentacao-{mensagem_id[:8]}.pptx"'},\n    )\n\n\n@router.get("/{mensagem_id}/documento.docx")\ndef baixar_documento_docx(\n    mensagem_id: str,\n    usuario: UsuarioAutenticado = Depends(usuario_atual),\n):\n    mensagem = _mensagem_do_usuario(mensagem_id, usuario)\n    if not _possui_tipo(mensagem, "DOCUMENTO_DOCX"):\n        raise HTTPException(status_code=404, detail="Esta mensagem não possui documento solicitado.")\n    metadados = dict(mensagem.get("metadados") or {})\n    if mensagem.get("fontes") and not metadados.get("fontes"):\n        metadados["fontes"] = mensagem.get("fontes")\n    conteudo = gerar_docx_resposta(str(mensagem.get("conteudo") or ""), metadados)\n    return Response(\n        content=conteudo,\n        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",\n        headers={"Content-Disposition": f'attachment; filename="cti-documento-{mensagem_id[:8]}.docx"'},\n    )\n'''
    write(router_path, router)

frontend_path = "frontend/src/components/ia/IaArtefatos.tsx"
front = read(frontend_path)
if "PLANILHA_XLSX" not in front:
    front = replace_once(
        front,
        '  const relatorio = artefatos.find((item) => item.tipo === "RELATORIO_PDF")\n',
        '  const relatorio = artefatos.find((item) => item.tipo === "RELATORIO_PDF")\n  const planilha = artefatos.find((item) => item.tipo === "PLANILHA_XLSX")\n  const apresentacao = artefatos.find((item) => item.tipo === "APRESENTACAO_PPTX")\n  const documento = artefatos.find((item) => item.tipo === "DOCUMENTO_DOCX")\n',
        frontend_path,
    )
    marker = '''      {relatorio ? (\n        <button\n'''
    buttons = '''      <div className="flex flex-wrap gap-2">\n        {planilha ? (\n          <button type="button" onClick={() => void baixarAutenticado(`/api/crm-proxy/ia-comercial-cti/artefatos/${id}/planilha.xlsx`, `cti-planilha-${id.slice(0, 8)}.xlsx`).catch((e) => setErro(e instanceof Error ? e.message : "Falha ao baixar planilha."))} className="inline-flex items-center gap-2 rounded-xl border border-emerald-700 px-4 py-2.5 text-sm font-semibold text-emerald-200">\n            <Download size={17} /> Baixar planilha XLSX\n          </button>\n        ) : null}\n        {apresentacao ? (\n          <button type="button" onClick={() => void baixarAutenticado(`/api/crm-proxy/ia-comercial-cti/artefatos/${id}/apresentacao.pptx`, `cti-apresentacao-${id.slice(0, 8)}.pptx`).catch((e) => setErro(e instanceof Error ? e.message : "Falha ao baixar apresentação."))} className="inline-flex items-center gap-2 rounded-xl border border-violet-700 px-4 py-2.5 text-sm font-semibold text-violet-200">\n            <Download size={17} /> Baixar apresentação PPTX\n          </button>\n        ) : null}\n        {documento ? (\n          <button type="button" onClick={() => void baixarAutenticado(`/api/crm-proxy/ia-comercial-cti/artefatos/${id}/documento.docx`, `cti-documento-${id.slice(0, 8)}.docx`).catch((e) => setErro(e instanceof Error ? e.message : "Falha ao baixar documento."))} className="inline-flex items-center gap-2 rounded-xl border border-slate-600 px-4 py-2.5 text-sm font-semibold text-slate-200">\n            <FileText size={17} /> Baixar documento DOCX\n          </button>\n        ) : null}\n      </div>\n\n'''
    front = replace_once(front, marker, buttons + marker, frontend_path)
    write(frontend_path, front)

test_path = "backend/tests/test_cti_ia_arquivos.py"
if not (ROOT / test_path).exists():
    write(test_path, '''from services.ia_comercial_arquivos import gerar_docx_resposta, gerar_pptx_resposta, gerar_xlsx_resposta\n\nMETA = {"fontes": [{"tipo": "CTI", "descricao": "Teste"}], "artefatos": [{"tipo": "PLANILHA_XLSX", "dados": [{"label": "Supra", "valor": 10, "unidade": "un."}]}]}\n\ndef test_xlsx_valido():\n    data = gerar_xlsx_resposta("Análise frigorífica", META)\n    assert data[:2] == b"PK"\n\ndef test_pptx_valido():\n    data = gerar_pptx_resposta("Análise frigorífica", META)\n    assert data[:2] == b"PK"\n\ndef test_docx_valido():\n    data = gerar_docx_resposta("Análise frigorífica", META)\n    assert data[:2] == b"PK"\n''')

print("Artefatos Office completos aplicados")
