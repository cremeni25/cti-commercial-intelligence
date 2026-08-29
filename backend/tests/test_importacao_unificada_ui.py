from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_importacao_unificada_e_unico_ponto_visivel():
    page = (_root() / "frontend/src/app/upload/page.tsx").read_text(encoding="utf-8")
    sidebar = (_root() / "frontend/src/components/ui/Sidebar.tsx").read_text(encoding="utf-8")
    catalog = (_root() / "frontend/src/core/i18n/catalog.ts").read_text(encoding="utf-8")
    service = (_root() / "frontend/src/services/cti-api.ts").read_text(encoding="utf-8")
    backoffice = (_root() / "frontend/src/app/backoffice-fontes/page.tsx").read_text(encoding="utf-8")

    assert "Importar Dados" in page
    assert "importarDados" in page
    assert 'labelKey: "nav.import"' in sidebar
    assert '"nav.import": "Importar Dados"' in catalog
    assert "Upload Operacional" not in sidebar
    assert "SEM_REGISTROS_PROCESSADOS" in service
    assert 'BACKOFFICE_URL = "/api/crm-proxy/backoffice-fontes"' in service
    assert "`${BACKOFFICE_URL}/upload`" in service
    assert "/upload/anfir/seguro" in service
    assert "Receber nova fonte" not in backoffice
    assert "As novas fontes entram exclusivamente por Importar Dados" in backoffice


def test_selecao_de_arquivo_inicia_importacao_sem_segundo_toque():
    page = (_root() / "frontend/src/app/upload/page.tsx").read_text(encoding="utf-8")

    assert "void enviarArquivo(arquivo)" in page
    assert "Arquivo selecionado. Iniciando importação..." in page
    assert "Importar novamente" in page
    assert "Arquivo selecionado. Pronto para importar." not in page
