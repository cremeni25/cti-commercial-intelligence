from datetime import date

from services.anfir_market_intelligence import consolidar_inteligencia_mercado
from services.operational_filters import filtrar_registros, selecionar_snapshot_viena


def _registro(ano, mes, linha, cliente, *, fonte="legado", ocorrencia=""):
    base = {
        "ano": ano,
        "ano_referencia": ano,
        "mes": mes,
        "linha": linha,
        "cliente": cliente,
        "empresa": cliente,
        "status": "TK",
        "ocorrencia": ocorrencia,
        "origem_base": "VIENA_SP",
        "autorizado": "VIENA",
        "estado": "SP",
        "cidade": "SAO PAULO",
    }
    if fonte == "carrier":
        base.update({
            "aba_origem": f"Relatorio Performance {ano}",
            "versao_parser": "3.1.0",
            "pipeline": "UPLOAD_ANFIR_OPERACIONAL",
        })
    elif fonte == "parser3":
        base.update({
            "aba_origem": f"Viena SP {ano}",
            "versao_parser": "3.0.0",
            "pipeline": "UPLOAD_ANFIR_OPERACIONAL",
        })
    else:
        base.update({
            "aba_origem": f"Viena SP {ano}",
            "versao_parser": "2.0.0",
            "pipeline": "UPLOAD_VIENA",
        })
    return base


def test_carrier_jov_substitui_snapshots_viena_do_mesmo_ano_sem_apagar_historico():
    base = [
        _registro(2025, 7, "DIRECT DRIVE", "HIST-2025", fonte="legado"),
        _registro(2026, 3, "TRAILER", "OLD-2", fonte="legado"),
        _registro(2026, 4, "DIESEL TRUCK", "OLD-3", fonte="parser3"),
        _registro(2026, 5, "DIRECT DRIVE", "NOVO-2026", fonte="carrier"),
    ]

    selecionados = selecionar_snapshot_viena(base)
    clientes = {registro["cliente"] for registro in selecionados}

    assert clientes == {"HIST-2025", "NOVO-2026"}


def test_sem_snapshot_carrier_base_historica_permanece_inalterada():
    base = [
        _registro(2025, 1, "TRAILER", "A", fonte="legado"),
        _registro(2025, 2, "DIRECT DRIVE", "B", fonte="parser3"),
    ]
    assert selecionar_snapshot_viena(base) == base


def test_precedencia_e_aplicada_em_viena_mas_nao_no_contexto_brasil():
    antigo = _registro(2026, 4, "DIRECT DRIVE", "ANTIGO", fonte="parser3")
    novo = _registro(2026, 4, "DIRECT DRIVE", "NOVO", fonte="carrier")
    base = [antigo, novo]

    viena = filtrar_registros(
        base,
        contexto="viena-sp",
        inicio=date(2026, 1, 1),
        fim=date(2026, 12, 31),
    )
    brasil = filtrar_registros(
        base,
        contexto="brasil",
        inicio=date(2026, 1, 1),
        fim=date(2026, 12, 31),
    )

    assert [registro["cliente"] for registro in viena] == ["NOVO"]
    assert {registro["cliente"] for registro in brasil} == {"ANTIGO", "NOVO"}


def test_observacao_do_snapshot_antigo_nao_contamina_inteligencia_2026():
    antigo = _registro(
        2026,
        4,
        "DIRECT DRIVE",
        "ANTIGO",
        fonte="parser3",
        ocorrencia="OBSERVAÇÃO: Thermo King preço manutenção relacionamento",
    )
    novo = _registro(
        2026,
        4,
        "DIRECT DRIVE",
        "NOVO",
        fonte="carrier",
        ocorrencia="OBSERVAÇÃO: cliente avaliando solução técnica",
    )

    analisados = filtrar_registros(
        [antigo, novo],
        contexto="viena-sp",
        inicio=date(2026, 1, 1),
        fim=date(2026, 12, 31),
    )
    mercado = consolidar_inteligencia_mercado(analisados, [])
    temas = {item["tema"] for item in mercado["inteligencia_observacoes"]["temas"]}

    assert mercado["mercado"]["volume"] == 1
    assert "CONCORRENTE_TK" not in temas
    assert "PRECO_VALOR" not in temas
    assert "RELACIONAMENTO" not in temas
    assert "TECNICO_PRODUTO" in temas
