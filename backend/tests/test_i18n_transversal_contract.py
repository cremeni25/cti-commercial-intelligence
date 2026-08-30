from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FRONT = ROOT / "frontend" / "src"


def read(path: str) -> str:
    return (FRONT / path).read_text(encoding="utf-8")


def test_i18n_provider_permanece_global_mas_operacao_esta_fixa_em_ptbr():
    layout = read("app/layout.tsx")
    context = read("core/i18n/I18nContext.tsx")
    catalog = read("core/i18n/catalog.ts")
    switcher = read("components/i18n/LanguageSwitcher.tsx")

    assert "<I18nProvider>" in layout
    assert 'LOCALES = ["pt-BR", "en", "es"]' in catalog
    assert 'FIXED_LOCALE: Locale = "pt-BR"' in context
    assert "document.documentElement.lang = FIXED_LOCALE" in context
    assert "return null" in switcher
    assert 'locale: "en"' not in switcher
    assert 'locale: "es"' not in switcher


def test_superficies_criticas_continuam_consumindo_contrato_i18n_sem_reabrir_multilingue():
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
    for path in paths:
        source = read(path)
        assert "useClosureI18n" in source, f"{path} precisa continuar consumindo o contrato i18n transversal"


def test_catalogos_semanticos_podem_permanecer_preservados_para_uso_futuro():
    for path in ["core/i18n/operational.ts", "core/i18n/clients.ts", "core/i18n/strategic.ts", "core/i18n/closure.ts"]:
        source = read(path)
        assert '"pt-BR"' in source
        assert re.search(r"\ben\s*[:=]", source)
        assert re.search(r"\bes\s*[:=]", source)


def test_fechamento_preserva_conceitos_e_dados_livres():
    glossary = read("core/i18n/SEMANTIC_GLOSSARY.md").lower()
    assert "dados livres" in glossary or "free-text" in glossary or "free text" in glossary
    assert "conceitos, não traduções literais" in glossary
