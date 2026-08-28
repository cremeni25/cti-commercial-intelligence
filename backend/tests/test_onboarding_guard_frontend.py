from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTH_CONTEXT = ROOT / "frontend" / "src" / "core" / "auth" / "AuthContext.tsx"
AUTH_SERVICE = ROOT / "frontend" / "src" / "core" / "auth" / "auth.service.ts"
ROUTE_ACCESS = ROOT / "frontend" / "src" / "core" / "rbac" / "route-access.ts"


def test_primeiro_acesso_e_rota_autenticada_permitida():
    codigo = ROUTE_ACCESS.read_text(encoding="utf-8")
    assert 'if (pathname === "/primeiro-acesso") return true' in codigo


def test_flags_de_onboarding_sao_carregadas_na_sessao():
    codigo = AUTH_SERVICE.read_text(encoding="utf-8")
    assert "primeiro_acesso_pendente: perfil.primeiro_acesso_pendente === true" in codigo
    assert "cadastro_completo: perfil.cadastro_completo !== false" in codigo


def test_guard_forca_onboarding_sem_bloquear_canal():
    codigo = AUTH_CONTEXT.read_text(encoding="utf-8")
    assert 'router.replace("/primeiro-acesso")' in codigo
    assert "primeiroAcessoPendente" in codigo
    assert "rotaPrimeiroAcesso ||" in codigo
