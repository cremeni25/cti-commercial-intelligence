from core import ingestion_promotion as mod


def test_pedido_exige_cadeia_relacional_explicitamente():
    try:
        mod.promover_pedido({"numero": "PED-1"})
    except ValueError as exc:
        texto = str(exc)
        assert "cliente_id" in texto
        assert "oportunidade_id" in texto
        assert "proposta_id" in texto
        assert "responsavel_id" in texto
    else:
        raise AssertionError("Pedido sem vínculos canônicos deveria ser bloqueado")


def test_promocao_pedido_valida_cadeia_e_insere_sem_criar_relacoes(monkeypatch):
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
                return Resposta([{"id": "ped-1", **self.payload}])
            if self.tabela == "clientes":
                return Resposta([{"id": "cli-1", "nome": "Cliente"}])
            if self.tabela == "cti_oportunidades":
                return Resposta([{"id": "opp-1", "cliente_id": "cli-1", "responsavel_id": "usr-1"}])
            if self.tabela == "cti_propostas":
                return Resposta([{"id": "prop-1", "cliente_id": "cli-1", "oportunidade_id": "opp-1", "responsavel_id": "usr-1"}])
            if self.tabela == "cti_users":
                return Resposta([{"id": "usr-1", "nome": "Responsável"}])
            if self.tabela == "cti_pedidos":
                return Resposta([])
            return Resposta([])

    class SB:
        def table(self, tabela): return Query(tabela)

    monkeypatch.setattr(mod, "supabase", SB())

    resultado = mod.promover_pedido({
        "numero": "PED-2026-001",
        "cliente_id": "cli-1",
        "oportunidade_id": "opp-1",
        "proposta_id": "prop-1",
        "responsavel_id": "usr-1",
        "valor": 25000,
    })

    assert resultado["acao"] == "INSERIDO"
    tabela, payload = inseridos[-1]
    assert tabela == "cti_pedidos"
    assert payload["cliente_id"] == "cli-1"
    assert payload["oportunidade_id"] == "opp-1"
    assert payload["proposta_id"] == "prop-1"
    assert payload["responsavel_id"] == "usr-1"
    assert payload["status"] == "ABERTO"
    assert payload["origem_comercial"] == "BACKOFFICE_FONTES"


def test_pedido_bloqueia_proposta_de_outro_cliente(monkeypatch):
    class Resposta:
        def __init__(self, data): self.data = data

    class Query:
        def __init__(self, tabela): self.tabela = tabela
        def select(self, *_): return self
        def eq(self, *_): return self
        def limit(self, *_): return self
        def execute(self):
            if self.tabela == "clientes":
                return Resposta([{"id": "cli-1"}])
            if self.tabela == "cti_oportunidades":
                return Resposta([{"id": "opp-1", "cliente_id": "cli-1"}])
            if self.tabela == "cti_propostas":
                return Resposta([{"id": "prop-1", "cliente_id": "cli-2", "oportunidade_id": "opp-1"}])
            return Resposta([])

    class SB:
        def table(self, tabela): return Query(tabela)

    monkeypatch.setattr(mod, "supabase", SB())

    try:
        mod.promover_pedido({
            "numero": "PED-2026-002",
            "cliente_id": "cli-1",
            "oportunidade_id": "opp-1",
            "proposta_id": "prop-1",
            "responsavel_id": "usr-1",
            "valor": 1000,
        })
    except ValueError as exc:
        assert "Proposta não pertence ao cliente" in str(exc)
    else:
        raise AssertionError("Proposta de outro cliente deveria bloquear a promoção")
