from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FRONT = ROOT / "frontend" / "src"
UI_ROOTS = [FRONT / "app", FRONT / "components"]

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
USER_CALL = re.compile(
    r"\b(?:alert|confirm|prompt|setErro|setError|setMensagem|setAviso)\(\s*['\"]([^'\"]+)['\"]"
)
FIXED_LOCALE = [
    'toLocaleString("pt-BR"', "toLocaleString('pt-BR'",
    'toLocaleDateString("pt-BR"', "toLocaleDateString('pt-BR'",
    'Intl.NumberFormat("pt-BR"', "Intl.NumberFormat('pt-BR'",
    'Intl.DateTimeFormat("pt-BR"', "Intl.DateTimeFormat('pt-BR'",
]

# Rotas de API não são UI. Arquivos de teste/gerados também não entram na auditoria visual.
def ui_files():
    for root in UI_ROOTS:
        for path in root.rglob("*.tsx"):
            rel = path.relative_to(FRONT).as_posix()
            if rel.startswith("app/api/"):
                continue
            yield path, rel


def user_facing_fragments(source: str):
    for regex in (JSX_TEXT, USER_PROP, USER_CALL):
        for match in regex.finditer(source):
            yield match.group(1).strip(), source.count("\n", 0, match.start()) + 1


def test_toda_ui_evitar_locale_brasileiro_fixo():
    failures = []
    for path, rel in ui_files():
        source = path.read_text(encoding="utf-8")
        for token in FIXED_LOCALE:
            if token in source:
                failures.append(f"{rel}: locale fixo {token}")
    assert not failures, "\n" + "\n".join(failures)


def test_toda_ui_nao_expor_texto_portugues_fora_da_camda_i18n():
    failures = []
    for path, rel in ui_files():
        source = path.read_text(encoding="utf-8")
        for fragment, line in user_facing_fragments(source):
            if PORTUGUESE.search(fragment):
                failures.append(f"{rel}:{line}: {fragment[:180]}")
    assert not failures, (
        "\nTextos de interface ainda presos ao português. "
        "Migrar para catálogo semântico PT/EN/ES ou expressão dependente de locale:\n"
        + "\n".join(failures)
    )
