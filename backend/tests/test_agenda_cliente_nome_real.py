from pathlib import Path
from types import SimpleNamespace

from routers import crm_scope_atividades_router as modulo


class _ConsultaFake:
    def __init__(self, tabela: str):
        self.tabela = tabela
        self.campo = ""
        self.valores: list[str] = []

    def select(self, _campos):
        return self

    def in_(self, campo, valores):
        self.campo = campo
        self.valores = list(valores)
        return self

    def execute(self):
        if self.tabela == "clientes" and self.campo == "id" and "cliente-123" in self.valores:
            return SimpleNamespace(data=[{"id": "cliente-123", "nome": "Transportadora Exemplo Ltda"}])
        if self.tabela == "clientes" and self.campo == "nome" and "Cliente Legado Ltda" in self.valores:
            return SimpleNamespace(data=[{"id": "cliente-456", "nome": "Cliente Legado Ltda"}])
        return SimpleNamespace(data=[])


class _SupabaseFake:
    def table(self, nome):
        return _ConsultaFake(nome)


def test_agenda_enriquece_cliente_por_id(monkeypatch):
    monkeypatch.setattr(modulo, "supabase", _SupabaseFake())

    itens = modulo._enriquecer_clientes([{"id": "atividade-1", "cliente_id": "cliente-123"}])

    assert itens[0]["cliente_nome"] == "Transportadora Exemplo Ltda"


def test_agenda_recupera_registro_legado_com_nome_em_cliente_id(monkeypatch):
    monkeypatch.setattr(modulo, "supabase", _SupabaseFake())

    itens = modulo._enriquecer_clientes([{"id": "atividade-2", "cliente_id": "Cliente Legado Ltda"}])

    assert itens[0]["cliente_nome"] == "Cliente Legado Ltda"


def test_frontend_nao_exibe_fallback_generico_cliente_vinculado():
    root = Path(__file__).resolve().parents[2]
    codigo = (root / "frontend" / "src" / "app" / "atividades" / "page.tsx").read_text(encoding="utf-8")

    assert '"Cliente vinculado"' not in codigo
    assert "clienteSelecionado?.id || clienteInformado" in codigo
    assert "cliente.nome === item.cliente_id" in codigo
