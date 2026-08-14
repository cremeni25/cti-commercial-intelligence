"""HIST-004 - reconciliador read-only do histórico comercial.

Não acessa banco, não grava staging e não promove registros. Recebe candidatos já
carregados pelo chamador e devolve decisões determinísticas em memória.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
import re
from typing import Any, Iterable, Mapping, Sequence

from services.historical_normalization import clean, fold

VALID_STATUSES = {"RECONCILIADO", "AMBIGUO", "NAO_ENCONTRADO"}


def only_digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def valid_cnpj(value: Any) -> bool:
    digits = only_digits(value)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False
    weights1 = (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    weights2 = (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)
    nums = [int(x) for x in digits]

    def dv(base, weights):
        rem = sum(n * w for n, w in zip(base, weights)) % 11
        return 0 if rem < 2 else 11 - rem

    d1 = dv(nums[:12], weights1)
    d2 = dv(nums[:12] + [d1], weights2)
    return nums[12:] == [d1, d2]


def key(value: Any) -> str:
    text = fold(value)
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


@dataclass(frozen=True)
class Candidate:
    id: str | None
    nome: str
    cnpj: str | None = None
    codigo: str | None = None
    aliases: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Candidate":
        aliases = value.get("aliases") or ()
        return cls(
            id=str(value["id"]) if value.get("id") is not None else None,
            nome=clean(value.get("nome") or value.get("name") or value.get("codigo")) or "",
            cnpj=clean(value.get("cnpj")),
            codigo=clean(value.get("codigo")),
            aliases=tuple(clean(x) for x in aliases if clean(x)),
        )


@dataclass(frozen=True)
class ReconciliationResult:
    entidade_tipo: str
    valor_original: str | None
    valor_normalizado: str | None
    status: str
    candidato_id: str | None = None
    candidato_nome: str | None = None
    metodo: str | None = None
    confianca: float = 0.0
    candidatos: tuple[dict[str, Any], ...] = ()
    flags: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _coerce_candidates(values: Iterable[Candidate | Mapping[str, Any]]) -> list[Candidate]:
    return [value if isinstance(value, Candidate) else Candidate.from_mapping(value) for value in values]


def _candidate_names(candidate: Candidate) -> tuple[str, ...]:
    values = [candidate.nome, candidate.codigo, *candidate.aliases]
    return tuple(dict.fromkeys(key(v) for v in values if clean(v)))


def _score(value: str, candidate: Candidate) -> float:
    if not value:
        return 0.0
    names = _candidate_names(candidate)
    if value in names:
        return 1.0
    return max((SequenceMatcher(None, value, n).ratio() for n in names), default=0.0)


def _equipment_identity(value: Any) -> tuple[str, str | None]:
    """Extrai família e identificador de modelo sem reduzir configuração histórica.

    Ex.: CITIMAX 700 -> (CITIMAX, 700), CITIMAX 500 -> (CITIMAX, 500).
    Modelos numericamente distintos não podem virar ambíguos só por similaridade textual.
    """
    tokens = key(value).split()
    family = tokens[0] if tokens else ""
    model = next((token for token in tokens[1:] if any(ch.isdigit() for ch in token)), None)
    return family, model


def reconcile(
    entidade_tipo: str,
    valor_original: Any,
    valor_normalizado: Any,
    candidates: Iterable[Candidate | Mapping[str, Any]],
    *,
    cnpj_original: Any = None,
    exact_only: bool = False,
    fuzzy_accept: float = 0.92,
    fuzzy_ambiguous: float = 0.80,
    min_margin: float = 0.05,
) -> ReconciliationResult:
    """Reconcilia sem efeitos colaterais.

    Hierarquia: CNPJ válido exato > nome/código/alias exato > fuzzy conservador.
    Fuzzy nunca decide quando os dois melhores candidatos ficam próximos.
    """
    tipo = key(entidade_tipo).replace(" ", "_")
    original = clean(valor_original)
    normalized = clean(valor_normalizado)
    pool = _coerce_candidates(candidates)
    if not normalized:
        return ReconciliationResult(tipo, original, normalized, "NAO_ENCONTRADO", flags=("VALOR_NORMALIZADO_AUSENTE",))

    cnpj = only_digits(cnpj_original)
    if cnpj and valid_cnpj(cnpj):
        matches = [c for c in pool if valid_cnpj(c.cnpj) and only_digits(c.cnpj) == cnpj]
        if len(matches) == 1:
            c = matches[0]
            return ReconciliationResult(tipo, original, normalized, "RECONCILIADO", c.id, c.nome, "CNPJ_EXATO", 1.0)
        if len(matches) > 1:
            return ReconciliationResult(
                tipo, original, normalized, "AMBIGUO", metodo="CNPJ_DUPLICADO", confianca=1.0,
                candidatos=tuple({"id": c.id, "nome": c.nome, "score": 1.0} for c in matches),
                flags=("CNPJ_DUPLICADO_NO_CATALOGO",),
            )

    lookup = key(normalized)
    exact = [c for c in pool if lookup in _candidate_names(c)]
    if len(exact) == 1:
        c = exact[0]
        return ReconciliationResult(tipo, original, normalized, "RECONCILIADO", c.id, c.nome, "EXATO_NORMALIZADO", 1.0)
    if len(exact) > 1:
        return ReconciliationResult(
            tipo, original, normalized, "AMBIGUO", metodo="EXATO_MULTIPLO", confianca=1.0,
            candidatos=tuple({"id": c.id, "nome": c.nome, "score": 1.0} for c in exact),
            flags=("MULTIPLOS_CANDIDATOS_EXATOS",),
        )
    if exact_only:
        return ReconciliationResult(tipo, original, normalized, "NAO_ENCONTRADO", metodo="EXATO_SEM_MATCH", confianca=0.0)

    ranked = sorted(((_score(lookup, c), c) for c in pool), key=lambda x: (-x[0], x[1].nome, x[1].id or ""))
    if not ranked or ranked[0][0] < fuzzy_ambiguous:
        return ReconciliationResult(tipo, original, normalized, "NAO_ENCONTRADO", metodo="FUZZY_ABAIXO_LIMIAR", confianca=ranked[0][0] if ranked else 0.0)

    best_score, best = ranked[0]
    second_score = ranked[1][0] if len(ranked) > 1 else 0.0
    evidence = tuple({"id": c.id, "nome": c.nome, "score": round(score, 6)} for score, c in ranked[:3] if score >= fuzzy_ambiguous)
    if best_score >= fuzzy_accept and best_score - second_score >= min_margin:
        return ReconciliationResult(tipo, original, normalized, "RECONCILIADO", best.id, best.nome, "FUZZY_ALTA_CONFIANCA", best_score, evidence)
    return ReconciliationResult(
        tipo, original, normalized, "AMBIGUO", metodo="FUZZY_REVISAO_HUMANA", confianca=best_score,
        candidatos=evidence, flags=("RECONCILIACAO_REQUER_REVISAO",),
    )


def reconcile_cliente(original: Any, normalized: Any, candidates: Iterable, cnpj_original: Any = None) -> ReconciliationResult:
    return reconcile("CLIENTE", original, normalized, candidates, cnpj_original=cnpj_original, fuzzy_accept=0.94, fuzzy_ambiguous=0.84, min_margin=0.06)


def reconcile_representante(original: Any, normalized: Any, candidates: Iterable) -> ReconciliationResult:
    if clean(normalized) == "VIENA SP":
        return ReconciliationResult(
            "REPRESENTANTE", clean(original), clean(normalized), "AMBIGUO",
            metodo="RESPONSAVEL_HISTORICO_NAO_INDIVIDUALIZADO", confianca=0.0,
            flags=("REPRESENTANTE_NAO_INDIVIDUALIZADO",),
        )
    return reconcile("REPRESENTANTE", original, normalized, candidates, exact_only=True)


def reconcile_equipamento(original: Any, normalized: Any, candidates: Iterable) -> ReconciliationResult:
    """Equipamento histórico só reconcilia automaticamente por identidade de modelo.

    Após tentar o match exato normalizado, qualquer diferença explícita de identificador
    de modelo dentro da mesma família é preservada como NAO_ENCONTRADO. Isso evita que
    CITIMAX 700 seja confundido/ambíguo com CITIMAX 500 apenas pela proximidade textual.
    """
    pool = _coerce_candidates(candidates)
    exact_result = reconcile("EQUIPAMENTO", original, normalized, pool, exact_only=True)
    if exact_result.status != "NAO_ENCONTRADO":
        return exact_result

    family, model = _equipment_identity(normalized)
    if family and model:
        same_family = []
        for candidate in pool:
            candidate_family, candidate_model = _equipment_identity(candidate.nome or candidate.codigo)
            if candidate_family == family:
                same_family.append((candidate_model, candidate))
        if same_family and all(candidate_model != model for candidate_model, _ in same_family if candidate_model):
            return ReconciliationResult(
                "EQUIPAMENTO", clean(original), clean(normalized), "NAO_ENCONTRADO",
                metodo="MODELO_HISTORICO_FORA_CATALOGO", confianca=0.0,
                flags=("EQUIPAMENTO_HISTORICO_NAO_CATALOGADO",),
            )

    return reconcile("EQUIPAMENTO", original, normalized, pool, fuzzy_accept=0.98, fuzzy_ambiguous=0.94, min_margin=0.08)


def reconcile_implementadora(original: Any, normalized: Any, candidates: Iterable) -> ReconciliationResult:
    if original and "/" in str(original) and not normalized:
        return ReconciliationResult(
            "IMPLEMENTADORA", clean(original), clean(normalized), "AMBIGUO",
            metodo="IMPLEMENTADORA_COMPOSTA", confianca=0.0,
            flags=("IMPLEMENTADORA_COMPOSTA_AMBIGUA",),
        )
    return reconcile("IMPLEMENTADORA", original, normalized, candidates, fuzzy_accept=0.96, fuzzy_ambiguous=0.88, min_margin=0.07)


def reconcile_record(record: Any, normalized: Any, catalogs: Mapping[str, Sequence[Candidate | Mapping[str, Any]]]) -> dict[str, ReconciliationResult]:
    return {
        "cliente": reconcile_cliente(
            getattr(record, "cliente_original", None),
            getattr(normalized, "cliente_normalizado", None),
            catalogs.get("clientes", ()),
            getattr(record, "cnpj_original", None),
        ),
        "representante": reconcile_representante(
            getattr(record, "representante_original", None),
            getattr(normalized, "representante_normalizado", None),
            catalogs.get("representantes", ()),
        ),
        "equipamento": reconcile_equipamento(
            getattr(record, "equipamento_original", None),
            getattr(normalized, "equipamento_normalizado", None),
            catalogs.get("equipamentos", ()),
        ),
        "implementadora": reconcile_implementadora(
            getattr(record, "implementadora_original", None),
            getattr(normalized, "implementadora_normalizada", None),
            catalogs.get("implementadoras", ()),
        ) if getattr(normalized, "canal_venda", "DIRETA") == "INDIRETA_OEM" else ReconciliationResult(
            "IMPLEMENTADORA", None, None, "NAO_ENCONTRADO", metodo="NAO_APLICAVEL_CANAL_DIRETO",
            confianca=1.0, flags=("NAO_APLICAVEL",),
        ),
    }
