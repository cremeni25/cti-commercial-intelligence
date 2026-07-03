from collections import defaultdict
from statistics import mean

from core.supabase_client import supabase


class CTIEngine:

    def dashboard_insights(self):

        dados = (
            supabase
            .table("cti_anfir")
            .select("*")
            .execute()
            .data
            or []
        )

        from collections import Counter

        estados = Counter()
        cidades = Counter()
        ddd = Counter()
        implementadores = Counter()
        linhas = Counter()
        segmentos = Counter()

        estados = defaultdict(int)
        implementadoras = set()

        score_operacional = []
        score_comercial = []

        prioridades = defaultdict(int)
        riscos = defaultdict(int)

        valor_total = 0

        for row in dados:

            estado = row.get("estado")

            if estado:
                estados[estado] += 1

            implementador = row.get("implementador")

            if implementador:
                implementadoras.add(implementador)

            so = row.get("score_operacional")

            if so is not None:
                score_operacional.append(float(so))

            sc = row.get("score_comercial")

            if sc is not None:
                score_comercial.append(float(sc))

            prioridade = row.get("prioridade")

            if prioridade:
                prioridades[prioridade] += 1

            risco = row.get("nivel_risco")

            if risco:
                riscos[risco] += 1

            valor_total += float(row.get("valor") or 0)

        return {

            "total_registros": len(dados),

            "implementadoras": len(
                implementadoras
            ),

            "valor_total": valor_total,

            "score_operacional":
                round(
                    mean(score_operacional),
                    2
                ) if score_operacional else 0,

            "score_comercial":
                round(
                    mean(score_comercial),
                    2
                ) if score_comercial else 0,

            "estados": sorted(

                [

                    {
                        "estado": estado,
                        "quantidade": quantidade
                    }

                    for estado,
                    quantidade
                    in estados.items()

                ],

                key=lambda x:
                x["quantidade"],

                reverse=True

            ),

            "prioridades": dict(prioridades),

            "riscos": dict(riscos)

        }
    def analytics_dashboard(self):
        return self.dashboard_insights()


cti_engine = CTIEngine()