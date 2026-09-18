from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VENDAS = ROOT / "backend" / "routers" / "vendas_router.py"
CICLO = ROOT / "backend" / "routers" / "pedidos_ciclo_router.py"
TELA = ROOT / "frontend" / "src" / "app" / "pedidos" / "[id]" / "ciclo" / "page.tsx"


def test_venda_direta_exige_nf_e_faturamento():
    source = VENDAS.read_text(encoding="utf-8")
    assert 'detail="Venda direta só pode ser reconhecida após a confirmação da Nota Fiscal."' in source
    assert 'pedido.get("faturado_em")' in source
    assert 'pedido.get("numero_nf")' in source
    assert 'return "VENDA_DIRETA", faturado_em[:10], "NF"' in source


def test_venda_indireta_so_existe_a_partir_do_pedido_da_proposta_aceita():
    source = VENDAS.read_text(encoding="utf-8")
    assert 'proposta_id = pedido.get("proposta_id") or pedido.get("proposta_aceita_id")' in source
    assert '_normalizar(oportunidade.get("titulo")) == "VENDAINDIRETA"' in source


def test_venda_indireta_e_reconhecida_por_anfir_ou_vendedor():
    source = VENDAS.read_text(encoding="utf-8")
    assert 'origem not in {"VENDEDOR", "ANFIR"}' in source
    assert 'finalizado pelo cliente e pela implementadora' in source
    assert 'return "VENDA_INDIRETA", data_venda, "ANFIR"' in source
    assert 'return "VENDA_INDIRETA", datetime.now(timezone.utc).date().isoformat(), "VENDEDOR"' in source


def test_anfir_indireta_exige_vinculo_conservador_com_cnpj_e_equipamento_do_pedido():
    source = VENDAS.read_text(encoding="utf-8")
    assert '_normalizar(registro.get("cnpj")) != cnpj' in source
    assert 'equipamento != modelo and equipamento not in modelo and modelo not in equipamento' in source
    assert 'data_registro < data_pedido' in source


def test_ciclo_direto_registra_venda_na_nf_e_indireto_nao_depende_de_instalacao():
    source = CICLO.read_text(encoding="utf-8")
    assert '_modalidade_venda(pedido) != "DIRETA" or etapa != "FATURADO"' in source
    assert '"marco_venda": "NF_CONFIRMADA" if modalidade == "DIRETA" else "ANFIR_OU_VENDEDOR"' in source
    assert 'Pedido de venda indireta não percorre faturamento/instalação como condição de venda.' in source
    assert '_sincronizar_venda_indireta_por_anfir' in source


def test_tela_explica_que_instalacao_nao_bloqueia_venda_direta():
    source = TELA.read_text(encoding="utf-8")
    assert "Venda direta é reconhecida quando a NF é confirmada." in source
    assert "A instalação não impede nem posterga a venda" in source
    assert "Instalação / acompanhamento ANFIR" in source
