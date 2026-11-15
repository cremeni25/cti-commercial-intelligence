"""Supabase em memória (tabelas como listas de dicts) para testar serviços sem rede."""
from types import SimpleNamespace


class _Consulta:
    def __init__(self, banco, tabela):
        self.banco, self.tabela = banco, tabela
        self.filtros, self.acao, self.dados, self.intervalo = [], "select", None, None

    def select(self, *_):
        self.acao = "select"
        return self

    def update(self, dados):
        self.acao, self.dados = "update", dados
        return self

    def insert(self, dados):
        self.acao, self.dados = "insert", dados
        return self

    def eq(self, campo, valor):
        self.filtros.append(lambda r: str(r.get(campo)) == str(valor))
        return self

    def in_(self, campo, valores):
        alvo = {str(v) for v in valores}
        self.filtros.append(lambda r: str(r.get(campo)) in alvo)
        return self

    def is_(self, campo, valor):
        self.filtros.append(lambda r: r.get(campo) is None)
        return self

    def limit(self, quantidade):
        self.intervalo = (0, quantidade - 1)
        return self

    def single(self):
        self.unico = True
        return self

    def range(self, inicio, fim):
        self.intervalo = (inicio, fim)
        return self

    def execute(self):
        linhas = self.banco.setdefault(self.tabela, [])
        if self.acao == "insert":
            novos = self.dados if isinstance(self.dados, list) else [self.dados]
            linhas.extend(dict(n) for n in novos)
            return SimpleNamespace(data=novos)
        alvo = [r for r in linhas if all(f(r) for f in self.filtros)]
        if self.acao == "update":
            for r in alvo:
                r.update(self.dados)
                for gatilho in self.banco.get("_ao_atualizar", {}).get(self.tabela, []):
                    gatilho(self.banco, r, self.dados)
            return SimpleNamespace(data=alvo)
        if self.intervalo:
            alvo = alvo[self.intervalo[0]:self.intervalo[1] + 1]
        if getattr(self, "unico", False):
            return SimpleNamespace(data=dict(alvo[0]) if alvo else None)
        return SimpleNamespace(data=[dict(r) for r in alvo])


def criar(banco):
    return SimpleNamespace(table=lambda nome: _Consulta(banco, nome))
