from __future__ import annotations

from datetime import datetime, timezone

from core.supabase_client import supabase

TABELA = "cti_anfir_concorrente_classificacao"


def remover_classificacao(registro_id: str) -> None:
    supabase.table(TABELA).delete().eq("anf_ir_id", registro_id).execute()


def salvar_classificacao(registro_id: str, fabricante: str, observacao: str | None, usuario_id: str) -> None:
    payload = {
        "anf_ir_id": registro_id,
        "fabricante_cti": fabricante,
        "observacao": observacao,
        "alterado_por": usuario_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    supabase.table(TABELA).upsert(payload, on_conflict="anf_ir_id").execute()
