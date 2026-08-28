from types import SimpleNamespace

from routers import crm_scope_atividades_router as modulo


class _TabelaUsuariosFake:
    def select(self, _campos):
        return self

    def in_(self, _campo, _ids):
        return self

    def execute(self):
        return SimpleNamespace(
            data=[
                {
                    "id": "4f2bedeb-5637-4cad-87a0-3ad551fc7c55",
                    "nome": "MONICA ALMEIDA",
                    "email": "vendas1sp@refrigeracaoviena.com.br",
                }
            ]
        )


class _SupabaseFake:
    def table(self, nome):
        assert nome == "cti_users"
        return _TabelaUsuariosFake()


def test_agenda_exibe_nome_real_do_responsavel(monkeypatch):
    monkeypatch.setattr(modulo, "supabase", _SupabaseFake())

    itens = modulo._enriquecer_responsaveis(
        [
            {
                "id": "atividade-1",
                "usuario_id": "4f2bedeb-5637-4cad-87a0-3ad551fc7c55",
                "titulo": "Prospecção",
            }
        ]
    )

    assert itens[0]["responsavel_id"] == "4f2bedeb-5637-4cad-87a0-3ad551fc7c55"
    assert itens[0]["responsavel_nome"] == "MONICA ALMEIDA"


def test_agenda_nao_inventa_responsavel_sem_usuario(monkeypatch):
    monkeypatch.setattr(modulo, "supabase", _SupabaseFake())

    itens = modulo._enriquecer_responsaveis([{"id": "atividade-sem-responsavel"}])

    assert "responsavel_nome" not in itens[0]
