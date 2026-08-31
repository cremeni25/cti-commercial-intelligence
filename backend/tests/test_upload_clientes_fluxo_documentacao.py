from pathlib import Path


def test_upload_clientes_preserva_fluxo_seguro_no_frontend():
    raiz = Path(__file__).resolve().parents[2]
    service = (raiz / "frontend/src/services/cti-api.ts").read_text(encoding="utf-8")
    page = (raiz / "frontend/src/app/upload/page.tsx").read_text(encoding="utf-8")

    assert "CLIENTES_PROMOVIDOS_COM_SEGURANCA" in service
    assert "PROMOCAO_BLOQUEADA_DIVERGENCIA" in service
    assert "CRM_CADASTRAL" in service
    assert "/reconciliacao/preparar" in service
    assert "/reconciliacao/aprovar" in service
    assert "/reconciliacao/promover?natureza=CRM_CADASTRAL" in service
    assert "Listas cadastrais são reconciliadas por CNPJ" in page
    assert "divergências não sobrescrevem o cadastro existente" in page
