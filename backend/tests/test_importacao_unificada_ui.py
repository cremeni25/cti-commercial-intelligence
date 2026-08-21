from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_importacao_unificada_e_unico_ponto_visivel():
    page = (_root() / "frontend/src/app/upload/page.tsx").read_text(encoding="utf-8")
    sidebar = (_root() / "frontend/src/components/ui/Sidebar.tsx").read_text(encoding="utf-8")
    service = (_root() / "frontend/src/services/cti-api.ts").read_text(encoding="utf-8")

    assert "Importar Dados" in page
    assert "importarDados" in page
    assert "Importar Dados" in sidebar
    assert "Upload Operacional" not in sidebar
    assert "SEM_REGISTROS_PROCESSADOS" in service
    assert "/backoffice-fontes/upload" in service
    assert "/upload/anfir/seguro" in service
