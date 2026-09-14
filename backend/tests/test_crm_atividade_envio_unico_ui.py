from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FORM = ROOT / "frontend" / "src" / "components" / "crm" / "InteracaoComercialForm.tsx"
APP_PAGE = ROOT / "frontend" / "src" / "app" / "crm-app" / "acao" / "registrar" / "page.tsx"
WEB_PAGE = ROOT / "frontend" / "src" / "app" / "atividades" / "interacao" / "page.tsx"


def test_registro_unico_bloqueia_multiplos_envios_imediatos():
    form = FORM.read_text(encoding="utf-8")
    compacto = "".join(form.split())
    assert "useRef" in form
    assert "envioRef.current" in form
    assert "if(envioRef.current||!usuario?.id)return" in compacto
    assert "envioRef.current=true" in compacto


def test_app_e_web_usam_o_mesmo_fluxo_de_interacao():
    app = APP_PAGE.read_text(encoding="utf-8")
    web = WEB_PAGE.read_text(encoding="utf-8")
    assert '<InteracaoComercialForm superficie="app" />' in app
    assert '<InteracaoComercialForm superficie="web"/>' in "".join(web.split())
