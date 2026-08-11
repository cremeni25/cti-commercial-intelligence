from services import ia_comercial_sintese_factual as sintese


PERGUNTA = (
    "Quais implementadoras aparecem com maior frequência no DDD 011, com quais clientes e linhas "
    "elas estão relacionadas, e onde existem sinais de atuação de fabricantes concorrentes de equipamento?"
)


def test_sanitizacao_relacional_remove_afirmacoes_de_relacao_ativa():
    texto = (
        "FIBRA WEST atua especialmente com CLIENTE A, usando equipamentos THERMOKING. "
        "PAVAN atende CLIENTE B. IBIPORÃ tem forte vínculo com CLIENTE C e atua principalmente em linhas TR. "
        "São implementadoras predominantes no recorte."
    )

    resultado, alteracoes = sintese._sanitizar_linguagem_relacional_territorial(texto, PERGUNTA)
    normalizado = resultado.casefold()

    assert alteracoes >= 5
    assert "atua especialmente com" not in normalizado
    assert "atende" not in normalizado
    assert "forte vínculo" not in normalizado
    assert "atua principalmente em linhas" not in normalizado
    assert "predominantes" not in normalizado
    assert "aparece em registros com" in normalizado
    assert "coocorrência histórica" in normalizado


def test_sanitizacao_nao_altera_pergunta_sem_dimensao_territorial_relacional():
    texto = "O produto líder aparece no catálogo."
    resultado, alteracoes = sintese._sanitizar_linguagem_relacional_territorial(
        texto,
        "Quais produtos existem no catálogo?",
    )

    assert resultado == texto
    assert alteracoes == 0


def test_metadado_de_controle_da_normalizacao_existe_no_codigo():
    import inspect

    codigo = inspect.getsource(sintese.sintetizar_fatos_execucao)
    assert "controle_linguagem_relacional" in codigo
    assert "normalizacao_deterministica_pos_sintese" in codigo
