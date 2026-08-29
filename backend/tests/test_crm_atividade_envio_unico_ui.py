from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "app" / "crm-app" / "atividades" / "nova" / "page.tsx"


def test_nova_atividade_bloqueia_multiplos_envios_imediatos():
    page = PAGE.read_text(encoding="utf-8")
    compacto = "".join(page.split())
    assert "useRef" in page
    assert "envioEmCursoRef.current" in page
    assert "if(envioEmCursoRef.current)return" in compacto
    assert 'window.location.href="/crm-app/atividades"' in compacto
