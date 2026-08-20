from core import ingestion_promotion as mod


def test_suporte_inclui_oportunidade_relacional():
    suporte = mod.suporte_promocao("CRM_COMERCIAL", "OPORTUNIDADE")
    assert suporte["suportado"] is True


def test_oportunidade_exige_cliente_e_responsavel_explicitos():
    try:
        mod.promover_oportunidade({"titulo": "Troca de equipamento"})
    except ValueError as exc:
        assert "cliente_id" in str(exc)
    else:
        raise AssertionError("Oportunidade sem cliente deveria ser bloqueada")

    try:
        mod.promover_oportunidade({"cliente_id": "cli-1", "titulo": "Troca de equipamento"})
    except ValueError as exc:
        assert "responsavel_id" in str(exc)
    else:
        raise AssertionError("Oportunidade sem responsável deveria ser bloqueada")


def test_promocao_oportunidade_valida_relacoes_e_normaliza_probabilidade(monkeypatch):
    inseridos = []

    class Resposta:
        def __init__(self, data):
            self.data = data

    class Query:
        def __init__(self, tabela):
            self.tabela = tabela
            self.filtros = []
            self.payload = None

        def select(self, *_): return self
        def eq(self, campo, valor):
            self.filtros.append((campo, valor))
            return self
        def limit(self, *_): return self
        def insert(self, payload):
            self.payload = payload
            inseridos.append((self.tabela, payload))
            return self
        def execute(self):
            if self.payload is not None:
                return Resposta([{"id": "opp-1", **self.payload}])
            if self.tabela == "clientes":
                return Resposta([{"id": "cli-1", "nome": "Cliente"}])
            if self.tabela == "cti_users":
                return Resposta([{"id": "usr-1", "nome": "Responsável"}])
            if self.tabela == "cti_oportunidades":
                return Resposta([])
            return Resposta([])

    class SB:
        def table(self, tabela): return Query(tabela)

    monkeypatch.setattr(mod, "supabase", SB())

    resultado = mod.promover_oportunidade({
        "cliente_id": "cli-1",
        "responsavel_id": "usr-1",
        "titulo": "Troca de equipamento",
        "valor_estimado": 1000,
        "probabilidade": 50,
    })

    assert resultado["acao"] == "INSERIDO"
    tabela, payload = inseridos[-1]
    assert tabela == "cti_oportunidades"
    assert payload["cliente_id"] == "cli-1"
    assert payload["responsavel_id"] == "usr-1"
    assert payload["probabilidade"] == 0.5
    assert payload["status"] == "OPORTUNIDADE"


def test_oportunidade_bloqueia_cliente_inexistente(monkeypatch):
    class Resposta:
        data = []
    class Query:
        def select(self, *_): return self
        def eq(self, *_): return self
        def limit(self, *_): return self
        def execute(self): return Resposta()
    class SB:
        def table(self, *_): return Query()
    monkeypatch.setattr(mod, "supabase", SB())

    try:
        mod.promover_oportunidade({
            "cliente_id": "cli-inexistente",
            "responsavel_id": "usr-1",
            "titulo": "Troca de equipamento",
        })
    except ValueError as exc:
        assert "Cliente relacionado" in str(exc)
    else:
        raise AssertionError("Relacionamento inexistente deveria ser bloqueado")
