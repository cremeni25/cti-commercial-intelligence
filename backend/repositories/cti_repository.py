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


def _adaptar_dominio_para_persistencia(registro):

    payload = dict(registro)

    if "implementadora" in payload:
        payload["implementador"] = payload.pop(
            "implementadora"
        )

    return payload


def _adaptar_persistencia_para_dominio(registro):

    payload = dict(registro)

    if "implementador" in payload:
        payload["implementadora"] = payload.pop(
            "implementador"
        )

    return payload


def _valor_preenchido(valor):

    return valor not in (None, "", "nan")


def _mesclar_sem_apagar(existente, novo):

    payload = dict(existente or {})

    for chave, valor in novo.items():

        if _valor_preenchido(valor):
            payload[chave] = valor

    return payload


class CTIRepository:

    TABELA = "cti_anfir"

    # ======================================================
    # CONSULTAS
    # ======================================================

    def buscar_cti_anfir(self):

        registros = (
            supabase
            .table(self.TABELA)
            .select("*")
            .execute()
            .data
            or []
        )

        return [
            _adaptar_persistencia_para_dominio(registro)
            for registro in registros
        ]

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

        return (
            _adaptar_persistencia_para_dominio(dados[0])
            if dados
            else None
        )

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

        return (
            _adaptar_persistencia_para_dominio(dados[0])
            if dados
            else None
        )

    # ======================================================
    # APOIO
    # ======================================================


    def buscar_por_origem(
        self,
        origem_base: str,
        autorizado: str = None
    ):

        consulta = (
            supabase
            .table(self.TABELA)
            .select("*")
            .eq("origem_base", origem_base)
        )

        if autorizado:
            consulta = consulta.eq(
                "autorizado",
                autorizado
            )

        registros = (
            consulta
            .execute()
            .data
            or []
        )

        return [
            _adaptar_persistencia_para_dominio(registro)
            for registro in registros
        ]

    def persistir_registros_idempotente(
        self,
        registros: List[dict]
    ):

        inseridos = 0
        atualizados = 0
        duplicados_ignorados = 0
        erros = 0

        for registro in registros:

            try:

                payload_dominio = dict(registro)
                hash_registro = payload_dominio.get(
                    "hash_registro"
                )

                if not hash_registro:
                    erros += 1
                    continue

                existente = (
                    supabase
                    .table(self.TABELA)
                    .select("*")
                    .eq("hash_registro", hash_registro)
                    .limit(1)
                    .execute()
                    .data
                    or []
                )

                payload = _adaptar_dominio_para_persistencia(
                    payload_dominio
                )

                if existente:
                    legado_existente = existente[0]
                    mesclado = _mesclar_sem_apagar(
                        legado_existente,
                        payload
                    )

                    if mesclado == legado_existente:
                        duplicados_ignorados += 1
                        continue

                    supabase.table(self.TABELA).update(
                        mesclado
                    ).eq(
                        "hash_registro",
                        hash_registro
                    ).execute()
                    atualizados += 1
                    continue

                supabase.table(self.TABELA).insert(
                    payload
                ).execute()
                inseridos += 1

            except Exception:
                erros += 1

        return {
            "inseridos": inseridos,
            "atualizados": atualizados,
            "duplicados_ignorados": duplicados_ignorados,
            "erros": erros,
        }

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

        registros = (
            supabase
            .table(self.TABELA)
            .select("implementador")
            .execute()
            .data
            or []
        )

        return [
            _adaptar_persistencia_para_dominio(registro)
            for registro in registros
        ]


repository = CTIRepository()
