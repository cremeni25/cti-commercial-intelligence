"""Registro de módulos: rotas declaradas existem e o roadmap fica visível."""
from pathlib import Path

import pytest

from core.modulos_plataforma import MODULOS, ModuloPlataforma, modulos_para_usuario

APP_DIR = Path(__file__).resolve().parents[2] / "frontend" / "src" / "app"


def _pagina_existe(rota: str) -> bool:
    return (APP_DIR / rota.strip("/") / "page.tsx").is_file()


@pytest.mark.parametrize("modulo", [m for m in MODULOS if m.status != "planejado"], ids=lambda m: m.codigo)
def test_rotas_declaradas_existem_no_frontend(modulo):
    for rota in (modulo.rota_web, modulo.rota_app):
        if rota:
            assert _pagina_existe(rota), f"{modulo.codigo}: rota {rota} não existe em frontend/src/app"


def test_codigos_unicos_e_planejados_sem_rota():
    codigos = [m.codigo for m in MODULOS]
    assert len(codigos) == len(set(codigos))
    for modulo in MODULOS:
        if modulo.status == "planejado":
            assert modulo.rota_web is None and modulo.rota_app is None


def test_gestao_ve_tudo_e_perfil_sem_permissao_ve_somente_roadmap():
    assert len(modulos_para_usuario("ADMIN_MASTER", {})) == len(MODULOS)
    sem_permissao = modulos_para_usuario("REPRES_REGIAO_01", {})
    assert {m["status"] for m in sem_permissao} == {"planejado"}


def test_status_invalido_e_rejeitado():
    with pytest.raises(ValueError):
        ModuloPlataforma("x", "X", "", "operacao", "experimental")
