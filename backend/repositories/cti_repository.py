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

import traceback

from core.supabase_client import supabase
from core.cti_taxonomy import normalizar_implementadora


COLUNAS_LEGADAS_CTI_ANFIR = {
    "ano", "mes", "data_venda", "cliente", "cnpj", "cidade", "estado",
    "ddd", "regiao", "sub_regiao", "placa", "chassi",
    "fabricante_caminhao", "modelo_caminhao", "eixo", "tipo_veiculo",
    "implementador", "fabricante_equipamento", "linha", "modelo",
    "responsavel", "status", "motivo", "ocorrencia", "valor",
    "origem_dado", "arquivo_origem", "aba_origem", "versao_parser",
    "pipeline", "created_at", "id_operacional", "hash_registro", "ativo",
    "score_operacional", "score_comercial", "classificacao", "prioridade",
    "nivel_risco",
}


def _adaptar_dominio_para_persistencia(registro):

    payload = dict(registro)

    if "empresa" in payload and not payload.get("cliente"):
        payload["cliente"] = payload.pop("empresa")

    if "implementadora" in payload:
        payload["implementador"] = normalizar_implementadora(
            payload.pop("implementadora")
        )

    return payload


def _inferir_origem(registro):

    origem = registro.get("origem_base") or registro.get("origem_dado")
    aba = str(registro.get("aba_origem") or "").upper()

    if origem in ("BRASIL", "VIENA_SP"):
        origem_base = origem
    elif "VIENA SP" in aba:
        origem_base = "VIENA_SP"
    elif "BRASIL" in aba:
        origem_base = "BRASIL"
    else:
        origem_base = origem

    autorizado = registro.get("autorizado")
    ano_referencia = registro.get("ano_referencia")
    escopo = registro.get("escopo_operacional")

    if origem_base == "VIENA_SP":
        autorizado = autorizado or "VIENA"
        escopo = escopo or "AUTORIZADO"
        if not ano_referencia:
            if "2025" in aba:
                ano_referencia = 2025
            elif "2026" in aba:
                ano_referencia = 2026
    elif origem_base == "BRASIL":
        escopo = escopo or "NACIONAL"

    return origem_base, autorizado, ano_referencia, escopo


def _adaptar_persistencia_para_dominio(registro):

    payload = dict(registro)

    if "implementador" in payload:
        payload["implementadora"] = normalizar_implementadora(
            payload.pop("implementador")
        )

    origem_base, autorizado, ano_referencia, escopo = _inferir_origem(
        payload
    )

    payload["empresa"] = payload.get("empresa") or payload.get("cliente")
    payload["tipo_empresa"] = payload.get("tipo_empresa")

    payload["origem_base"] = origem_base
    payload["autorizado"] = autorizado
    payload["ano_referencia"] = ano_referencia
    payload["escopo_operacional"] = escopo

    return payload


def _filtrar_colunas_legadas(payload):

    return {
        chave: valor
        for chave, valor in payload.items()
        if chave in COLUNAS_LEGADAS_CTI_ANFIR
    }


def _classificar_erro_persistencia(erro):

    mensagem = str(erro)
    texto = mensagem.lower()

    if "column" in texto or "schema" in texto or "could not find" in texto:
        return "schema_incompativel"

    if "jwt" in texto or "auth" in texto or "permission" in texto:
        return "erro_autenticacao"

    if "connection" in texto or "timeout" in texto or "network" in texto:
        return "erro_rede"

    return "erro_persistencia"


def _erro_payload(registro, etapa, tipo, mensagem, campo=None, valor=None):

    return {
        "linha": registro.get("linha_planilha"),
        "aba": registro.get("aba_origem"),
        "etapa": etapa,
        "tipo": tipo,
        "mensagem": mensagem,
        "campo": campo,
        "valor": valor,
        "hash_registro": registro.get("hash_registro"),
        "origem_base": registro.get("origem_base"),
    }

def _valor_preenchido(valor):

    return valor not in (None, "", "nan")


def _mesclar_sem_apagar(existente, novo):

    payload = dict(existente or {})

    for chave, valor in novo.items():

        if _valor_preenchido(valor):
            payload[chave] = valor

    return payload



def _registrar_erro(resultado, erro):

    resultado["erros"] += 1
    tipo = erro.get("tipo") or "outros"

    if tipo not in resultado["erros_por_tipo"]:
        tipo = "outros"

    resultado["erros_por_tipo"][tipo] += 1

    if len(resultado["amostra_erros"]) < 100:
        resultado["amostra_erros"].append(erro)


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

        registros = self.buscar_cti_anfir()

        return [
            registro
            for registro in registros
            if registro.get("origem_base") == origem_base
            and (
                autorizado is None
                or registro.get("autorizado") == autorizado
            )
        ]

    def persistir_registros_idempotente(
        self,
        registros: List[dict]
    ):

        resultado = {
            "tentados": len(registros),
            "inseridos": 0,
            "atualizados": 0,
            "duplicados_ignorados": 0,
            "erros": 0,
            "erros_por_tipo": {
                "campo_invalido": 0,
                "registro_sem_identificador": 0,
                "schema_incompativel": 0,
                "erro_persistencia": 0,
                "erro_autenticacao": 0,
                "erro_rede": 0,
                "outros": 0,
            },
            "amostra_erros": [],
        }

        for registro in registros:

            payload_dominio = dict(registro)
            hash_registro = payload_dominio.get(
                "hash_registro"
            )

            if not hash_registro:
                erro = _erro_payload(
                    payload_dominio,
                    "validacao",
                    "registro_sem_identificador",
                    "Registro sem hash_registro.",
                    "hash_registro",
                    None
                )
                _registrar_erro(resultado, erro)
                continue

            try:
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
                payload = _filtrar_colunas_legadas(payload)

                if existente:
                    legado_existente = existente[0]
                    mesclado = _mesclar_sem_apagar(
                        legado_existente,
                        payload
                    )
                    mesclado = _filtrar_colunas_legadas(mesclado)

                    if mesclado == _filtrar_colunas_legadas(legado_existente):
                        resultado["duplicados_ignorados"] += 1
                        continue

                    supabase.table(self.TABELA).update(
                        mesclado
                    ).eq(
                        "hash_registro",
                        hash_registro
                    ).execute()
                    resultado["atualizados"] += 1
                    continue

                supabase.table(self.TABELA).insert(
                    payload
                ).execute()
                resultado["inseridos"] += 1

            except Exception as erro:
                traceback.print_exc()
                print(
                    "ERRO_PERSISTENCIA",
                    {
                        "hash_registro": hash_registro,
                        "aba_origem": payload_dominio.get("aba_origem"),
                        "origem_base": payload_dominio.get("origem_base"),
                        "mensagem": str(erro),
                    }
                )
                tipo = _classificar_erro_persistencia(erro)
                erro_payload = _erro_payload(
                    payload_dominio,
                    "persistencia",
                    tipo,
                    str(erro)
                )
                _registrar_erro(resultado, erro_payload)

        return resultado

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
