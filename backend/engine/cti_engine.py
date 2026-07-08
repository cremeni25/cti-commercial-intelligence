from collections import defaultdict
from statistics import mean

from core.cti_taxonomy import normalizar_implementadora
from repositories.cti_repository import repository


class CTIEngine:

    def dashboard_insights(self):

        estados = defaultdict(int)
        implementadoras = set()

        score_operacional = []
        score_comercial = []

        prioridades = defaultdict(int)
        riscos = defaultdict(int)

        valor_total = 0

        dados = repository.buscar_cti_anfir()

        for row in dados:

            estado = row.get("estado")

            if estado:
                estados[estado] += 1

            implementadora = normalizar_implementadora(
                row.get("implementador")
            )

            if implementadora:
                implementadoras.add(implementadora)

            so = row.get("score_operacional")

            if so is not None:
                try:
                    score_operacional.append(float(so))
                except (TypeError, ValueError):
                    pass

            sc = row.get("score_comercial")

            if sc is not None:
                try:
                    score_comercial.append(float(sc))
                except (TypeError, ValueError):
                    pass

            prioridade = row.get("prioridade")

            if prioridade:
                prioridades[prioridade] += 1

            risco = row.get("nivel_risco")

            if risco:
                riscos[risco] += 1

            try:
                valor_total += float(row.get("valor") or 0)
            except (TypeError, ValueError):
                pass

        return {

            "kpis": {
                "total_registros": len(dados),
                "implementadoras": len(implementadoras),
                "estados": len(estados),
                "valor_total": valor_total,
                "score_operacional": (
                    round(mean(score_operacional), 2)
                    if score_operacional
                    else None
                ),
                "score_comercial": (
                    round(mean(score_comercial), 2)
                    if score_comercial
                    else None
                ),
            },

            "territorial": {
                "estados": sorted(
                    [
                        {
                            "estado": estado,
                            "quantidade": quantidade,
                        }
                        for estado, quantidade in estados.items()
                    ],
                    key=lambda x: x["quantidade"],
                    reverse=True,
                )
            },

            "timeline": {
                "status": "indisponivel"
            },

            "insights": {
                "status": "indisponivel"
            },

            "prioridades": dict(prioridades),

            "debug": {
                "implementadoras": sorted(
                    list(implementadoras)
                )
            },

            "riscos": dict(riscos),
        }

    def analytics_dashboard(self):
        return self.dashboard_insights()


cti_engine = CTIEngine()