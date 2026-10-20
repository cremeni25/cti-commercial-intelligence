from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from xml.sax.saxutils import escape
from pydantic import BaseModel, Field
from decimal import Decimal
from core.admin_auth import UsuarioAutenticado, usuario_atual
from core.supabase_client import supabase

router = APIRouter(prefix="/crm-seguro/feiras", tags=["feiras-eventos"])

class ItemIntencao(BaseModel):
    codigo_produto: str | None = None
    lancamento_feira: bool = False
    descricao_lancamento: str | None = None
    linha_produto: str = Field(min_length=2)
    nome_produto: str = Field(min_length=2)
    quantidade: int = Field(ge=1, le=100000)

class Atendimento(BaseModel):
    feira_id: str
    empresa: str = Field(min_length=2)
    cnpj: str | None = None
    visitante: str = Field(min_length=2)
    contato: str | None = None
    email: str | None = None
    cidade: str | None = None
    uf: str | None = None
    regiao: str = "A_CONFIRMAR"
    autorizado_destino: str | None = None
    interesse: str | None = None
    observacoes: str | None = None
    moeda: str | None = None
    valor_referencia: Decimal | None = None
    itens: list[ItemIntencao] = Field(default_factory=list)

@router.get("")
def listar_feiras(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return supabase.table("cti_feiras").select("*").order("inicio", desc=True).execute().data or []

@router.get("/catalogo")
def catalogo(usuario: UsuarioAutenticado = Depends(usuario_atual)):
    return supabase.table("cti_catalogo_equipamentos").select("codigo,linha_produto,nome_comercial").eq("ativo",True).order("linha_produto").execute().data or []

@router.get("/{feira_id}/atendimentos")
def listar_atendimentos(feira_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    rows = supabase.table("cti_feira_atendimentos").select("*").eq("feira_id",feira_id).order("criado_em",desc=True).limit(1000).execute().data or []
    if rows:
        ids = [r["id"] for r in rows]
        itens = supabase.table("cti_feira_itens").select("*").in_("atendimento_id",ids).execute().data or []
        for r in rows:
            r["itens"] = [i for i in itens if i["atendimento_id"] == r["id"]]
    return rows

@router.post("/{feira_id}/atendimentos", status_code=201)
def registrar_atendimento(feira_id: str, entrada: Atendimento, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    if entrada.feira_id != feira_id:
        raise HTTPException(422,"Feira inconsistente.")
    if entrada.regiao not in {"VIENA","OUTRA","A_CONFIRMAR"}:
        raise HTTPException(422,"Região inválida.")
    if entrada.moeda not in {None,"BRL","USD"}:
        raise HTTPException(422,"Moeda inválida.")
    if entrada.valor_referencia is not None and entrada.valor_referencia < 0:
        raise HTTPException(422,"Valor inválido.")
    if not entrada.itens:
        raise HTTPException(422,"Informe ao menos um equipamento.")
    if entrada.valor_referencia is not None and not entrada.moeda:
        raise HTTPException(422,"Informe a moeda do valor de referência.")
    codigos = [str(i.codigo_produto or "").strip() for i in entrada.itens if not i.lancamento_feira]
    for i in entrada.itens:
        if i.lancamento_feira:
            if not str(i.codigo_produto or "").strip() or not str(i.descricao_lancamento or "").strip():
                raise HTTPException(422,"Lançamento de feira exige código e descrição.")
        elif not str(i.codigo_produto or "").strip():
            raise HTTPException(422,"Selecione um equipamento do catálogo.")
    catalogados = (supabase.table("cti_catalogo_equipamentos")
        .select("codigo,linha_produto,nome_comercial").eq("ativo",True)
        .in_("codigo",list(set(codigos))).execute().data or []) if codigos else []
    por_codigo = {str(p["codigo"]):p for p in catalogados}
    if any(codigo not in por_codigo for codigo in codigos):
        raise HTTPException(422,"Um ou mais equipamentos não estão ativos no catálogo.")

    feiras = supabase.table("cti_feiras").select("id").eq("id",feira_id).limit(1).execute().data or []
    if not feiras:
        raise HTTPException(404,"Feira não localizada.")
    payload = entrada.model_dump(exclude={"itens","feira_id"})
    payload["feira_id"] = feira_id
    payload["criado_por"] = str(usuario.id)
    registro = supabase.table("cti_feira_atendimentos").insert(payload).execute().data
    if not registro:
        raise HTTPException(503,"Atendimento não confirmado.")
    atendimento = registro[0]
    try:
        itens = [dict(
            atendimento_id=atendimento["id"],
            codigo_produto=i.codigo_produto,
            linha_produto=i.linha_produto if i.lancamento_feira else por_codigo[i.codigo_produto]["linha_produto"],
            nome_produto=i.nome_produto if i.lancamento_feira else por_codigo[i.codigo_produto]["nome_comercial"],
            quantidade=i.quantidade,
            lancamento_feira=i.lancamento_feira,
            descricao_lancamento=i.descricao_lancamento if i.lancamento_feira else None
        ) for i in entrada.itens]
        supabase.table("cti_feira_itens").insert(itens).execute()
    except Exception:
        supabase.table("cti_feira_atendimentos").delete().eq("id",atendimento["id"]).execute()
        raise HTTPException(503,"Itens não gravados; atendimento revertido.")
    return {"id":atendimento["id"],"status":"REGISTRADO"}

@router.post("/{feira_id}/atendimentos/{atendimento_id}/converter-oportunidade")
def converter_oportunidade(feira_id: str, atendimento_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    from routers.crm_scope_cliente_referencia_router import _criar_oportunidade, _resolver_cliente, _usa_escopo_proprio
    from routers.clientes_oportunidade_router import ClienteOportunidadeCreate, ClienteContexto, OportunidadeContexto
    registros = (supabase.table("cti_feira_atendimentos").select("*")
        .eq("id",atendimento_id).eq("feira_id",feira_id).limit(1).execute().data or [])
    if not registros:
        raise HTTPException(404,"Atendimento não localizado.")
    a = registros[0]
    if a.get("regiao") != "VIENA":
        raise HTTPException(403,"Somente intenções da região VIENA podem gerar oportunidade no CTI.")
    if a.get("oportunidade_id"):
        return {"oportunidade_id":a["oportunidade_id"],"reutilizada":True}
    itens = (supabase.table("cti_feira_itens").select("*")
        .eq("atendimento_id",atendimento_id).execute().data or [])
    if not itens:
        raise HTTPException(422,"Intenção sem equipamentos.")
    linhas = []
    for i in itens:
        prefixo = "LANÇAMENTO DA FEIRA - PENDENTE DE HOMOLOGAÇÃO" if i.get("lancamento_feira") else "CATÁLOGO CTI"
        linhas.append(f'{prefixo}: {i.get("quantidade")} x {i.get("nome_produto")} (código {i.get("codigo_produto")})')
    descricao = "Origem: Feira / "+str(feira_id)+"; atendimento "+str(atendimento_id)+"\n"+"\n".join(linhas)
    if any(i.get("lancamento_feira") for i in itens):
        descricao += "\nATENÇÃO: lançamento não homologado; não emitir proposta formal para este item."
    dados = ClienteOportunidadeCreate(
        cliente=ClienteContexto(nome=a["empresa"],cidade=a.get("cidade"),estado=a.get("uf")),
        oportunidade=OportunidadeContexto(
            responsavel_id=str(usuario.id),
            titulo="Feira - "+str(a["empresa"]),
            descricao=descricao,
            valor_estimado=0,
            probabilidade=0,
            linha_equipamentos="FEIRA",
            equipamento=", ".join(str(i.get("nome_produto")) for i in itens)
        )
    )
    if _usa_escopo_proprio(usuario):
        dados = dados.model_copy(update={"oportunidade":dados.oportunidade.model_copy(update={"responsavel_id":str(usuario.id)})})
    cliente, compat = _resolver_cliente(dados)
    resultado = _criar_oportunidade(dados,cliente,compat)
    oportunidade = resultado.get("oportunidade") or {}
    oportunidade_id = oportunidade.get("id")
    if not oportunidade_id:
        raise HTTPException(503,"Oportunidade não confirmada; atendimento preservado.")
    supabase.table("cti_feira_atendimentos").update({"oportunidade_id":oportunidade_id,"status":"CONVERTIDO"}).eq("id",atendimento_id).eq("feira_id",feira_id).is_("oportunidade_id","null").execute()
    return {"oportunidade_id":oportunidade_id,"reutilizada":bool(resultado.get("reutilizada"))}

@router.delete("/{feira_id}/atendimentos/{atendimento_id}")
def excluir_atendimento_teste(feira_id: str, atendimento_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    if usuario.tipo_usuario not in {"ADMIN_MASTER","DIRETOR_VIENA_SP","ADMIN_COMERCIAL_VIENA_SP"}:
        raise HTTPException(403,"Exclusão de teste restrita à gestão.")
    registros = (supabase.table("cti_feira_atendimentos").select("id,criado_por,observacoes,oportunidade_id")
        .eq("id",atendimento_id).eq("feira_id",feira_id).limit(1).execute().data or [])
    if not registros:
        raise HTTPException(404,"Atendimento não localizado.")
    registro = registros[0]
    if not str(registro.get("observacoes") or "").lstrip().upper().startswith("[TESTE]"):
        raise HTTPException(409,"Somente atendimentos identificados com [TESTE] podem ser excluídos.")
    if registro.get("oportunidade_id"):
        raise HTTPException(409,"Registro vinculado a oportunidade não pode ser excluído.")
    supabase.table("cti_feira_atendimentos").delete().eq("id",atendimento_id).eq("feira_id",feira_id).execute()
    return {"excluido":True,"id":atendimento_id}

@router.get("/{feira_id}/relatorio.pdf")
def relatorio_pdf(feira_id: str, usuario: UsuarioAutenticado = Depends(usuario_atual)):
    feira = supabase.table("cti_feiras").select("nome").eq("id",feira_id).limit(1).execute().data or []
    if not feira:
        raise HTTPException(404,"Feira não localizada.")
    registros = listar_atendimentos(feira_id, usuario)
    memoria = BytesIO()
    doc = SimpleDocTemplate(memoria,pagesize=landscape(A4),leftMargin=25,rightMargin=25,topMargin=30,bottomMargin=30)
    estilo = getSampleStyleSheet()
    titulo = Paragraph("CTI / VIENA - "+escape(feira[0]["nome"]),estilo["Title"])
    cabecalho = ["Empresa","Visitante","Cidade/UF","Região","Equipamentos","Data"]
    linhas = [cabecalho]
    for a in registros:
        produtos = "; ".join(str(i.get("quantidade",0))+"x "+str(i.get("nome_produto",""))+(" [LANÇAMENTO DA FEIRA]" if i.get("lancamento_feira") else "") for i in a.get("itens",[]))
        campos = [a.get("empresa"),a.get("visitante"),str(a.get("cidade") or "")+"/"+str(a.get("uf") or ""),a.get("regiao"),produtos,str(a.get("criado_em") or "")[:16]]
        linhas.append([Paragraph(escape(str(x or "")),estilo["BodyText"]) for x in campos])
    tabela = Table(linhas,colWidths=[125,100,100,75,275,90],repeatRows=1,hAlign="LEFT")
    tabela.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#E6EFF7")),("GRID",(0,0),(-1,-1),0.3,colors.grey),("VALIGN",(0,0),(-1,-1),"TOP"),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    doc.build([titulo,Spacer(1,12),Paragraph(f"Total de atendimentos: {len(registros)}",estilo["Normal"]),Spacer(1,12),tabela])
    memoria.seek(0)
    return StreamingResponse(memoria,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=cti-feira-relatorio.pdf"})
