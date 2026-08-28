from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from core.supabase_client import supabase
from routers.analytics_router import router as analytics_router
from routers.autorizados_router import router as autorizados_router
from routers.brasil_router import router as brasil_router
from routers.clientes_router import router as clientes_router
from routers.crm_atividades_governanca_router import router as crm_atividades_governanca_router
from routers.crm_router import router as crm_router
from routers.crm_scope_router import router as crm_scope_router
from routers.crm_scope_atividades_router import router as crm_scope_atividades_router
from routers.crm_scope_carrier_router import router as crm_scope_carrier_router
from routers.crm_scope_cliente_referencia_router import router as crm_scope_cliente_referencia_router
from routers.crm_scope_clientes_router import router as crm_scope_clientes_router
from routers.crm_scope_documents_router import public_router as crm_scope_documents_public_router, secure_router as crm_scope_documents_secure_router
from routers.crm_scope_estrategia_router import router as crm_scope_estrategia_router
from routers.crm_scope_implementadoras_router import router as crm_scope_implementadoras_router
from routers.crm_scope_negocio_historico_router import router as crm_scope_negocio_historico_router
from routers.crm_scope_vendas_router import router as crm_scope_vendas_router
from routers.cti_api_router import router as cti_api_router
from routers.drilldown_router import router as drilldown_router
from routers.engine_router import router as engine_router
from routers.modulos_router import router as modulos_router
from routers.negociacoes_router import router as negociacoes_router
from routers.strategic_layers_router import router as strategic_layers_router
from routers.upload_router import router as upload_router
from routers.vendas_router import router as vendas_router


def _cors_origins() -> list[str]:
    configurado = os.getenv("CTI_CORS_ALLOWED_ORIGINS", "").strip()
    if not configurado:
        return ["*"]
    origens = [origem.strip() for origem in configurado.split(",") if origem.strip()]
    return origens or ["*"]


app = FastAPI(title="CTI Comercial Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Governança de atividades vem antes do router CRM legado para que as leituras
# operacionais excluam arquivadas e resolvam corretamente o cliente.
app.include_router(crm_atividades_governanca_router)
app.include_router(crm_router)
app.include_router(crm_scope_router)
app.include_router(crm_scope_atividades_router)
app.include_router(crm_scope_carrier_router)
app.include_router(crm_scope_cliente_referencia_router)
app.include_router(crm_scope_clientes_router)
app.include_router(crm_scope_documents_secure_router)
app.include_router(crm_scope_documents_public_router)
app.include_router(crm_scope_estrategia_router)
app.include_router(crm_scope_implementadoras_router)
app.include_router(crm_scope_vendas_router)
app.include_router(crm_scope_negocio_historico_router)
app.include_router(analytics_router)
app.include_router(engine_router)
app.include_router(negociacoes_router)
app.include_router(clientes_router)
app.include_router(vendas_router)
app.include_router(upload_router)
app.include_router(cti_api_router)
app.include_router(brasil_router)
app.include_router(autorizados_router)
app.include_router(modulos_router)
app.include_router(strategic_layers_router)
app.include_router(drilldown_router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "sistema": "CTI Comercial Intelligence",
        "versao": "3.0",
    }


@app.get("/status")
def status():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _carregar_base_anfir_ativa() -> list[dict]:
    base: list[dict] = []
    pagina = 0
    limite = 1000

    while True:
        response = (
            supabase.table("cti_anfir")
            .select("cliente,estado,valor")
            .eq("ativo", True)
            .range(pagina * limite, ((pagina + 1) * limite) - 1)
            .execute()
        )
        registros = response.data or []
        base.extend(registros)
        if len(registros) < limite:
            break
        pagina += 1

    return base


@app.get("/dashboard/insights")
def insights():
    data = _carregar_base_anfir_ativa()
    if not data:
        return {"status": "sem_dados"}

    clientes = Counter()
    estados = Counter()
    valores: list[float] = []

    for row in data:
        if row.get("cliente"):
            clientes[str(row["cliente"])] += 1
        if row.get("estado"):
            estados[str(row["estado"])] += 1
        if row.get("valor") not in (None, ""):
            try:
                valores.append(float(row["valor"]))
            except (TypeError, ValueError):
                pass

    top_cliente = clientes.most_common(1)
    top_estado = estados.most_common(1)
    ticket = sum(valores) / len(valores) if valores else 0

    return {
        "status": "ok",
        "leitura_estrategica": {
            "cliente_dominante": top_cliente[0][0] if top_cliente else None,
            "regiao_dominante": top_estado[0][0] if top_estado else None,
            "ticket_medio": round(ticket, 2),
            "recomendacoes": [
                "Expandir base de clientes" if len(clientes) < 10 else None,
                "Aumentar presença geográfica" if len(estados) < 5 else None,
                "Explorar grandes contas" if ticket > 10000 else None,
            ],
        },
    }


@app.get("/pipeline/status")
def pipeline_status():
    resposta = (
        supabase.table("cti_anfir")
        .select("id", count="exact")
        .eq("ativo", True)
        .limit(1)
        .execute()
    )
    total = resposta.count or 0
    return {
        "linhas_brutas": total,
        "linhas_processadas": total,
        "pipeline": "ativo",
    }
