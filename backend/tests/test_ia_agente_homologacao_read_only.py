from services.ia_comercial_agente_homologacao import _executar_ferramenta, _ferramentas


def test_catalogo_do_agente_nao_expoe_ferramentas_de_escrita():
    ferramentas = _ferramentas()
    nomes = {
        ferramenta.get("name", "")
        for ferramenta in ferramentas
        if ferramenta.get("type") == "function"
    }

    assert nomes == {
        "consultar_resumo_cti",
        "consultar_dominio_crm",
        "consultar_historico_dashboard",
    }
    assert all(
        not any(verbo in nome for verbo in ("criar", "alterar", "atualizar", "excluir", "deletar", "emitir"))
        for nome in nomes
    )


def test_ferramenta_desconhecida_nao_executa_acao():
    resultado = _executar_ferramenta(
        "excluir_oportunidade",
        {"id": "teste"},
        usuario_id="usuario-teste",
        tipo_usuario="ADMIN_MASTER",
    )

    assert resultado["erro"] == "Ferramenta desconhecida ou não autorizada."


def test_pesquisa_web_e_consultas_sao_as_unicas_capacidades():
    ferramentas = _ferramentas()
    tipos = [ferramenta.get("type") for ferramenta in ferramentas]

    assert tipos.count("web_search") == 1
    assert tipos.count("function") == 3
    assert set(tipos) == {"web_search", "function"}
