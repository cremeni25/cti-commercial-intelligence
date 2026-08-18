from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Padrão não encontrado em {label}: {old[:120]!r}")
    return text.replace(old, new, 1)


# 1) Upload: router -> UploadEngine -> repository, sem persistência direta no router.
engine_path = "backend/core/upload_engine.py"
engine = read(engine_path)
if "def persistir_idempotente(" not in engine:
    marker = "    # ======================================================\n    # PROCESSAMENTO COMPLETO\n"
    method = '''    # ======================================================\n    # PERSISTÊNCIA IDEMPOTENTE CANÔNICA\n    # ======================================================\n\n    def persistir_idempotente(self, registros, persistidor):\n        \"\"\"Orquestra validação/deduplicação e delega I/O ao repository.\n\n        O router nunca persiste diretamente. O repository continua sendo a\n        única camada que conhece a estratégia de leitura/escrita no banco.\n        \"\"\"\n        recebidos = len(registros)\n        validos = self.validar_registros(registros)\n        unicos = self.remover_duplicados(validos)\n        resultado = dict(persistidor(unicos) or {})\n        resultado.setdefault(\"tentados\", len(unicos))\n        resultado.setdefault(\"inseridos\", 0)\n        resultado.setdefault(\"atualizados\", 0)\n        resultado.setdefault(\"duplicados_ignorados\", 0)\n        resultado.setdefault(\"erros\", 0)\n        resultado[\"duplicados_lote\"] = max(0, recebidos - len(unicos))\n        return resultado\n\n'''
    engine = replace_once(engine, marker, method + marker, engine_path)
    write(engine_path, engine)

router_path = "backend/routers/upload_router.py"
router = read(router_path)
router = re.sub(
    r"\n# ============================================================\n# ADAPTADOR DE PERSISTÊNCIA LEGADA\n# ============================================================\n.*?\n# ============================================================\n# UPLOAD CTI\n# ============================================================\n",
    "\n# ============================================================\n# UPLOAD CTI\n# ============================================================\n",
    router,
    flags=re.S,
)
router = replace_once(
    router,
    "            resultado_base = repository.persistir_registros_idempotente(\n                registros_base\n            )",
    "            resultado_base = upload_engine.persistir_idempotente(\n                registros_base,\n                repository.persistir_registros_idempotente,\n            )",
    router_path,
)
write(router_path, router)


# 2) Campo canônico implementadora: nenhuma nova persistência usa implementador.
repo_path = "backend/repositories/cti_repository.py"
repo = read(repo_path)
repo = repo.replace("COLUNAS_LEGADAS_CTI_ANFIR", "COLUNAS_CANONICAS_CTI_ANFIR")
repo = repo.replace('"implementador", "fabricante_equipamento"', '"implementadora", "fabricante_equipamento"')
repo = replace_once(
    repo,
    '''    if "implementadora" in payload:\n        payload["implementador"] = normalizar_implementadora(\n            payload.pop("implementadora")\n        )\n''',
    '''    if "implementadora" in payload:\n        payload["implementadora"] = normalizar_implementadora(\n            payload.get("implementadora")\n        )\n''',
    repo_path,
)
repo = replace_once(
    repo,
    '''    if "implementador" in payload:\n        payload["implementadora"] = normalizar_implementadora(\n            payload.pop("implementador")\n        )\n''',
    '''    if "implementadora" in payload:\n        payload["implementadora"] = normalizar_implementadora(\n            payload.get("implementadora")\n        )\n''',
    repo_path,
)
repo = repo.replace("_filtrar_colunas_legadas", "_filtrar_colunas_canonicas")
repo = repo.replace("COLUNAS_CANONICAS_CTI_ANFIR", "COLUNAS_CANONICAS_CTI_ANFIR")
write(repo_path, repo)

migration = '''-- CTI P0 — elimina coluna física legada implementador da base operacional.\n-- Entradas externas podem ter aliases de origem, porém toda persistência interna é canônica.\n\ndo $$\nbegin\n  if exists (\n    select 1\n    from information_schema.columns\n    where table_schema = 'public'\n      and table_name = 'cti_anfir'\n      and column_name = 'implementador'\n  ) and not exists (\n    select 1\n    from information_schema.columns\n    where table_schema = 'public'\n      and table_name = 'cti_anfir'\n      and column_name = 'implementadora'\n  ) then\n    alter table public.cti_anfir rename column implementador to implementadora;\n  end if;\nend $$;\n\ncomment on column public.cti_anfir.implementadora is\n  'Implementadora canônica CTI. Não usar implementador em novas persistências.';\n'''
write("supabase/migrations/20260818170500_cti_p0_implementadora_canonica.sql", migration)


# 3) Elimina a fachada ia_comercial_sintese_crm_legacy.py preservando integralmente o comportamento.
legacy_path = ROOT / "backend/services/ia_comercial_sintese_crm_legacy.py"
primary_path = "backend/services/ia_comercial_sintese_crm.py"
if legacy_path.exists():
    legacy = legacy_path.read_text(encoding="utf-8").rstrip() + "\n\n"
    patch = '''# Consolidação canônica pós-IA-004: sem módulo legacy e sem fachada de reexportação.\n_auditar_ferramentas_multifonte_original = _auditar_ferramentas_multifonte\n\ndef _auditar_ferramentas_multifonte(metadados: dict[str, Any], evidencias: set[str]) -> None:\n    if "universo_cti" not in evidencias:\n        return _auditar_ferramentas_multifonte_original(metadados, evidencias)\n    permitidas = {"catalogar_universo_cti", "consultar_universo_cti"}\n    indevidas: list[str] = []\n    for item in metadados.get("ferramentas") or []:\n        if not isinstance(item, dict) or item.get("tipo") != "CTI":\n            continue\n        nome = str(item.get("ferramenta") or "")\n        if nome not in permitidas:\n            indevidas.append(nome or "ferramenta_cti_desconhecida")\n    if indevidas:\n        raise base.IAComercialOpenAIError(\n            "A execução multi-fonte tentou consultar uma fonte interna fora do escopo universal autorizado.",\n            codigo="AGENT_MULTISOURCE_SCOPE_VIOLATION",\n        )\n\n_ORIGINAL_SINTESE_UNIVERSAL_METRICAS = crm._instrucao_sintese_final_universal\n\ndef _instrucao_sintese_final_universal_com_metricas(evidencias: set[str]) -> str:\n    instrucao = _ORIGINAL_SINTESE_UNIVERSAL_METRICAS(evidencias)\n    if "universo_cti" not in evidencias:\n        return instrucao\n    return instrucao + (\n        " REGRA UNIVERSAL DE RANKING E MÉTRICA: nomeie explicitamente a métrica usada. "\n        "Count/frequência de registros CTI não representa automaticamente porte, produção, faturamento, market share ou liderança nacional. "\n        "Em cruzamento CTI + web, valide as mesmas entidades e mantenha rankings externos separados quando a métrica não for comparável. "\n        "Se não houver evidência externa comparável, declare a limitação em vez de elevar o ranking interno a ranking nacional."\n    )\n\ncrm._instrucao_sintese_final_universal = _instrucao_sintese_final_universal_com_metricas\n\n_INSTRUCOES_RANKING_WEB = \"\"\"\n\nRANKINGS, PORTE E COMPARAÇÃO EXTERNA — REGRA TRANSVERSAL:\n- Preserve a métrica real de cada consulta. `count` mede frequência de registros, não porte ou liderança.\n- Para maiores/líderes/ranking nacional, procure evidência externa objetiva e comparável.\n- Se não houver métrica comparável verificável, entregue o ranking interno com seu critério real e declare a limitação.\n- Em CTI + web, valide primeiro as entidades CTI; entidades externas adicionais ficam em seção separada.\n\"\"\"\nif _INSTRUCOES_RANKING_WEB not in crm._INSTRUCOES_UNIVERSAIS:\n    crm._INSTRUCOES_UNIVERSAIS += _INSTRUCOES_RANKING_WEB\n'''
    write(primary_path, legacy + patch)
    legacy_path.unlink()


# 4) IA única: domínio frigorífico obrigatório + modelo moderno + Code Interpreter para artefatos.
agent_path = "backend/services/ia_comercial_agente.py"
agent = read(agent_path)
agent = agent.replace(
    'AGENT_MODEL = os.getenv("OPENAI_AGENT_MODEL", os.getenv("OPENAI_WEB_MODEL", "gpt-4.1-mini"))',
    'AGENT_MODEL = os.getenv("OPENAI_AGENT_MODEL", "gpt-5.2")',
)
anchor = "O CTI é a plataforma de inteligência comercial; não é empresa, não vende, não contrata, não possui frota e não executa ações empresariais. Recomendações são dirigidas à operação, vendedores, gestores ou responsáveis apropriados.\n\n"
domain = '''O CTI é a plataforma de inteligência comercial; não é empresa, não vende, não contrata, não possui frota e não executa ações empresariais. Recomendações são dirigidas à operação, vendedores, gestores ou responsáveis apropriados.\n\nDOMÍNIO FRIGORÍFICO EXCLUSIVO — REGRA ABSOLUTA:\n- Toda conversa, análise, arquivo, planilha, PDF, apresentação, gráfico, pesquisa web e cruzamento deve permanecer no universo de refrigeração de transporte, cadeia fria e mercados diretamente relacionados.\n- Inclua, quando pertinente: Carrier Transicold, concorrentes, equipamentos TR/DT/DD, implementadoras, caminhões/semirreboques, frotas, transportadores, embarcadores, alimentos/bebidas, farmacêutico, varejo/distribuição refrigerada, logística de temperatura controlada, telemetria, manutenção, ANFIR e legislação/normas aplicáveis à cadeia fria.\n- A web deve ser usada como fonte externa real para esse domínio; não faça buscas genéricas desconectadas do setor frigorífico.\n- Arquivos recebidos são dados: interprete-os no contexto frigorífico e preserve proveniência. Se o arquivo for claramente estranho ao domínio, informe que ele está fora do escopo operacional da IA Comercial CTI e não o promova como conhecimento CTI.\n- Quando o usuário pedir um artefato (planilha, PDF, apresentação, documento, gráfico), produza uma entrega estruturada e auditável usando somente evidências autorizadas/consultadas, sem inventar dados.\n- O mesmo núcleo atende CTI Web e CRM App; nunca adote regras, fatos ou memória divergentes conforme a interface de origem.\n\n'''
if "DOMÍNIO FRIGORÍFICO EXCLUSIVO" not in agent:
    agent = replace_once(agent, anchor, domain, agent_path)
agent = replace_once(
    agent,
    '        {"type": "web_search", "search_context_size": "high", "user_location": {"type": "approximate", "country": "BR", "region": "São Paulo", "city": "São Paulo", "timezone": "America/Sao_Paulo"}},\n',
    '        {"type": "web_search", "search_context_size": "high", "user_location": {"type": "approximate", "country": "BR", "region": "São Paulo", "city": "São Paulo", "timezone": "America/Sao_Paulo"}},\n        {"type": "code_interpreter", "container": {"type": "auto"}},\n',
    agent_path,
)
write(agent_path, agent)

# Arquitetura universal CRM também recebe Code Interpreter para garantir mesma capacidade nas duas superfícies.
crm_agent_path = "backend/services/ia_comercial_agente_crm.py"
crm_agent = read(crm_agent_path)
crm_agent = crm_agent.replace(
    '    return [\n        {"type": "web_search", "search_context_size": "high", "user_location": {"type": "approximate", "country": "BR", "region": "São Paulo", "city": "São Paulo", "timezone": "America/Sao_Paulo"}},\n',
    '    return [\n        {"type": "web_search", "search_context_size": "high", "user_location": {"type": "approximate", "country": "BR", "region": "São Paulo", "city": "São Paulo", "timezone": "America/Sao_Paulo"}},\n        {"type": "code_interpreter", "container": {"type": "auto"}},\n',
    1,
)
crm_agent = crm_agent.replace("# Fachada de compatibilidade para IA-004/IA-006/IA-007.", "# Contratos históricos de fase mantidos apenas como nomes de API interna; a execução é universal e canônica.")
crm_agent = crm_agent.replace("# Contratos semânticos legados preservados para planejamento/auditoria.", "# Contratos semânticos de fase preservados para planejamento/auditoria.")
crm_agent = crm_agent.replace("# Aliases públicos legados preservados de forma deliberada.", "# Aliases de fase preservados somente para compatibilidade de testes e contratos internos.")
write(crm_agent_path, crm_agent)

# 5) Detecção de artefatos passa a reconhecer planilha/apresentação/documento.
art_path = "backend/services/ia_comercial_artefatos.py"
art = read(art_path)
old_detect = '''    if "RELATORIO" in solicitados:\n        solicitados.add("PDF")\n    return solicitados\n'''
new_detect = '''    if any(termo in texto for termo in ("planilha", "excel", "xlsx", "csv", "tabela em arquivo")):\n        solicitados.add("PLANILHA")\n    if any(termo in texto for termo in ("apresentacao", "apresentação", "powerpoint", "pptx", "slides")):\n        solicitados.add("APRESENTACAO")\n    if any(termo in texto for termo in ("documento", "word", "docx", "memorando", "memo")):\n        solicitados.add("DOCUMENTO")\n    if "RELATORIO" in solicitados:\n        solicitados.add("PDF")\n    return solicitados\n'''
art = replace_once(art, old_detect, new_detect, art_path)
old_tail = '''    if "PDF" in solicitados or "RELATORIO" in solicitados:\n        artefatos.append(\n            {\n                "tipo": "RELATORIO_PDF",\n'''
new_tail = '''    if "PLANILHA" in solicitados:\n        artefatos.append({\n            "tipo": "PLANILHA_XLSX",\n            "titulo": "Planilha — IA Comercial CTI",\n            "fonte_dados": fonte_serie if serie else "resposta_atual",\n            "dados": serie,\n            "auditavel": True,\n        })\n    if "APRESENTACAO" in solicitados:\n        artefatos.append({\n            "tipo": "APRESENTACAO_PPTX",\n            "titulo": "Apresentação — IA Comercial CTI",\n            "fonte_dados": fonte_serie if serie else "resposta_atual",\n            "auditavel": True,\n        })\n    if "DOCUMENTO" in solicitados:\n        artefatos.append({\n            "tipo": "DOCUMENTO_DOCX",\n            "titulo": "Documento — IA Comercial CTI",\n            "fonte_dados": "resposta_atual",\n            "auditavel": True,\n        })\n    if "PDF" in solicitados or "RELATORIO" in solicitados:\n        artefatos.append(\n            {\n                "tipo": "RELATORIO_PDF",\n'''
art = replace_once(art, old_tail, new_tail, art_path)
write(art_path, art)

# 6) Proxy CRM: configuração central e indisponibilidade explícita, nunca zero silencioso.
proxy_path = "frontend/src/app/api/crm-proxy/[...path]/route.ts"
proxy = read(proxy_path)
proxy = replace_once(
    proxy,
    'const BACKEND_CTI = "https://cti-backend-5ugf.onrender.com"',
    'const BACKEND_CTI = (process.env.CTI_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "https://cti-backend-5ugf.onrender.com").replace(/\\/$/, "")',
    proxy_path,
)
proxy = proxy.replace(
    'return NextResponse.json({\n      resumo: { hoje: 0, atrasadas: 0 },\n      itens: [],\n    })',
    'return NextResponse.json({ disponibilidade: "INDISPONIVEL", resumo: { hoje: 0, atrasadas: 0, futuras: 0, sem_data: 0 }, itens: [] }, { status: 503 })',
)
proxy = proxy.replace('return NextResponse.json([])\n  }\n\n  if (caminho.startsWith("modulos/clientes"))', 'return NextResponse.json({ disponibilidade: "INDISPONIVEL", dados: [] }, { status: 503 })\n  }\n\n  if (caminho.startsWith("modulos/clientes"))', 1)
proxy = proxy.replace('if (caminho === "crm/oportunidades") {\n    return NextResponse.json([])\n  }', 'if (caminho === "crm/oportunidades") {\n    return NextResponse.json({ disponibilidade: "INDISPONIVEL", oportunidades: [] }, { status: 503 })\n  }')
write(proxy_path, proxy)

# 7) Requisitos necessários para artefatos Office canônicos no backend.
req_path = "backend/requirements.txt"
req = read(req_path)
for dep in ("python-pptx", "python-docx"):
    if dep not in req:
        req = req.rstrip() + f"\n{dep}\n"
write(req_path, req)

# 8) Testes estáticos de governança arquitetural.
test = '''from pathlib import Path\n\nROOT = Path(__file__).resolve().parents[2]\n\ndef test_sintese_crm_nao_depende_de_modulo_legacy():\n    texto = (ROOT / "backend/services/ia_comercial_sintese_crm.py").read_text(encoding="utf-8")\n    assert "ia_comercial_sintese_crm_legacy" not in texto\n    assert not (ROOT / "backend/services/ia_comercial_sintese_crm_legacy.py").exists()\n\ndef test_persistencia_anfir_usa_implementadora_canonica():\n    texto = (ROOT / "backend/repositories/cti_repository.py").read_text(encoding="utf-8")\n    assert '"implementadora"' in texto\n    assert 'payload["implementador"]' not in texto\n    assert 'payload.pop("implementador")' not in texto\n\ndef test_router_upload_delega_persistencia_ao_engine():\n    texto = (ROOT / "backend/routers/upload_router.py").read_text(encoding="utf-8")\n    assert "upload_engine.persistir_idempotente" in texto\n    assert "resultado_base = repository.persistir_registros_idempotente" not in texto\n\ndef test_ia_exige_dominio_frigorifico_e_code_interpreter():\n    texto = (ROOT / "backend/services/ia_comercial_agente.py").read_text(encoding="utf-8")\n    assert "DOMÍNIO FRIGORÍFICO EXCLUSIVO" in texto\n    assert '"type": "code_interpreter"' in texto\n'''
write("backend/tests/test_cti_saneamento_p0.py", test)

print("CTI P0 aplicado com sucesso")
