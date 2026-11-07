"""Modelo de sinais e registro de provedores do Agente de Inteligência Comercial.

Um *sinal* é uma constatação objetiva sobre a operação comercial (um
follow-up atrasado, uma proposta sem retorno, um dado faltante) acompanhada
da explicação, da evidência e da ação recomendada. Sinais nunca alteram
registros: o agente apenas lê o núcleo comercial e devolve a leitura.

Cada módulo da plataforma pode contribuir com seus próprios sinais
registrando um *provedor*. É assim que módulos futuros (catálogo de
produtos, treinamentos comerciais, feiras...) passam a alimentar a mesma
devolutiva sem que o briefing precise ser reescrito:

    from services.inteligencia_comercial import registrar_provedor, Sinal

    @registrar_provedor("treinamento_pendente", modulo="treinamentos")
    def _treinamentos(contexto):
        return [Sinal(...)]

Um provedor que falha não derruba o briefing: a falha é registrada em
``provedores`` e os demais sinais continuam disponíveis.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
import math
from typing import Any, Callable

CATEGORIAS = ("acao", "risco", "oportunidade", "qualidade")
SEVERIDADES = ("critica", "alta", "media", "baixa")
PESO_SEVERIDADE = {"critica": 100.0, "alta": 70.0, "media": 40.0, "baixa": 15.0}


@dataclass(frozen=True)
class Sinal:
    codigo: str
    categoria: str
    severidade: str
    titulo: str
    explicacao: str
    acao_recomendada: str
    entidade_tipo: str
    entidade_id: str
    cliente_nome: str = ""
    responsavel_id: str = ""
    valor: float = 0.0
    dias: int | None = None
    rota: str = ""
    rota_app: str = ""
    evidencias: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.categoria not in CATEGORIAS:
            raise ValueError(f"categoria inválida: {self.categoria}")
        if self.severidade not in SEVERIDADES:
            raise ValueError(f"severidade inválida: {self.severidade}")

    @property
    def pontuacao(self) -> float:
        """Prioridade = gravidade + peso do valor em jogo + tempo parado.

        O valor entra em escala logarítmica para que um negócio grande não
        esconda todo o resto, e o tempo é limitado a 60 dias.
        """
        peso_valor = math.log10(max(self.valor, 0.0) + 1.0) * 6.0
        peso_tempo = min(max(self.dias or 0, 0), 60) / 2.0
        return round(PESO_SEVERIDADE[self.severidade] + peso_valor + peso_tempo, 2)

    def para_dict(self) -> dict[str, Any]:
        dados = asdict(self)
        dados["evidencias"] = list(self.evidencias)
        dados["pontuacao"] = self.pontuacao
        return dados


@dataclass
class ContextoInteligencia:
    """Dados já filtrados pelo escopo do usuário e entregues aos provedores."""

    hoje: date
    oportunidades: list[dict[str, Any]]
    atividades: list[dict[str, Any]]
    extras: dict[str, Any] = field(default_factory=dict)

    # Índices calculados uma única vez e compartilhados entre provedores.
    _atividades_por_oportunidade: dict[str, list[dict[str, Any]]] | None = None

    def atividades_da_oportunidade(self, oportunidade_id: str) -> list[dict[str, Any]]:
        if self._atividades_por_oportunidade is None:
            indice: dict[str, list[dict[str, Any]]] = {}
            for atividade in self.atividades:
                oid = texto(atividade.get("oportunidade_id"))
                if oid:
                    indice.setdefault(oid, []).append(atividade)
            self._atividades_por_oportunidade = indice
        return self._atividades_por_oportunidade.get(oportunidade_id, [])


Provedor = Callable[[ContextoInteligencia], list[Sinal]]


@dataclass(frozen=True)
class RegistroProvedor:
    codigo: str
    modulo: str
    descricao: str
    funcao: Provedor


_PROVEDORES: dict[str, RegistroProvedor] = {}


def registrar_provedor(codigo: str, *, modulo: str, descricao: str = "") -> Callable[[Provedor], Provedor]:
    def decorar(funcao: Provedor) -> Provedor:
        _PROVEDORES[codigo] = RegistroProvedor(codigo, modulo, descricao or (funcao.__doc__ or "").strip(), funcao)
        return funcao

    return decorar


def provedores_registrados() -> list[RegistroProvedor]:
    return list(_PROVEDORES.values())


def remover_provedor(codigo: str) -> None:
    _PROVEDORES.pop(codigo, None)


# --- utilidades compartilhadas -------------------------------------------------

STATUS_ATIVIDADE_FINAL = {"CONCLUIDA", "CONCLUÍDA", "CONCLUIDO", "CONCLUÍDO", "CANCELADA", "CANCELADO", "ARQUIVADA"}


def texto(valor: Any) -> str:
    return str(valor or "").strip()


def status(valor: Any) -> str:
    return texto(valor).upper().replace(" ", "_")


def numero(valor: Any) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def data(valor: Any) -> date | None:
    bruto = texto(valor)
    if not bruto:
        return None
    try:
        return datetime.fromisoformat(bruto.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(bruto[:10])
        except ValueError:
            return None


def atividade_pendente(atividade: dict[str, Any]) -> bool:
    if atividade.get("arquivado_em") or atividade.get("arquivada_em"):
        return False
    return status(atividade.get("status") or "PENDENTE") not in STATUS_ATIVIDADE_FINAL
