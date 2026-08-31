from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
FRONT = ROOT / "frontend" / "src"
UI_ROOTS = [FRONT / "app", FRONT / "components"]
LEGACY_CATALOG = json.loads((FRONT / "core/i18n/legacy-semantic.json").read_text(encoding="utf-8"))
LEGACY_CATALOG.update(json.loads((FRONT / "core/i18n/legacy-semantic-extra.json").read_text(encoding="utf-8")))

TEXT_AUDIT_EXCLUDED = {
    "app/page.tsx",
    "app/radar/page.tsx",
    "app/negocios/[slug]/page.tsx",
    "components/crm/CarrierProposalDocument.tsx",
    # A operação foi deliberadamente fixada em PT-BR. Estas superfícies novas/ativas
    # permanecem em PT-BR e não devem ser obrigadas pelo auditor legado a receber
    # equivalentes EN/ES enquanto o seletor multilíngue permanecer desativado.
    "app/dashboard/page.tsx",
    "app/dashboard/carteiras-comerciais/page.tsx",
    "app/dashboard/anfir-competitividade-relatorio/page.tsx",
    "app/upload/page.tsx",
    "components/AnfirWorkbookPanel.tsx",
    "components/AnfirWorkbookCharts.tsx",
}

PORTUGUESE = re.compile(
    r"\b(?:"
    r"não|nao|cliente|clientes|responsável|responsavel|responsáveis|responsaveis|"
    r"carregando|salvar|cancelar|excluir|editar|voltar|avançar|avancar|próximo|proximo|próxima|proxima|"
    r"nenhum|nenhuma|operação|operacao|configuração|configuracao|usuário|usuario|usuários|usuarios|"
    r"relatório|relatorio|relatórios|relatorios|pedido|pedidos|proposta|propostas|venda|vendas|"
    r"oportunidade|oportunidades|atividade|atividades|agenda|histórico|historico|visita|visitas|"
    r"buscar|pesquisar|abrir|fechar|descrição|descricao|observações|observacoes|endereço|endereco|"
    r"cidade|estado|telefone|contato|empresa|empresas|implementadora|implementadoras|transportadora|"
    r"transportadoras|locadora|locadoras|equipamento|equipamentos|ação|acao|ações|acoes|"
    r"concluída|concluida|concluído|concluido|pendente|elaboração|elaboracao|"
    r"preencha|selecione|informe|confirme|cadastro|cadastros|detalhes|resultado|"
    r"período|periodo|início|inicio|fim|hoje|amanhã|amanha|ontem|"
    r"somente|todos|todas|gerar|enviar|receber|liberada|liberado|análise|analise"
    r")\b",
    re.IGNORECASE,
)

JSX_TEXT = re.compile(r">\s*([^<>{}\n]*[A-Za-zÀ-ÿ][^<>{}\n]*)\s*<")
USER_PROP = re.compile(r"\b(?:placeholder|title|aria-label|alt)=['\"]([^'\"]+)['\"]")
USER_CALL = re.compile(r"\b(?:alert|confirm|prompt|setErro|setError|setMensagem|setAviso)\(\s*['\"]([^'\"]+)['\"]")


def normalize(value: str) -> str:
    return " ".join(value.replace("\u00ad", "").split())


NORMALIZED_CATALOG = {normalize(key): value for key, value in LEGACY_CATALOG.items()}


def ui_files():
    for root in UI_ROOTS:
        for path in root.rglob("*.tsx"):
            rel = path.relative_to(FRONT).as_posix()
            if rel.startswith("app/api/"):
                continue
            yield path, rel


def looks_like_source_fragment(fragment: str) -> bool:
    technical = [
        "useState", "=>", "&&", "buscarSeguro", "buscarJson", ": Record", ": Array", "setClientes", "setPedidos",
        "setVendas", "setOportunidades", "@cliente.com", "@empresa.com",
    ]
    return any(token in fragment for token in technical) or fragment.startswith(("([])", "=(", ":", "("))


def user_facing_fragments(source: str):
    for regex in (JSX_TEXT, USER_PROP, USER_CALL):
        for match in regex.finditer(source):
            fragment = match.group(1).strip()
            if not fragment or looks_like_source_fragment(fragment):
                continue
            yield fragment, source.count("\n", 0, match.start()) + 1


def test_ponte_semantica_global_esta_montada_e_localiza_formatos():
    layout = (FRONT / "app/layout.tsx").read_text(encoding="utf-8")
    bridge = (FRONT / "components/i18n/LegacySemanticBridge.tsx").read_text(encoding="utf-8")
    assert "<LegacySemanticBridge />" in layout
    assert "legacy-semantic.json" in bridge
    assert "legacy-semantic-extra.json" in bridge
    assert "MutationObserver" in bridge
    assert "HTMLTextAreaElement" in bridge
    assert "localizeBrazilianFormats" in bridge
    assert "normalizeSemanticKey" in bridge
    assert '"en-US"' in bridge and '"es-419"' in bridge
    assert "Intl.NumberFormat" in bridge and "Intl.DateTimeFormat" in bridge


def test_texto_portugues_legado_tem_equivalencia_semantica_en_es():
    failures = []
    for path, rel in ui_files():
        if rel in TEXT_AUDIT_EXCLUDED:
            continue
        source = path.read_text(encoding="utf-8")
        for fragment, line in user_facing_fragments(source):
            if not PORTUGUESE.search(fragment):
                continue
            entry = NORMALIZED_CATALOG.get(normalize(fragment))
            if entry and entry.get("en") and entry.get("es"):
                continue
            failures.append(f"{rel}:{line}: {fragment[:220]}")
    assert not failures, (
        "\nTexto operacional em português sem equivalência conceitual EN/ES no catálogo de compatibilidade:\n"
        + "\n".join(failures)
    )