# engine/win_loss_engine.py

class WinLossEngine:

    def __init__(self, anfir_data, negociacoes_data):

        self.anfir = anfir_data or []
        self.negociacoes = negociacoes_data or []

    # -----------------------------------------
    # RESUMO GERAL
    # -----------------------------------------

    def resumo(self):

        total_anfir = len(self.anfir)
        total_negociacoes = len(self.negociacoes)

        ganhos = 0
        perdas = 0

        clientes_anfir = set([
            (r.get("cliente_resolvido") or r.get("cliente") or "").upper()
            for r in self.anfir
        ])

        for n in self.negociacoes:

            cliente = (n.get("cliente") or "").upper()

            if cliente in clientes_anfir:
                ganhos += 1
            else:
                perdas += 1

        taxa = 0

        if total_negociacoes > 0:
            taxa = round((ganhos / total_negociacoes) * 100, 2)

        return {
            "total_anfir": total_anfir,
            "total_negociacoes": total_negociacoes,
            "ganhos": ganhos,
            "perdas": perdas,
            "taxa_conversao": taxa
        }

    # -----------------------------------------
    # CRUZAMENTO DETALHADO
    # -----------------------------------------

    def cruzar(self):

        resultado = []

        clientes_anfir = set([
            (r.get("cliente_resolvido") or r.get("cliente") or "").upper()
            for r in self.anfir
        ])

        for n in self.negociacoes:

            cliente = (n.get("cliente") or "").upper()

            status = "GANHO" if cliente in clientes_anfir else "PERDIDO"

            resultado.append({

                "cliente": cliente,
                "estado": n.get("estado"),
                "produto": n.get("produto"),
                "valor": n.get("valor"),
                "status": status

            })

        return resultado
