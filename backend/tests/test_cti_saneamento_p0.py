from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_sintese_crm_nao_depende_de_modulo_legacy():
    texto = (ROOT / "backend/services/ia_comercial_sintese_crm.py").read_text(encoding="utf-8")
    assert "ia_comercial_sintese_crm_legacy" not in texto
    assert not (ROOT / "backend/services/ia_comercial_sintese_crm_legacy.py").exists()

def test_persistencia_anfir_usa_implementadora_canonica():
    texto = (ROOT / "backend/repositories/cti_repository.py").read_text(encoding="utf-8")
    assert '"implementadora"' in texto
    assert 'payload["implementador"]' not in texto
    assert 'payload.pop("implementador")' not in texto

def test_router_upload_delega_persistencia_ao_engine():
    texto = (ROOT / "backend/routers/upload_router.py").read_text(encoding="utf-8")
    assert "upload_engine.persistir_idempotente" in texto
    assert "resultado_base = repository.persistir_registros_idempotente" not in texto

def test_ia_exige_dominio_frigorifico_e_code_interpreter():
    texto = (ROOT / "backend/services/ia_comercial_agente.py").read_text(encoding="utf-8")
    assert "DOMÍNIO FRIGORÍFICO EXCLUSIVO" in texto
    assert '"type": "code_interpreter"' in texto
