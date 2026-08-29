from pathlib import Path


def test_contrato_carrier_jov_preserva_campos_e_isola_bloco_lateral():
    parser = (Path(__file__).resolve().parents[1] / "parsers/viena_parser.py").read_text(encoding="utf-8")

    assert '"RELATORIO PERFORMANCE 2026"' in parser
    assert '"formato": "CARRIER_JOV"' in parser
    assert 'limite = nomes.index("STATUS PLANO AÇÃO 1") + 1' in parser
    assert 'responsavel=""' in parser
    assert 'linha=texto_util(campo_direto(row, "SEGMENTO"))' in parser
    assert 'motivo=texto_util(campo_direto(row, "MOTIVO CONCORRENTE"))' in parser
    assert 'ocorrencia=_ocorrencia_carrier(row)' in parser
    assert 'partes.append(f"REPRESENTAÇÃO: {representacao}")' in parser
