from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "frontend" / "src" / "app" / "crm-app" / "acao" / "registrar" / "page.tsx"


def test_registro_unico_bloqueia_multiplos_envios_imediatos():
    page = PAGE.read_text(encoding="utf-8")
    compacto = "".join(page.split())
    assert "useRef" in page
    assert "envioRef.current" in page
    assert "if(envioRef.current||!cliente||!usuario?.id)return" in compacto
    assert "envioRef.current=true" in compacto
    assert "window.location.href=`/crm-app/acao/concluida?${qs.toString()}`" in compacto
