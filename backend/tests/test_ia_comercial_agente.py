from services import ia_comercial_agente as agente


def test_catalogo_agente_combina_web_e_ferramentas_cti():
    ferramentas = agente.ferramentas_agente()
    tipos = [item["type"] for item in ferramentas]
    nomes = {item.get("name") for item in ferramentas if item.get("type") == "function"}

    assert "web_search" in tipos
    assert nomes == {
        "consultar_resumo_cti",
        "consultar_dominio_cti",
        "consultar_historico_cti",
    }


def test_entrada_inicial_preserva_contexto_conversacional_recente():
    historico = [
        {"role": "user", "content": "Analise o cliente Alfa."},
        {"role": "assistant", "content": "Vou considerar os dados disponíveis."},
    ]

    entrada = agente._entrada_inicial("Agora compare com o mercado.", historico)

    assert entrada == [
        {"role": "user", "content": "Analise o cliente Alfa."},
        {"role": "assistant", "content": "Vou considerar os dados disponíveis."},
        {"role": "user", "content": "Agora compare com o mercado."},
    ]


def test_consultar_resumo_cti_respeita_resultado_autorizado(monkeypatch):
    monkeypatch.setattr(
        agente,
        "contexto_comercial",
        lambda usuario_id, tipo_usuario: {
            "escopo": "usuario_autorizado",
            "quantidades": {"oportunidades": 4},
            "valores": {"pedidos_em_curso": 150000.0},
            "fontes_disponiveis": ["CRM"],
        },
    )

    resultado = agente._executar_ferramenta_cti(
        "consultar_resumo_cti",
        {},
        "usuario-1",
        "VENDEDOR",
    )

    assert resultado["escopo"] == "usuario_autorizado"
    assert resultado["quantidades"]["oportunidades"] == 4
    assert resultado["valores"]["pedidos_em_curso"] == 150000.0
