"""Registro oficial de módulos da plataforma CTI.

Fonte única que descreve *o que a plataforma faz*: cada módulo declara onde
vive (rotas web e app), quem pode vê-lo (permissões), com que estágio de
maturidade opera e com que fontes alimenta o Agente de Inteligência.

Adicionar um módulo novo (ex.: Treinamentos Comerciais) começa aqui:
1. declare o ``ModuloPlataforma`` com ``status="planejado"``;
2. crie as rotas/telas e mude para ``"beta"`` → ``"ativo"``;
3. se o módulo gera sinais comerciais, registre um provedor em
   ``services/inteligencia_comercial`` e cite o código em ``provedores``.

O teste ``tests/test_modulos_plataforma.py`` garante que toda rota declarada
existe no frontend, evitando links quebrados na Central.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

STATUS_MODULO = ("ativo", "beta", "planejado")
CATEGORIAS_MODULO = {
    "inteligencia": "Inteligência",
    "operacao": "Operação comercial",
    "mercado": "Mercado",
    "conhecimento": "Conhecimento",
    "administracao": "Administração",
}


@dataclass(frozen=True)
class ModuloPlataforma:
    codigo: str
    nome: str
    descricao: str
    categoria: str
    status: str
    rota_web: str | None = None
    rota_app: str | None = None
    # Qualquer uma destas permissões libera o módulo. Vazio = somente gestão.
    permissoes: tuple[str, ...] = field(default_factory=tuple)
    provedores: tuple[str, ...] = field(default_factory=tuple)
    consultado_pela_ia: bool = False

    def __post_init__(self) -> None:
        if self.status not in STATUS_MODULO:
            raise ValueError(f"status inválido em {self.codigo}: {self.status}")
        if self.categoria not in CATEGORIAS_MODULO:
            raise ValueError(f"categoria inválida em {self.codigo}: {self.categoria}")

    def para_dict(self) -> dict[str, Any]:
        dados = asdict(self)
        dados["permissoes"] = list(self.permissoes)
        dados["provedores"] = list(self.provedores)
        dados["categoria_rotulo"] = CATEGORIAS_MODULO[self.categoria]
        return dados


VER_OPORTUNIDADES = ("oportunidades_visualizar", "oportunidades_editar")

MODULOS: tuple[ModuloPlataforma, ...] = (
    ModuloPlataforma("central", "Central de Inteligência", "Seu dia comercial em uma tela: prioridades, riscos e saúde da carteira.", "inteligencia", "ativo", "/central", "/crm-app/prioridades", VER_OPORTUNIDADES, ("agenda", "pipeline", "pedidos"), True),
    ModuloPlataforma("ia-comercial", "IA Comercial", "Converse com a IA sobre carteira, mercado, ANFIR, produtos e estratégia.", "inteligencia", "ativo", "/ia-comercial", None, VER_OPORTUNIDADES, (), True),
    ModuloPlataforma("clientes", "Clientes e carteiras", "Cadastro, carteira por responsável e histórico de cada conta.", "operacao", "ativo", "/empresas", "/crm-app/clientes", ("clientes_visualizar",), (), True),
    ModuloPlataforma("atividades", "Interações e agenda", "Visitas, ligações e follow-ups com responsável e data.", "operacao", "ativo", "/atividades", "/crm-app/atividades", VER_OPORTUNIDADES, ("agenda",), True),
    ModuloPlataforma("oportunidades", "Oportunidades e pipeline", "Negócios em andamento, etapas e previsão de fechamento.", "operacao", "ativo", "/oportunidades", "/crm-app/oportunidades", VER_OPORTUNIDADES, ("pipeline",), True),
    ModuloPlataforma("propostas", "Propostas", "Emissão, versões, envio e aceite de propostas oficiais.", "operacao", "ativo", "/propostas", "/crm-app/propostas", ("propostas_visualizar",), ("pipeline",), True),
    ModuloPlataforma("pedidos", "Pedidos e pós-venda", "Pedido, dossiê, Carrier e acompanhamento de entrega.", "operacao", "ativo", "/pedidos", "/crm-app/pedidos", ("pedidos_visualizar",), ("pedidos",), True),
    ModuloPlataforma("forecast", "Forecast", "Previsão ponderada por competência e responsável.", "operacao", "ativo", "/forecast", "/crm-app/forecast", VER_OPORTUNIDADES, (), True),
    ModuloPlataforma("vendas", "Vendas", "Negócios ganhos e faturados.", "operacao", "ativo", "/vendas", "/crm-app/vendas", ("dashboard_executivo",), (), True),
    ModuloPlataforma("mapa-estrategico", "Mapa Estratégico", "Mercado por região, linha e concorrente com base ANFIR.", "mercado", "ativo", "/mapa-estrategico", None, VER_OPORTUNIDADES, (), True),
    ModuloPlataforma("feiras", "Feiras e eventos", "Captação de contatos em eventos, inclusive offline.", "mercado", "ativo", "/crm-app/feiras", "/crm-app/feiras", VER_OPORTUNIDADES, (), False),
    ModuloPlataforma("relatorios", "Relatórios", "Relatórios gerenciais e geração modular em PDF.", "inteligencia", "ativo", "/relatorios", "/crm-app/relatorios", ("dashboard_executivo",), (), False),
    ModuloPlataforma("catalogo-produtos", "Catálogo de produtos", "Linhas, modelos e preços oficiais (TR, DT, DD). Hoje administrado em Configurações e consultado pela IA; próxima etapa: vitrine de consulta para a equipe.", "conhecimento", "beta", "/configuracoes", None, ("configuracoes_administrar",), (), True),
    ModuloPlataforma("treinamentos", "Treinamentos comerciais", "Trilhas por produto e etapa de venda, com recomendação do agente a partir das dificuldades observadas no pipeline.", "conhecimento", "planejado", None, None, VER_OPORTUNIDADES, (), False),
)


def _gestao(tipo_usuario: str, permissoes: dict[str, Any]) -> bool:
    return tipo_usuario == "ADMIN_MASTER" or (tipo_usuario == "DIRETOR_VIENA_SP" and bool(permissoes.get("acesso_total")))


def modulo_visivel(modulo: ModuloPlataforma, tipo_usuario: str, permissoes: dict[str, Any]) -> bool:
    if _gestao(tipo_usuario, permissoes):
        return True
    if modulo.status == "planejado":
        return True  # roadmap é visível; não há rota a proteger
    return any(permissoes.get(chave) is True for chave in modulo.permissoes)


def modulos_para_usuario(tipo_usuario: str, permissoes: dict[str, Any], modulos: Iterable[ModuloPlataforma] = MODULOS) -> list[dict[str, Any]]:
    return [m.para_dict() for m in modulos if modulo_visivel(m, tipo_usuario, permissoes or {})]


def obter_modulo(codigo: str) -> ModuloPlataforma | None:
    return next((m for m in MODULOS if m.codigo == codigo), None)
