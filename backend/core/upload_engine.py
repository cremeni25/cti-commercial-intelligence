# ============================================================
# CTI - COMMERCIAL INTELLIGENCE
# Arquivo......: upload_engine.py
# Versão.......: 1.1.0
# Status.......: ESTÁVEL
# Data.........: 24/06/2026
#
# Responsabilidade:
# - Receber registros prontos
# - Eliminar duplicados do lote
# - Inserir em batches
# - Retornar estatísticas da carga
#
# OBS:
# Não possui regra de negócio.
# Não conhece ANFIR, VIENA, Carrier ou qualquer parser.
# ============================================================

from typing import List, Dict

from supabase import create_client

import os

import time


class UploadEngine:

    def __init__(self):

        self.supabase = create_client(

            os.getenv("SUPABASE_URL"),

            os.getenv("SUPABASE_KEY")

        )

    # ======================================================
    # REMOVE DUPLICADOS DO LOTE
    # ======================================================

    def remover_duplicados(

        self,

        registros: List[Dict]

    ) -> List[Dict]:

        vistos = set()

        resultado = []

        for registro in registros:

            chave = registro.get("hash_registro")

            if not chave:

                resultado.append(registro)

                continue

            if chave in vistos:

                continue

            vistos.add(chave)

            resultado.append(registro)

        return resultado

    # ======================================================
    # VALIDA REGISTROS
    # ======================================================

    def validar_registros(

        self,

        registros: List[Dict]

    ) -> List[Dict]:

        validos = []

        for registro in registros:

            if not isinstance(registro, dict):

                continue

            validos.append(registro)

        return validos

    # ======================================================
    # INSERÇÃO EM LOTES
    # ======================================================

    def inserir_batches(

    self,

    tabela: str,

    registros: List[Dict],

    batch_size: int = 500

):

    inseridos = 0

    batches = 0

    duplicados = 0

    for inicio in range(

        0,

        len(registros),

        batch_size

    ):

        lote = registros[
            inicio:inicio + batch_size
        ]

        try:

            print("=" * 80)
            print("TABELA:", tabela)
            print("PRIMEIRO REGISTRO:")
            print(lote[0])
            print("=" * 80)

            ids_lote = [

                r["id_operacional"]

                for r in lote

                if r.get("id_operacional")

            ]

            existentes = (

                self.supabase

                    .table(tabela)

                    .select("id_operacional")

                    .in_("id_operacional", ids_lote)

                    .execute()

            )

            ids_existentes = {

                r["id_operacional"]

                for r in (existentes.data or [])

            }

            novos = [

                r

                for r in lote

                if r.get("id_operacional") not in ids_existentes

            ]

            duplicados += len(lote) - len(novos)

            if novos:

                self.supabase.table(

                    tabela

                ).insert(

                    novos

                ).execute()

                inseridos += len(novos)

            batches += 1

        except Exception as erro:

            raise Exception(

                f"Erro ao inserir lote {batches + 1}: {erro}"

            )

    return {

        "batches": batches,

        "inseridos": inseridos,

        "duplicados": duplicados

    }

    # ======================================================
    # PROCESSAMENTO COMPLETO
    # ======================================================

    def processar(

        self,

        tabela: str,

        registros: List[Dict]

    ):

        inicio = time.time()

        total_recebidos = len(registros)

        registros = self.validar_registros(
            registros
        )

        registros = self.remover_duplicados(
            registros
        )

        total_unicos = len(registros)

        resultado_insert = self.inserir_batches(

            tabela,

            registros

        )

        tempo = round(

            time.time() - inicio,

            2

        )

        return {

            "status": "SUCESSO",

            "recebidos": total_recebidos,

            "validos": total_unicos,

            "duplicados_lote":

                total_recebidos - total_unicos,

            "batches":

                resultado_insert["batches"],

            "inseridos":

                resultado_insert["inseridos"],

            "duplicados_banco":

                resultado_insert["duplicados"],

            "tempo_execucao":

                tempo