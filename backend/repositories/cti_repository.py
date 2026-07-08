# ============================================================
# CTI - COMMERCIAL INTELLIGENCE
# Arquivo......: cti_repository.py
# Versão.......: 2.1.0
# Status.......: OFICIAL
#
# Responsabilidade:
# - Centralizar consultas ao banco
# - Não possuir regra de negócio
# - Não conhecer Engine
# - Não conhecer Router
# - Não conhecer IA
#
# Única responsabilidade:
# Consulta aos dados persistidos.
# ============================================================

from typing import List

from core.supabase_client import supabase


class CTIRepository:

    TABELA = "cti_anfir"

    # ======================================================
    # CONSULTAS
    # ======================================================

    def buscar_cti_anfir(self):

        return (
            supabase
            .table(self.TABELA)
            .select("*")
            .execute()
            .data
            or []
        )

    def buscar_ids_existentes(
        self,
        ids_operacionais: List[str],
        batch_size: int = 50
    ):

        if not ids_operacionais:
            return set()

        ids_existentes = set()

        ids_operacionais = [
            str(i)
            for i in ids_operacionais
            if i not in (None, "")
        ]

        for inicio in range(
            0,
            len(ids_operacionais),
            batch_size
        ):

            lote = ids_operacionais[
                inicio:inicio + batch_size
            ]

            resultado = (
                supabase
                .table(self.TABELA)
                .select("id_operacional")
                .in_(
                    "id_operacional",
                    lote
                )
                .execute()
            )

            ids_existentes.update(

                item["id_operacional"]

                for item in (
                    resultado.data or []
                )

            )

        return ids_existentes

    def buscar_hashes_existentes(
        self,
        hashes: List[str],
        batch_size: int = 50
    ):

        if not hashes:
            return set()

        hashes_existentes = set()

        hashes = [
            str(h)
            for h in hashes
            if h not in (None, "")
        ]

        for inicio in range(
            0,
            len(hashes),
            batch_size
        ):

            lote = hashes[
                inicio:inicio + batch_size
            ]

            resultado = (
                supabase
                .table(self.TABELA)
                .select("hash_registro")
                .in_(
                    "hash_registro",
                    lote
                )
                .execute()
            )

            hashes_existentes.update(

                item["hash_registro"]

                for item in (
                    resultado.data or []
                )

            )

        return hashes_existentes

    def buscar_por_id_operacional(
        self,
        id_operacional: str
    ):

        resultado = (
            supabase
            .table(self.TABELA)
            .select("*")
            .eq(
                "id_operacional",
                str(id_operacional)
            )
            .limit(1)
            .execute()
        )

        dados = resultado.data or []

        return dados[0] if dados else None

    def buscar_por_hash(
        self,
        hash_registro: str
    ):

        resultado = (
            supabase
            .table(self.TABELA)
            .select("*")
            .eq(
                "hash_registro",
                str(hash_registro)
            )
            .limit(1)
            .execute()
        )

        dados = resultado.data or []

        return dados[0] if dados else None

    # ======================================================
    # APOIO
    # ======================================================

    def listar_clientes(self):

        return (
            supabase
            .table(self.TABELA)
            .select("cliente")
            .execute()
            .data
            or []
        )

    def listar_implementadoras(self):

        return (
            supabase
            .table(self.TABELA)
            .select("implementador")
            .execute()
            .data
            or []
        )


repository = CTIRepository()