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
    assert 'return "VENDA_DIRETA", faturado_em[:10]' in source


def test_venda_indireta_permanece_ate_encerramento_pos_venda():
    source = VENDAS.read_text(encoding="utf-8")
    assert '_normalizar(oportunidade.get("titulo")) == "VENDAINDIRETA"' in source
    assert 'detail="Venda indireta permanece em acompanhamento e só vira venda após o encerramento operacional do pós-venda."' in source
    assert 'return "VENDA_INDIRETA", encerrado_em[:10]' in source


def test_ciclo_registra_venda_no_marco_correto_sem_depender_da_instalacao_direta():
    source = CICLO.read_text(encoding="utf-8")
    assert 'modalidade == "DIRETA" and etapa == "FATURADO"' in source
    assert 'modalidade == "INDIRETA" and etapa == "ENCERRADO"' in source
    assert '"marco_venda": "NF_CONFIRMADA" if modalidade == "DIRETA" else "ENCERRAMENTO_POS_VENDA"' in source
    assert 'if etapa == "ENCERRADO" and not pedido.get("instalado_em")' in source


def test_tela_explica_que_instalacao_nao_bloqueia_venda_direta():
    source = TELA.read_text(encoding="utf-8")
    assert "Venda direta é reconhecida quando a NF é confirmada." in source
    assert "A instalação não impede nem posterga a venda" in source
    assert "Instalação / acompanhamento ANFIR" in source
