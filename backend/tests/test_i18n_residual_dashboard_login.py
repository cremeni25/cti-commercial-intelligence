from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
FRONT = ROOT / "frontend" / "src"


def test_login_nao_regride_para_rotulos_pt_fixos():
    source = (FRONT / "app/login/page.tsx").read_text(encoding="utf-8")
    assert "const ui =" in source
    assert 'const { t, locale } = useI18n()' in source
    assert "tx.fullName" in source
    assert "tx.confirmPassword" in source
    assert "tx.createFirstAccess" in source
    assert "tx.backToLogin" in source


def test_dashboard_anfir_residuos_visuais_tem_equivalencia_en_es():
    catalog = json.loads((FRONT / "core/i18n/legacy-semantic-extra.json").read_text(encoding="utf-8"))
    required = [
        "Evolução mensal 2026",
        "Tema",
        "Direct Drive é o maior mercado elegível e também o maior espaço competitivo: forte presença de fabricantes nacionais, baixa presença Carrier observada e grande incidência de não participação nas propostas.",
        "Trailer possui a posição competitiva mais forte da Carrier na ANFIR elegível. A defesa da base e o tratamento de TK devem ser prioridade, sem atribuir todas as perdas a preço.",
        "Diesel Truck apresenta mercado mais fragmentado: nacionais, usados, sem contato e equipamentos Carrier usados indicam oportunidade de renovação e reconquista, além da disputa tradicional com TK.",
        "O DDD 011 concentra a maior parte do mercado. Como há sobreposição comercial interna, esta leitura não atribui arbitrariamente os registros a uma única vendedora.",
        "Sem contato e não participamos da proposta são indicadores de cobertura comercial e devem virar fila de ação no CTI, não apenas estatística histórica.",
        "A presença Carrier é classificação observada na ANFIR. Market share oficial só deve ser publicado após reconciliação com vendas/instalações Carrier na mesma competência e território.",
    ]
    for text in required:
        assert text in catalog
        assert catalog[text].get("en")
        assert catalog[text].get("es")
