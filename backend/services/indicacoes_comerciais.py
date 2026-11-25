"""Indicadores, indicações e comissões.

Cada indicação registra: quem indicou, o cliente, a região, a máquina (linha e
modelo), a quantidade e o valor final. Quando a venda é concluída, a comissão do
indicador é calculada por equipamento conforme a linha:

    Trailer R$ 1.400 · Diesel Truck R$ 900 · Direct Drive R$ 400 (por unidade)

O valor por unidade fica gravado na indicação no momento da venda, para que uma
mudança futura de tabela não altere o histórico. A comissão segue o ciclo
A_PAGAR → NF_RECEBIDA (nota fiscal do indicador) → PAGA.

Indicação ligada a uma oportunidade do CRM acompanha o negócio sozinha: ganho
vira venda concluída e perda vira indicação perdida.

Os registros ficam no cofre privado (um documento por indicação e por indicador).
"""
from __future__ import annotations

import re
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

PASTA_INDICADORES = "indicadores"
PASTA_INDICACOES = "indicacoes"

COMISSAO_POR_LINHA = {"TRAILER": 1400.0, "DIESEL TRUCK": 900.0, "DIRECT DRIVE": 400.0}
LINHAS = tuple(COMISSAO_POR_LINHA)
STATUS = ("INDICADA", "EM_NEGOCIACAO", "VENDIDA", "PERDIDA")
STATUS_COMISSAO = ("A_PAGAR", "NF_RECEBIDA", "PAGA")
STATUS_OPORTUNIDADE_GANHA = {"GANHO", "GANHA", "FATURADO"}
STATUS_OPORTUNIDADE_PERDIDA = {"PERDIDO", "PERDIDA", "CANCELADO", "CANCELADA"}

_trava = threading.Lock()
_cache: dict[str, Any] = {}
VALIDADE_CACHE_S = 60


class ErroIndicacao(ValueError):
    """Pedido inválido (vira 422/409 na API)."""


def _cofre():
    from services import cofre_agente

    return cofre_agente


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id() -> str:
    return uuid.uuid4().hex


def _texto(valor: Any, limite: int = 200) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()[:limite]


def _numero(valor: Any) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def normalizar_linha(valor: Any) -> str:
    texto = re.sub(r"[^A-Z ]", " ", str(valor or "").upper())
    texto = re.sub(r"\s+", " ", texto).strip()
    apelidos = {"TR": "TRAILER", "DT": "DIESEL TRUCK", "DD": "DIRECT DRIVE", "DIESELTRUCK": "DIESEL TRUCK", "DIRECTDRIVE": "DIRECT DRIVE"}
    texto = apelidos.get(texto.replace(" ", ""), apelidos.get(texto, texto))
    if texto not in COMISSAO_POR_LINHA:
        raise ErroIndicacao("Linha inválida: use Trailer, Diesel Truck ou Direct Drive.")
    return texto


def comissao(linha: str, quantidade: int, valor_unitario: float | None = None) -> float:
    unitario = COMISSAO_POR_LINHA[normalizar_linha(linha)] if valor_unitario is None else valor_unitario
    return round(unitario * max(int(quantidade or 0), 0), 2)


# ---------------------------------------------------------------- leitura


def _limpar_cache() -> None:
    with _trava:
        _cache.clear()


def _todos() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    with _trava:
        if _cache and time.monotonic() - _cache["em"] < VALIDADE_CACHE_S:
            return _cache["indicadores"], _cache["indicacoes"]
    cofre = _cofre()
    indicadores = {d["id"]: d for d in cofre.ler_pasta(PASTA_INDICADORES).values() if isinstance(d, dict) and d.get("id")}
    indicacoes = {d["id"]: d for d in cofre.ler_pasta(PASTA_INDICACOES).values() if isinstance(d, dict) and d.get("id")}
    with _trava:
        _cache.update({"indicadores": indicadores, "indicacoes": indicacoes, "em": time.monotonic()})
    return indicadores, indicacoes


def _gravar(pasta: str, registro: dict[str, Any]) -> dict[str, Any]:
    cofre = _cofre()
    cofre.gravar(cofre.caminho(pasta, f"{registro['id']}.json"), registro)
    _limpar_cache()
    return registro


def _historico(registro: dict[str, Any], ator: str, acao: str) -> None:
    registro.setdefault("historico", []).append({"em": _agora(), "por": ator, "acao": acao})


# ---------------------------------------------------------------- indicadores


def listar_indicadores(incluir_inativos: bool = True) -> list[dict[str, Any]]:
    indicadores, _ = _todos()
    lista = [i for i in indicadores.values() if incluir_inativos or i.get("ativo", True)]
    return sorted(lista, key=lambda i: _texto(i.get("nome")).upper())


def salvar_indicador(dados: dict[str, Any], ator: str, indicador_id: str | None = None) -> dict[str, Any]:
    indicadores, _ = _todos()
    atual = dict(indicadores.get(indicador_id or "", {})) if indicador_id else {}
    if indicador_id and not atual:
        raise KeyError(indicador_id)
    nome = _texto(dados.get("nome", atual.get("nome")), 120)
    if len(nome) < 2:
        raise ErroIndicacao("Informe o nome do indicador.")
    documento = re.sub(r"\D", "", str(dados.get("documento", atual.get("documento")) or ""))
    if documento and len(documento) not in (11, 14):
        raise ErroIndicacao("CPF ou CNPJ do indicador inválido.")
    duplicado = next((i for i in indicadores.values() if documento and i.get("documento") == documento and i["id"] != indicador_id), None)
    if duplicado:
        raise ErroIndicacao(f"Já existe um indicador com este documento: {duplicado.get('nome')}.")
    registro = {
        **atual,
        "id": atual.get("id") or _id(),
        "nome": nome,
        "documento": documento or None,
        "telefone": _texto(dados.get("telefone", atual.get("telefone")), 40) or None,
        "email": _texto(dados.get("email", atual.get("email")), 120) or None,
        "regiao": _texto(dados.get("regiao", atual.get("regiao")), 80) or None,
        "dados_pagamento": _texto(dados.get("dados_pagamento", atual.get("dados_pagamento")), 200) or None,
        "ativo": bool(dados.get("ativo", atual.get("ativo", True))),
        "criado_em": atual.get("criado_em") or _agora(),
        "atualizado_em": _agora(),
    }
    _historico(registro, ator, "cadastro atualizado" if atual else "cadastro criado")
    return _gravar(PASTA_INDICADORES, registro)


# ---------------------------------------------------------------- indicações


def _regiao_do_cliente(cliente_id: str | None) -> tuple[str | None, str | None]:
    """(nome do cliente, região) a partir do cadastro, quando houver cliente vinculado."""
    if not cliente_id:
        return None, None
    try:
        from services import carteira_setorizada

        perfis, _, _ = carteira_setorizada._carteira_completa()
    except Exception:
        return None, None
    perfil = next((p for p in perfis if p["cliente_id"] == str(cliente_id)), None)
    if not perfil:
        return None, None
    local = " / ".join(filter(None, [perfil.get("cidade"), perfil.get("estado")]))
    return perfil.get("nome"), perfil.get("sub_regiao") or local or None


def registrar_indicacao(dados: dict[str, Any], ator: str) -> dict[str, Any]:
    indicadores, _ = _todos()
    indicador = indicadores.get(str(dados.get("indicador_id") or ""))
    if not indicador:
        raise ErroIndicacao("Escolha um indicador cadastrado.")
    if not indicador.get("ativo", True):
        raise ErroIndicacao("Este indicador está inativo.")
    cliente_id = _texto(dados.get("cliente_id"), 80) or None
    nome_cadastro, regiao_cadastro = _regiao_do_cliente(cliente_id)
    cliente = _texto(dados.get("cliente_nome"), 160) or nome_cadastro
    if not cliente:
        raise ErroIndicacao("Informe o cliente indicado.")
    regiao = _texto(dados.get("regiao"), 80) or regiao_cadastro
    if not regiao:
        raise ErroIndicacao("Informe a região do cliente.")
    quantidade = int(_numero(dados.get("quantidade")))
    if quantidade < 1 or quantidade > 500:
        raise ErroIndicacao("Quantidade deve ser entre 1 e 500 equipamentos.")
    valor = round(_numero(dados.get("valor_final")), 2)
    if valor < 0:
        raise ErroIndicacao("Valor final inválido.")
    registro = {
        "id": _id(),
        "indicador_id": indicador["id"],
        "indicador_nome": indicador["nome"],
        "cliente_id": cliente_id,
        "cliente_nome": cliente,
        "regiao": regiao,
        "linha": normalizar_linha(dados.get("linha")),
        "modelo": _texto(dados.get("modelo"), 80) or None,
        "quantidade": quantidade,
        "valor_final": valor,
        "oportunidade_id": _texto(dados.get("oportunidade_id"), 80) or None,
        "observacao": _texto(dados.get("observacao"), 500) or None,
        "status": "INDICADA",
        "data_indicacao": _texto(dados.get("data_indicacao"), 10) or _agora()[:10],
        "data_venda": None,
        "comissao_unitaria": None,
        "comissao_valor": None,
        "comissao_status": None,
        "nota_fiscal": None,
        "nf_recebida_em": None,
        "paga_em": None,
        "registrado_por": ator,
        "criado_em": _agora(),
    }
    _historico(registro, ator, "indicação registrada")
    return _gravar(PASTA_INDICACOES, registro)


def _concluir_venda(registro: dict[str, Any], data_venda: str | None) -> None:
    registro["status"] = "VENDIDA"
    registro["data_venda"] = (data_venda or _agora())[:10]
    registro["comissao_unitaria"] = COMISSAO_POR_LINHA[registro["linha"]]
    registro["comissao_valor"] = comissao(registro["linha"], registro["quantidade"], registro["comissao_unitaria"])
    registro["comissao_status"] = registro.get("comissao_status") or "A_PAGAR"


def atualizar_indicacao(indicacao_id: str, dados: dict[str, Any], ator: str) -> dict[str, Any]:
    """Muda status, quantidade/valor final ou o ciclo da comissão (NF e pagamento)."""
    _, indicacoes = _todos()
    if indicacao_id not in indicacoes:
        raise KeyError(indicacao_id)
    registro = dict(indicacoes[indicacao_id])
    paga = registro.get("comissao_status") == "PAGA"
    acoes = []

    if any(k in dados for k in ("quantidade", "valor_final", "linha", "modelo", "regiao", "cliente_nome")):
        if paga:
            raise ErroIndicacao("A comissão desta indicação já foi paga; os dados da venda não podem mudar.")
        if "quantidade" in dados:
            quantidade = int(_numero(dados["quantidade"]))
            if quantidade < 1 or quantidade > 500:
                raise ErroIndicacao("Quantidade deve ser entre 1 e 500 equipamentos.")
            registro["quantidade"] = quantidade
        if "valor_final" in dados:
            registro["valor_final"] = round(max(_numero(dados["valor_final"]), 0), 2)
        linha_anterior = registro["linha"]
        if "linha" in dados:
            registro["linha"] = normalizar_linha(dados["linha"])
        for campo, limite in (("modelo", 80), ("regiao", 80), ("cliente_nome", 160)):
            if campo in dados:
                registro[campo] = _texto(dados[campo], limite) or registro.get(campo)
        acoes.append("dados da venda atualizados")
        if registro["status"] == "VENDIDA":
            # Mantém o valor por equipamento gravado na venda; só troca se a linha mudou.
            if registro["linha"] != linha_anterior or not registro.get("comissao_unitaria"):
                registro["comissao_unitaria"] = COMISSAO_POR_LINHA[registro["linha"]]
            registro["comissao_valor"] = comissao(registro["linha"], registro["quantidade"], registro["comissao_unitaria"])

    if "oportunidade_id" in dados:
        registro["oportunidade_id"] = _texto(dados["oportunidade_id"], 80) or None
        acoes.append("oportunidade vinculada" if registro["oportunidade_id"] else "vínculo com oportunidade removido")

    novo_status = dados.get("status")
    if novo_status and novo_status != registro["status"]:
        if novo_status not in STATUS:
            raise ErroIndicacao("Status inválido.")
        if registro["status"] == "VENDIDA" and registro.get("comissao_status") in {"NF_RECEBIDA", "PAGA"}:
            raise ErroIndicacao("A comissão já tem nota fiscal; não é possível desfazer a venda.")
        if novo_status == "VENDIDA":
            _concluir_venda(registro, dados.get("data_venda"))
        else:
            registro["status"] = novo_status
            registro.update({"data_venda": None, "comissao_unitaria": None, "comissao_valor": None, "comissao_status": None})
        acoes.append(f"status: {novo_status}")

    novo_comissao = dados.get("comissao_status")
    if novo_comissao and novo_comissao != registro.get("comissao_status"):
        if registro["status"] != "VENDIDA":
            raise ErroIndicacao("A comissão só existe para venda concluída.")
        if paga:
            raise ErroIndicacao("Comissão já paga não pode mudar de situação.")
        if novo_comissao == "NF_RECEBIDA":
            nota = _texto(dados.get("nota_fiscal"), 40)
            if not nota:
                raise ErroIndicacao("Informe o número da nota fiscal do indicador.")
            registro.update({"comissao_status": "NF_RECEBIDA", "nota_fiscal": nota, "nf_recebida_em": _agora()})
        elif novo_comissao == "PAGA":
            if registro.get("comissao_status") != "NF_RECEBIDA":
                raise ErroIndicacao("Registre a nota fiscal antes de marcar a comissão como paga.")
            registro.update({"comissao_status": "PAGA", "paga_em": (_texto(dados.get("paga_em"), 10) or _agora()[:10])})
        elif novo_comissao == "A_PAGAR":
            registro.update({"comissao_status": "A_PAGAR", "nota_fiscal": None, "nf_recebida_em": None})
        else:
            raise ErroIndicacao("Situação de comissão inválida.")
        acoes.append(f"comissão: {novo_comissao}")

    if not acoes:
        return registro
    registro["atualizado_em"] = _agora()
    _historico(registro, ator, "; ".join(acoes))
    return _gravar(PASTA_INDICACOES, registro)


def sincronizar_com_oportunidades() -> int:
    """Indicação ligada a oportunidade ganha vira venda; perdida vira perdida. Devolve quantas mudaram."""
    _, indicacoes = _todos()
    abertas: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for i in indicacoes.values():
        if i.get("oportunidade_id") and i["status"] in {"INDICADA", "EM_NEGOCIACAO"}:
            abertas[i["oportunidade_id"]].append(i)
    if not abertas:
        return 0
    try:
        from core.supabase_client import supabase

        dados = supabase.table("cti_oportunidades").select("id,status,valor_total,data_fechamento_real,updated_at").in_("id", list(abertas)).execute().data or []
    except Exception:
        return 0
    mudou = 0
    for oportunidade in dados:
        status = str(oportunidade.get("status") or "").upper()
        for original in abertas.get(str(oportunidade.get("id")), []):
            registro = dict(original)
            if status in STATUS_OPORTUNIDADE_GANHA:
                if not registro.get("valor_final") and _numero(oportunidade.get("valor_total")):
                    registro["valor_final"] = round(_numero(oportunidade.get("valor_total")), 2)
                _concluir_venda(registro, str(oportunidade.get("data_fechamento_real") or oportunidade.get("updated_at") or "") or None)
                _historico(registro, "sistema", f"venda concluída pela oportunidade ({status})")
            elif status in STATUS_OPORTUNIDADE_PERDIDA:
                registro["status"] = "PERDIDA"
                _historico(registro, "sistema", f"oportunidade encerrada ({status})")
            elif registro["status"] == "INDICADA":
                registro["status"] = "EM_NEGOCIACAO"
                _historico(registro, "sistema", "oportunidade em negociação")
            else:
                continue
            registro["atualizado_em"] = _agora()
            _gravar(PASTA_INDICACOES, registro)
            mudou += 1
    return mudou


def listar_indicacoes(indicador_id: str | None = None, ano: int | None = None, mes: int | None = None,
                      status: str | None = None, regiao: str | None = None) -> list[dict[str, Any]]:
    _, indicacoes = _todos()
    saida = []
    for i in indicacoes.values():
        if indicador_id and i["indicador_id"] != indicador_id:
            continue
        if status and i["status"] != status:
            continue
        if regiao and _texto(i.get("regiao")).upper() != _texto(regiao).upper():
            continue
        referencia = i.get("data_venda") or i.get("data_indicacao") or ""
        if ano and not referencia.startswith(f"{ano:04d}"):
            continue
        if ano and mes and not referencia.startswith(f"{ano:04d}-{mes:02d}"):
            continue
        saida.append(i)
    return sorted(saida, key=lambda i: (i.get("data_venda") or i.get("data_indicacao") or ""), reverse=True)


# ---------------------------------------------------------------- relatórios


def _agregar(itens: list[dict[str, Any]]) -> dict[str, Any]:
    vendidas = [i for i in itens if i["status"] == "VENDIDA"]
    encerradas = [i for i in itens if i["status"] in {"VENDIDA", "PERDIDA"}]
    def soma(lista, campo):
        return round(sum(_numero(i.get(campo)) for i in lista), 2)
    return {
        "indicacoes": len(itens),
        "em_aberto": sum(1 for i in itens if i["status"] in {"INDICADA", "EM_NEGOCIACAO"}),
        "vendidas": len(vendidas),
        "perdidas": sum(1 for i in itens if i["status"] == "PERDIDA"),
        "conversao": round(len(vendidas) / len(encerradas), 4) if encerradas else None,
        "equipamentos_vendidos": int(sum(i["quantidade"] for i in vendidas)),
        "valor_vendido": soma(vendidas, "valor_final"),
        "valor_em_aberto": soma([i for i in itens if i["status"] in {"INDICADA", "EM_NEGOCIACAO"}], "valor_final"),
        "comissao_total": soma(vendidas, "comissao_valor"),
        "comissao_a_pagar": soma([i for i in vendidas if i.get("comissao_status") == "A_PAGAR"], "comissao_valor"),
        "comissao_nf_recebida": soma([i for i in vendidas if i.get("comissao_status") == "NF_RECEBIDA"], "comissao_valor"),
        "comissao_paga": soma([i for i in vendidas if i.get("comissao_status") == "PAGA"], "comissao_valor"),
    }


def _vendas_totais(ano: int | None, mes: int | None) -> dict[str, Any]:
    """Total vendido pela Viena no período (CRM: negócios ganhos; planilha: equipamentos) para medir o peso dos indicadores."""
    prefixo = f"{ano:04d}-{mes:02d}" if ano and mes else (f"{ano:04d}" if ano else "")
    valor, unidades = None, None
    try:
        from services.acervo_comercial import paginar

        ganhos = paginar("cti_oportunidades", "id,status,valor_total,data_fechamento_real,updated_at", lambda q: q.is_("arquivado_em", "null"))
        ganhos = [o for o in ganhos if str(o.get("status") or "").upper() in STATUS_OPORTUNIDADE_GANHA
                  and str(o.get("data_fechamento_real") or o.get("updated_at") or "").startswith(prefixo)]
        valor = round(sum(_numero(o.get("valor_total")) for o in ganhos), 2)
    except Exception:
        valor = None
    try:
        from services import planilhas_comerciais

        vendas = planilhas_comerciais.registros("vendas_realizadas")
        unidades = int(sum(_numero(v.get("quantidade")) for v in vendas if str(v.get("data_emissao") or v.get("mes") or "").startswith(prefixo)))
    except Exception:
        unidades = None
    return {"valor_vendido": valor, "equipamentos_vendidos": unidades}


def painel(ano: int | None = None, mes: int | None = None, indicador_id: str | None = None) -> dict[str, Any]:
    itens = listar_indicacoes(indicador_id=indicador_id, ano=ano, mes=mes)
    indicadores, _ = _todos()
    por_indicador: dict[str, list] = defaultdict(list)
    por_regiao: dict[str, list] = defaultdict(list)
    por_linha: dict[str, list] = defaultdict(list)
    for i in itens:
        por_indicador[i["indicador_id"]].append(i)
        por_regiao[i.get("regiao") or "Sem região"].append(i)
        por_linha[i["linha"]].append(i)
    total = _agregar(itens)
    viena = _vendas_totais(ano, mes) if not indicador_id else {"valor_vendido": None, "equipamentos_vendidos": None}
    peso = {
        "valor_vendido_viena": viena["valor_vendido"],
        "equipamentos_vendidos_viena": viena["equipamentos_vendidos"],
        "participacao_valor": round(total["valor_vendido"] / viena["valor_vendido"], 4) if viena["valor_vendido"] else None,
        "participacao_equipamentos": round(total["equipamentos_vendidos"] / viena["equipamentos_vendidos"], 4) if viena["equipamentos_vendidos"] else None,
    }
    linhas_indicador = [{"indicador_id": k, "nome": (indicadores.get(k) or {}).get("nome") or v[0].get("indicador_nome"), **_agregar(v)} for k, v in por_indicador.items()]
    linhas_regiao = [{"regiao": k, **_agregar(v)} for k, v in por_regiao.items()]
    if total["valor_vendido"]:
        for linha in linhas_regiao:
            linha["participacao_no_indicado"] = round(linha["valor_vendido"] / total["valor_vendido"], 4)
    return {
        "periodo": {"ano": ano, "mes": mes},
        "tabela_comissao": COMISSAO_POR_LINHA,
        "total": total,
        "peso_nas_vendas": peso,
        "por_indicador": sorted(linhas_indicador, key=lambda l: (-l["valor_vendido"], -l["indicacoes"])),
        "por_regiao": sorted(linhas_regiao, key=lambda l: (-l["valor_vendido"], -l["indicacoes"])),
        "por_linha": [{"linha": k, "comissao_por_equipamento": COMISSAO_POR_LINHA[k], **_agregar(por_linha.get(k, []))} for k in LINHAS],
    }


def extrato(indicador_id: str, ano: int | None = None, mes: int | None = None) -> dict[str, Any]:
    indicadores, _ = _todos()
    indicador = indicadores.get(indicador_id)
    if not indicador:
        raise KeyError(indicador_id)
    itens = listar_indicacoes(indicador_id=indicador_id, ano=ano, mes=mes)
    return {"indicador": indicador, "periodo": {"ano": ano, "mes": mes}, "resumo": _agregar(itens), "indicacoes": itens}
