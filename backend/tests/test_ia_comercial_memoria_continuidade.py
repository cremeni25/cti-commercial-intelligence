from __future__ import annotations

from types import SimpleNamespace

from routers import ia_comercial_cti_router as router


class _TabelaMensagensFake:
    def __init__(self, linhas):
        self.linhas = linhas
        self.filtros = []
        self.ordem = None
        self.limite = None

    def select(self, _campos):
        return self

    def eq(self, campo, valor):
        self.filtros.append((campo, valor))
        return self

    def order(self, campo, desc=False):
        self.ordem = (campo, desc)
        return self

    def limit(self, limite):
        self.limite = limite
        return self

    def execute(self):
        return SimpleNamespace(data=self.linhas[: self.limite])


class _SupabaseFake:
    def __init__(self, linhas):
        self.tabela = _TabelaMensagensFake(linhas)

    def table(self, nome):
        assert nome == "cti_ia_mensagens"
        return self.tabela


def test_historico_conversacional_isola_conversa_usuario_e_restaura_ordem(monkeypatch):
    # O backend consulta em ordem decrescente para limitar e depois restaura a ordem cronológica.
    linhas_desc = [
        {"papel": "assistant", "conteudo": "Pedido PED-2 está em CARRIER.", "created_at": "2026-08-11T03:00:00Z"},
        {"papel": "user", "conteudo": "Analise o pedido PED-2.", "created_at": "2026-08-11T02:59:00Z"},
    ]
    fake = _SupabaseFake(linhas_desc)
    monkeypatch.setattr(router, "supabase", fake)
    usuario = SimpleNamespace(id="usuario-1")

    historico = router._historico_conversacional("conversa-1", usuario)

    assert historico == [
        {"role": "user", "content": "Analise o pedido PED-2."},
        {"role": "assistant", "content": "Pedido PED-2 está em CARRIER."},
    ]
    assert ("conversa_id", "conversa-1") in fake.tabela.filtros
    assert ("usuario_id", "usuario-1") in fake.tabela.filtros
    assert fake.tabela.ordem == ("created_at", True)
    assert fake.tabela.limite == router._HISTORICO_MAX_MENSAGENS


def test_historico_descarta_papeis_invalidos_e_limita_conteudo(monkeypatch):
    longo = "x" * (router._HISTORICO_MAX_CARACTERES_POR_MENSAGEM + 100)
    fake = _SupabaseFake(
        [
            {"papel": "system", "conteudo": "não deve entrar", "created_at": "3"},
            {"papel": "assistant", "conteudo": longo, "created_at": "2"},
            {"papel": "user", "conteudo": "   ", "created_at": "1"},
        ]
    )
    monkeypatch.setattr(router, "supabase", fake)
    usuario = SimpleNamespace(id="usuario-1")

    historico = router._historico_conversacional("conversa-1", usuario)

    assert len(historico) == 1
    assert historico[0]["role"] == "assistant"
    assert len(historico[0]["content"]) == router._HISTORICO_MAX_CARACTERES_POR_MENSAGEM


def test_contexto_ia005_memoria_resolve_referencia_mas_nao_substitui_evidencia():
    mensagem, _ = router._mensagem_com_contexto_temporal("E qual é a próxima etapa dele?")

    assert "histórico da conversa pode ser usado para compreender continuidade" in mensagem
    assert "nunca conta como evidência factual da execução atual" in mensagem
    assert "reconsulte a ferramenta adequada antes de responder" in mensagem
    assert "Não reutilize silenciosamente números, status, vendas" in mensagem
