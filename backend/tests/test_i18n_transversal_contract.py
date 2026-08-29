from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FRONT = ROOT / "frontend" / "src"


def read(path: str) -> str:
    return (FRONT / path).read_text(encoding="utf-8")


def test_i18n_provider_e_tres_locales_permanecem_globais():
    layout = read("app/layout.tsx")
    context = read("core/i18n/I18nContext.tsx")
    catalog = read("core/i18n/catalog.ts")
    switcher = read("components/i18n/LanguageSwitcher.tsx")

    assert "<I18nProvider>" in layout
    assert 'LOCALES = ["pt-BR", "en", "es"]' in catalog
    assert 'locale: "pt-BR"' in switcher
    assert 'locale: "en"' in switcher
    assert 'locale: "es"' in switcher
    assert "document.documentElement.lang = locale" in context
    assert '"es-419"' in context


def test_superficies_criticas_nao_fixam_locale_ptbr():
    paths = [
        "app/propostas/[id]/page.tsx",
        "app/propostas/[id]/documento/page.tsx",
        "app/pedidos/[id]/page.tsx",
        "app/pedidos/[id]/documento/page.tsx",
        "app/implementadoras/page.tsx",
        "components/EmpresasSegurasPage.tsx",
        "app/crm-app/propostas/[id]/page.tsx",
        "app/crm-app/pedidos/[id]/page.tsx",
        "app/crm-app/historico/[oportunidadeId]/page.tsx",
    ]
    forbidden = [
        'toLocaleString("pt-BR"',
        "toLocaleString('pt-BR'",
        'toLocaleDateString("pt-BR"',
        "toLocaleDateString('pt-BR'",
        'Intl.NumberFormat("pt-BR"',
        "Intl.NumberFormat('pt-BR'",
    ]
    for path in paths:
        source = read(path)
        assert "useClosureI18n" in source, f"{path} precisa consumir o contrato i18n transversal"
        for token in forbidden:
            assert token not in source, f"{path} ainda fixa locale brasileiro: {token}"


def test_catalogos_semanticos_declaram_pt_en_es():
    for path in ["core/i18n/operational.ts", "core/i18n/clients.ts", "core/i18n/strategic.ts", "core/i18n/closure.ts"]:
        source = read(path)
        assert '"pt-BR"' in source
        assert re.search(r"\ben\s*[:=]", source)
        assert re.search(r"\bes\s*[:=]", source)


def test_fechamento_preserva_conceitos_e_dados_livres():
    glossary = read("core/i18n/SEMANTIC_GLOSSARY.md").lower()
    assert "dados livres" in glossary or "free-text" in glossary or "free text" in glossary
    assert "conceitos, não traduções literais" in glossary
