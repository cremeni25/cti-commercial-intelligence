from types import SimpleNamespace

from routers import crm_scope_clientes_router as clientes


def base_isolada(monkeypatch):
    rows = [{"id": f"{i:05}", "responsavel_comercial_id": "r1" if i < 1400 else "r2"} for i in range(1503)]
    chamadas = {"clientes": 0, "cti_users": 0}

    class Consulta:
        def __init__(self, tabela):
            self.tabela = tabela
            self.rows = rows if tabela == "clientes" else [{"id": "r1", "nome": "Regional 1"}, {"id": "r2", "nome": "Regional 2"}]
        def select(self, *_): return self
        def order(self, *_): return self
        def range(self, inicio, fim):
            # Simula limite de resposta menor que o tamanho solicitado.
            self.rows = self.rows[inicio:min(fim + 1, inicio + 137)]
            return self
        def in_(self, chave, valores):
            self.rows = [r for r in self.rows if r[chave] in valores]
            return self
        def execute(self):
            chamadas[self.tabela] += 1
            return SimpleNamespace(data=self.rows)

    monkeypatch.setattr(clientes, "supabase", SimpleNamespace(table=Consulta))
    return rows, chamadas


def test_carteira_completa_ultrapassa_limite_de_pagina_sem_n_mais_um(monkeypatch):
    rows, chamadas = base_isolada(monkeypatch)
    master = SimpleNamespace(id="master", tipo_usuario="ADMIN_MASTER", permissoes={})
    resposta = clientes.listar_clientes_seguro(None, False, master)
    assert len(resposta) == len(rows)
    assert len({r["id"] for r in resposta}) == len(rows)
    assert resposta[-1]["responsavel_comercial_nome"] == "Regional 2"
    assert chamadas["cti_users"] == 1
    assert chamadas["clientes"] == 12


def test_filtro_encontra_responsavel_apos_a_primeira_pagina(monkeypatch):
    base_isolada(monkeypatch)
    regional = SimpleNamespace(id="r2", tipo_usuario="REPRES_REGIAO_02", permissoes={"clientes_visualizar": True})
    resposta = clientes.listar_clientes_seguro(None, False, regional)
    assert len(resposta) == 103
    assert all(r["responsavel_comercial_id"] == "r2" for r in resposta)
