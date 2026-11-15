"""Campanhas direcionadas, posts do Canal e autorização LGPD.

O agente monta cada campanha a partir da carteira setorizada (Etapa 1):
público, mensagem personalizada por cliente e posts semanais para o Canal
"CTI Viena SP". Nada é enviado sem aprovação da gestão.

Enquanto a API oficial do WhatsApp não está conectada, a campanha aprovada é
disparada pelo próprio WhatsApp Business (link por cliente) ou exportada.
Quando a API estiver conectada, o mesmo registro alimenta o envio automático.

Estado (rascunhos, aprovações, envios e autorizações) fica no cofre privado.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from services import carteira_setorizada

PASTA = "campanhas"
PASTA_CONSENTIMENTO = "consentimentos"

TEXTO_AUTORIZACAO = (
    "Para continuar recebendo novidades, campanhas e atendimento da Viena Refrigeração (Carrier Transicold) "
    "por WhatsApp, responda SIM. Usamos seu contato apenas para assuntos comerciais da Viena, não "
    "compartilhamos com terceiros e você pode pedir para sair a qualquer momento respondendo SAIR."
)

CAMPANHAS: dict[str, dict[str, Any]] = {
    "RENOVACAO": {
        "titulo": "Renovação de frota",
        "publico": "Clientes cujo equipamento mais novo conhecido tem 6 anos ou mais.",
        "filtro": {"sinal": "JANELA_RENOVACAO"},
        "mensagem": (
            "Olá, {contato}! Aqui é da Viena Refrigeração, representante Carrier Transicold em SP. "
            "Pelos nossos registros, parte da frota refrigerada da {empresa} já passou dos 6 anos de uso. "
            "Equipamentos novos consomem menos e reduzem paradas. Posso enviar uma simulação de renovação "
            "para os seus baús?"
        ),
    },
    "CONQUISTA_CONCORRENTE": {
        "titulo": "Comparativo com a concorrência",
        "publico": "Clientes com frota média ou grande que usam equipamentos de outros fabricantes.",
        "filtro": {"sinal": "USA_CONCORRENTE", "portes": ["GRANDE", "MEDIO"]},
        "mensagem": (
            "Olá, {contato}! Aqui é da Viena Refrigeração (Carrier Transicold). Vimos que a {empresa} "
            "opera {frota} equipamentos de refrigeração. Preparamos um comparativo técnico de consumo, "
            "temperatura e assistência para frotas do seu porte. Quer receber?"
        ),
    },
    "REATIVACAO": {
        "titulo": "Reativação de clientes",
        "publico": "Clientes que compraram da Viena, mas não compram há mais de 24 meses.",
        "filtro": {"grupo": "CLIENTE_INATIVO"},
        "mensagem": (
            "Olá, {contato}! Aqui é da Viena Refrigeração. A {empresa} é nossa cliente e faz tempo que "
            "não conversamos. Temos condições novas para equipamentos Carrier e revisão da frota. "
            "Posso te ligar esta semana?"
        ),
    },
    "PROSPECCAO_FROTA": {
        "titulo": "Prospecção de frotas",
        "publico": "Empresas com frota refrigerada registrada que ainda não compraram da Viena.",
        "filtro": {"grupo": "PROSPECT_COM_FROTA"},
        "mensagem": (
            "Olá, {contato}! Aqui é da Viena Refrigeração, representante Carrier Transicold em SP. "
            "Atendemos frotas refrigeradas como a da {empresa} com equipamentos, instalação e assistência. "
            "Posso te mostrar qual equipamento atende cada tamanho de baú e temperatura?"
        ),
    },
    "RELACIONAMENTO": {
        "titulo": "Novidades para clientes ativos",
        "publico": "Clientes que compraram nos últimos 24 meses.",
        "filtro": {"grupo": "CLIENTE_ATIVO"},
        "mensagem": (
            "Olá, {contato}! Aqui é da Viena Refrigeração. Obrigado pela parceria com a {empresa}. "
            "Lançamos o catálogo Carrier atualizado e a Tabela de Aplicação (equipamento x baú x temperatura). "
            "Quer que eu envie?"
        ),
    },
}


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def telefone_whatsapp(valor: Any) -> str | None:
    """Telefone brasileiro em formato internacional (55 + DDD + número) ou None."""
    digitos = re.sub(r"\D", "", str(valor or ""))
    if digitos.startswith("55") and len(digitos) in (12, 13):
        return digitos
    if len(digitos) in (10, 11):
        return "55" + digitos
    return None


def _primeiro_nome(contato: Any) -> str:
    texto = str(contato or "").strip()
    return texto.split()[0].title() if texto else "tudo bem"


def personalizar(modelo: str, cliente: dict[str, Any]) -> str:
    empresa = str(cliente.get("nome") or "sua empresa").strip().title()
    return modelo.format(contato=_primeiro_nome(cliente.get("contato")), empresa=empresa, frota=cliente.get("frota_registrada") or "seus")


def _cofre():
    from services import cofre_agente

    return cofre_agente


def consentimentos() -> dict[str, dict[str, Any]]:
    """Autorizações registradas, por cliente_id."""
    cofre = _cofre()
    return {nome.removesuffix(".json"): dado for nome, dado in cofre.ler_pasta(PASTA_CONSENTIMENTO).items() if isinstance(dado, dict)}


def registrar_consentimento(cliente_id: str, status: str, origem: str, ator: str) -> dict[str, Any]:
    if status not in {"AUTORIZADO", "RECUSADO"}:
        raise ValueError("Status de autorização inválido.")
    cofre = _cofre()
    registro = {"cliente_id": cliente_id, "status": status, "origem": origem, "registrado_por": ator, "registrado_em": _agora()}
    cofre.gravar(cofre.caminho(PASTA_CONSENTIMENTO, f"{cliente_id}.json"), registro)
    return registro


def _publico(codigo: str) -> list[dict[str, Any]]:
    filtro = CAMPANHAS[codigo]["filtro"]
    base = carteira_setorizada.setorizacao(grupo=filtro.get("grupo"), sinal=filtro.get("sinal"), limite=100000)["clientes"]
    if filtro.get("portes"):
        base = [c for c in base if c["porte"] in filtro["portes"]]
    perfis, fontes, _ = carteira_setorizada._carteira_completa()
    cadastro = {str(c.get("id")): c for c in fontes["clientes"]}
    base = [dict(c) for c in base]  # não altera o cache da carteira
    for cliente in base:
        dados = cadastro.get(cliente["cliente_id"], {})
        cliente["contato"] = dados.get("contato")
        cliente["telefone"] = telefone_whatsapp(dados.get("fone"))
    return base


def resumo_campanhas() -> list[dict[str, Any]]:
    autorizacoes = consentimentos()
    saida = []
    for codigo, definicao in CAMPANHAS.items():
        publico = _publico(codigo)
        com_telefone = [c for c in publico if c["telefone"]]
        saida.append({
            "codigo": codigo, "titulo": definicao["titulo"], "publico_descricao": definicao["publico"],
            "total": len(publico), "com_whatsapp": len(com_telefone),
            "autorizados": sum(1 for c in com_telefone if (autorizacoes.get(c["cliente_id"]) or {}).get("status") == "AUTORIZADO"),
            "recusaram": sum(1 for c in publico if (autorizacoes.get(c["cliente_id"]) or {}).get("status") == "RECUSADO"),
            "rascunho": ler_campanha(codigo),
        })
    return saida


def ler_campanha(codigo: str) -> dict[str, Any]:
    cofre = _cofre()
    salvo = cofre.ler(cofre.caminho(PASTA, f"{codigo}.json")) or {}
    return {"mensagem": salvo.get("mensagem") or CAMPANHAS[codigo]["mensagem"], "status": salvo.get("status") or "RASCUNHO",
            "aprovada_por": salvo.get("aprovada_por"), "aprovada_em": salvo.get("aprovada_em"), "enviados": _envios(codigo)}


def salvar_campanha(codigo: str, mensagem: str, aprovar: bool, ator: str) -> dict[str, Any]:
    if codigo not in CAMPANHAS:
        raise KeyError(codigo)
    if not {"{empresa}"} <= set(re.findall(r"\{[a-z]+\}", mensagem)):
        raise ValueError("A mensagem precisa conter {empresa} para ser personalizada.")
    try:
        mensagem.format(contato="", empresa="", frota="")
    except (KeyError, IndexError, ValueError) as erro:
        raise ValueError("Use apenas os campos {contato}, {empresa} e {frota}.") from erro
    cofre = _cofre()
    atual = ler_campanha(codigo)
    atual.pop("enviados", None)  # envios ficam em documentos próprios
    registro = {**atual, "mensagem": mensagem, "status": "APROVADA" if aprovar else "RASCUNHO",
                "aprovada_por": ator if aprovar else None, "aprovada_em": _agora() if aprovar else None, "editada_em": _agora()}
    cofre.gravar(cofre.caminho(PASTA, f"{codigo}.json"), registro)
    return registro


def publico_detalhado(codigo: str) -> dict[str, Any]:
    if codigo not in CAMPANHAS:
        raise KeyError(codigo)
    campanha = ler_campanha(codigo)
    autorizacoes = consentimentos()
    enviados = campanha.get("enviados") or {}
    itens = []
    for cliente in _publico(codigo):
        autorizacao = (autorizacoes.get(cliente["cliente_id"]) or {}).get("status") or "PENDENTE"
        texto = personalizar(campanha["mensagem"], cliente)
        if autorizacao != "AUTORIZADO":
            texto = f"{texto}\n\n{TEXTO_AUTORIZACAO}"
        itens.append({
            "cliente_id": cliente["cliente_id"], "nome": cliente["nome"], "cidade": cliente.get("cidade"),
            "responsavel_nome": cliente.get("responsavel_nome"), "telefone": cliente["telefone"], "autorizacao": autorizacao,
            "mensagem": texto, "enviado_em": enviados.get(cliente["cliente_id"]),
            "link_whatsapp": f"https://wa.me/{cliente['telefone']}?text={quote(texto)}" if cliente["telefone"] and autorizacao != "RECUSADO" else None,
        })
    return {"codigo": codigo, "titulo": CAMPANHAS[codigo]["titulo"], **campanha, "texto_autorizacao": TEXTO_AUTORIZACAO, "clientes": itens}


def _envios(codigo: str) -> dict[str, str]:
    """Envios registrados (um documento por cliente, sem disputa entre gravações)."""
    cofre = _cofre()
    return {str(item["name"]).removesuffix(".json"): str(item.get("created_at") or item.get("updated_at") or "registrado")
            for item in cofre.listar_itens(cofre.caminho(PASTA, "envios", codigo))}


def marcar_enviado(codigo: str, cliente_id: str, ator: str) -> None:
    if codigo not in CAMPANHAS:
        raise KeyError(codigo)
    if ler_campanha(codigo)["status"] != "APROVADA":
        raise ValueError("Aprove a campanha antes de enviar.")
    cofre = _cofre()
    cofre.gravar(cofre.caminho(PASTA, "envios", codigo, f"{cliente_id}.json"), {"cliente_id": cliente_id, "enviado_por": ator, "enviado_em": _agora()})


def posts_do_canal() -> list[dict[str, str]]:
    """Três posts semanais para o Canal "CTI Viena SP", rodando linha de produto e tema."""
    from services.catalogo_vitrine import tabela_aplicacao

    semana = datetime.now(timezone.utc).isocalendar().week
    linhas = [
        ("Direct Drive (Citimax)", "para baús de 2,8 m a 9,4 m em entregas urbanas, acoplado ao motor do veículo"),
        ("Diesel Truck (Supra)", "com motor próprio a diesel, para baús grandes e rotas longas, chegando a -29 °C"),
        ("Trailer (Vector/X4)", "para carretas refrigeradas, com controle preciso de temperatura em longas distâncias"),
    ]
    linha, descricao = linhas[semana % len(linhas)]
    tabela = tabela_aplicacao() or {}
    exemplo = ""
    for equipamento in tabela.get("equipamentos", []):
        pares = [(t, tam) for t, tam in zip(equipamento.get("temperaturas", []), tabela.get("tamanhos", [])) if t is not None]
        if pares:
            temperatura, tamanho = min(pares, key=lambda par: par[0])
            exemplo = f"{equipamento['modelo']} chega a {temperatura} °C em baú de {tamanho.get('codigo')}"
            break
    return [
        {"tema": "Linha da semana", "texto": f"🚚❄️ Linha da semana: Carrier Transicold {linha}, {descricao}. Quer saber qual modelo atende o seu baú? Fale com a Viena Refrigeração."},
        {"tema": "Dica técnica", "texto": f"📏 Qual equipamento para o meu baú? A Tabela de Aplicação Carrier cruza tamanho do baú e temperatura. Exemplo: {exemplo or 'cada modelo tem a sua faixa'}. Peça a tabela completa à Viena."},
        {"tema": "Chamada para conversa", "texto": "🔧 Frota com mais de 6 anos? Equipamentos novos consomem menos e param menos. A Viena Refrigeração faz uma simulação de renovação para a sua frota. Chame no WhatsApp."},
    ]
