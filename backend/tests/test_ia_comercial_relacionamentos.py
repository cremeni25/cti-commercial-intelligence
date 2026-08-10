from services import ia_comercial_agente as agente


def test_pergunta_relacional_de_vendas_usa_vinculos_da_entidade_base():
    requeridas = agente._fontes_requeridas(
        "Quantas vendas existem no CTI e quais clientes, produtos e oportunidades estão relacionados a elas?"
    )

    assert requeridas == {"vendas", "relacionamentos_vendas"}


def test_consulta_de_vendas_satisfaz_evidencia_de_relacionamentos_resolvidos():
    rastreio = [
        {
            "tipo": "CTI",
            "ferramenta": "consultar_dominio_cti",
            "argumentos": {"dominio": "vendas", "termo": None, "status": None, "limite": 100, "offset": 0},
        }
    ]

    presentes = agente._evidencias_presentes(rastreio, [])

    assert "vendas" in presentes
    assert "relacionamentos_vendas" in presentes
    assert "clientes" not in presentes
    assert "oportunidades" not in presentes


def test_sintese_relacional_proibe_incluir_registros_sem_vinculo():
    instrucao = agente._instrucao_sintese_final({"vendas", "relacionamentos_vendas"})

    assert "somente os vínculos explícitos" in instrucao
    assert "Não acrescente outros clientes, produtos ou oportunidades" in instrucao
    assert "não há oportunidade vinculada" in instrucao
    assert "não exigiu web" in instrucao
