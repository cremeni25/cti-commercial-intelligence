"""Indicadores, indicações e comissões.

Uso exclusivo do Master: é ele quem cadastra indicadores, lança indicações,
registra nota fiscal e pagamento e lê os relatórios. Indicadores não têm acesso
ao CTI nem ao aplicativo.
"""
from __future__ import annotations

import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core.admin_auth import UsuarioAutenticado, usuario_atual
from services import indicacoes_comerciais as ind

router = APIRouter(prefix="/crm-seguro/indicacoes", tags=["Indicadores e comissões"])

def _erro(erro: Exception) -> HTTPException:
    if isinstance(erro, KeyError):
        return HTTPException(status_code=404, detail="Registro não encontrado.")
    return HTTPException(status_code=422, detail=str(erro))


def master(usuario: UsuarioAutenticado = Depends(usuario_atual)) -> UsuarioAutenticado:
    if str(usuario.tipo_usuario or "").upper() != "ADMIN_MASTER":
        raise HTTPException(status_code=403, detail="Indicadores e comissões são de uso exclusivo do Master.")
    return usuario


class Indicador(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    documento: str | None = Field(default=None, max_length=20)
    telefone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    regiao: str | None = Field(default=None, max_length=80)
    dados_pagamento: str | None = Field(default=None, max_length=200)
    ativo: bool = True


class NovaIndicacao(BaseModel):
    indicador_id: str | None = Field(default=None, max_length=80)
    cliente_id: str | None = Field(default=None, max_length=80)
    cliente_nome: str | None = Field(default=None, max_length=160)
    regiao: str | None = Field(default=None, max_length=80)
    linha: str = Field(max_length=20)
    modelo: str | None = Field(default=None, max_length=80)
    quantidade: int = Field(ge=1, le=500)
    valor_final: float = Field(ge=0, le=1e9)
    oportunidade_id: str | None = Field(default=None, max_length=80)
    observacao: str | None = Field(default=None, max_length=500)
    data_indicacao: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class AtualizarIndicacao(BaseModel):
    status: str | None = None
    data_venda: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    quantidade: int | None = Field(default=None, ge=1, le=500)
    valor_final: float | None = Field(default=None, ge=0, le=1e9)
    linha: str | None = None
    modelo: str | None = Field(default=None, max_length=80)
    regiao: str | None = Field(default=None, max_length=80)
    cliente_nome: str | None = Field(default=None, max_length=160)
    oportunidade_id: str | None = Field(default=None, max_length=80)
    comissao_status: str | None = None
    nota_fiscal: str | None = Field(default=None, max_length=40)
    paga_em: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


@router.get("/acesso")
def acesso(usuario: UsuarioAutenticado = Depends(master)):
    return {"tabela_comissao": ind.COMISSAO_POR_LINHA}


@router.get("/indicadores")
def indicadores(usuario: UsuarioAutenticado = Depends(master)):
    return {"indicadores": ind.listar_indicadores()}


@router.post("/indicadores", status_code=201)
def criar_indicador(corpo: Indicador, usuario: UsuarioAutenticado = Depends(master)):
    try:
        return ind.salvar_indicador(corpo.model_dump(), str(usuario.id))
    except (ind.ErroIndicacao, KeyError) as erro:
        raise _erro(erro) from erro


@router.put("/indicadores/{indicador_id}")
def editar_indicador(indicador_id: str, corpo: Indicador, usuario: UsuarioAutenticado = Depends(master)):
    try:
        return ind.salvar_indicador(corpo.model_dump(), str(usuario.id), indicador_id)
    except (ind.ErroIndicacao, KeyError) as erro:
        raise _erro(erro) from erro


@router.get("")
def listar(
    indicador_id: str | None = Query(default=None, max_length=80),
    ano: int | None = Query(default=None, ge=2000, le=2100),
    mes: int | None = Query(default=None, ge=1, le=12),
    status: str | None = Query(default=None, max_length=20),
    regiao: str | None = Query(default=None, max_length=80),
    usuario: UsuarioAutenticado = Depends(master),
):
    ind.sincronizar_com_oportunidades()
    return {"indicacoes": ind.listar_indicacoes(indicador_id, ano, mes, status, regiao)}


@router.post("", status_code=201)
def registrar(corpo: NovaIndicacao, usuario: UsuarioAutenticado = Depends(master)):
    try:
        return ind.registrar_indicacao(corpo.model_dump(), str(usuario.id))
    except (ind.ErroIndicacao, KeyError) as erro:
        raise _erro(erro) from erro


@router.patch("/{indicacao_id}")
def atualizar(indicacao_id: str, corpo: AtualizarIndicacao, usuario: UsuarioAutenticado = Depends(master)):
    try:
        return ind.atualizar_indicacao(indicacao_id, corpo.model_dump(exclude_unset=True), str(usuario.id))
    except (ind.ErroIndicacao, KeyError) as erro:
        raise _erro(erro) from erro


@router.get("/painel")
def painel(
    ano: int | None = Query(default=None, ge=2000, le=2100),
    mes: int | None = Query(default=None, ge=1, le=12),
    usuario: UsuarioAutenticado = Depends(master),
):
    ind.sincronizar_com_oportunidades()
    return ind.painel(ano, mes)


@router.get("/indicadores/{indicador_id}/extrato")
def extrato(indicador_id: str, ano: int | None = Query(default=None, ge=2000, le=2100), mes: int | None = Query(default=None, ge=1, le=12),
            usuario: UsuarioAutenticado = Depends(master)):
    ind.sincronizar_com_oportunidades()
    try:
        return ind.extrato(indicador_id, ano, mes)
    except KeyError as erro:
        raise _erro(erro) from erro


@router.get("/indicadores/{indicador_id}/extrato.csv")
def extrato_csv(indicador_id: str, ano: int | None = Query(default=None, ge=2000, le=2100), mes: int | None = Query(default=None, ge=1, le=12),
                usuario: UsuarioAutenticado = Depends(master)):
    ind.sincronizar_com_oportunidades()
    try:
        dados = ind.extrato(indicador_id, ano, mes)
    except KeyError as erro:
        raise _erro(erro) from erro
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(["indicador", "cliente", "regiao", "linha", "modelo", "quantidade", "valor_final", "status", "data_indicacao", "data_venda",
                       "comissao_por_equipamento", "comissao", "situacao_comissao", "nota_fiscal", "paga_em"])
    moeda = lambda v: "" if v is None else f"{float(v):.2f}".replace(".", ",")  # noqa: E731
    for i in dados["indicacoes"]:
        escritor.writerow([i["indicador_nome"], i["cliente_nome"], i.get("regiao") or "", i["linha"], i.get("modelo") or "", i["quantidade"],
                           moeda(i["valor_final"]), i["status"], i.get("data_indicacao") or "", i.get("data_venda") or "",
                           moeda(i.get("comissao_unitaria")), moeda(i.get("comissao_valor")), i.get("comissao_status") or "",
                           i.get("nota_fiscal") or "", i.get("paga_em") or ""])
    nome = "".join(c for c in dados["indicador"]["nome"].lower().replace(" ", "-") if c.isalnum() or c == "-")[:40] or "indicador"
    return Response(content="﻿" + saida.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="extrato-{nome}.csv"'})
