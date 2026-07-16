from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class CTIRecord:

    # ======================================================
    # DADOS TEMPORAIS
    # ======================================================

    ano: Optional[int] = None
    mes: Optional[int] = None
    data_venda: Optional[str] = None

    # ======================================================
    # CLIENTE
    # ======================================================

    cliente: Optional[str] = None
    cnpj: Optional[str] = None

    # ======================================================
    # LOCALIZAÇÃO
    # ======================================================

    cidade: Optional[str] = None
    estado: Optional[str] = None
    ddd: Optional[str] = None
    regiao: Optional[str] = None
    sub_regiao: Optional[str] = None

    # ======================================================
    # VEÍCULO
    # ======================================================

    placa: Optional[str] = None
    chassi: Optional[str] = None

    fabricante_caminhao: Optional[str] = None
    modelo_caminhao: Optional[str] = None

    eixo: Optional[str] = None
    tipo_veiculo: Optional[str] = None

    # ======================================================
    # EQUIPAMENTO
    # ======================================================

    implementadora: Optional[str] = None

    fabricante_equipamento: Optional[str] = None

    linha: Optional[str] = None
    modelo: Optional[str] = None

    # ======================================================
    # OPERAÇÃO
    # ======================================================

    responsavel: Optional[str] = None

    status: Optional[str] = None
    motivo: Optional[str] = None
    ocorrencia: Optional[str] = None

    valor: float = 0.0

    # ======================================================
    # ORIGEM DOS DADOS
    # ======================================================

    origem_dado: Optional[str] = None

    arquivo_origem: Optional[str] = None
    aba_origem: Optional[str] = None

    versao_parser: Optional[str] = None
    pipeline: Optional[str] = None

    created_at: Optional[str] = None

    # ======================================================
    # IDENTIFICAÇÃO
    # ======================================================

    id_operacional: Optional[str] = None
    hash_registro: Optional[str] = None

    ativo: bool = True

    # ======================================================
    # IA / SCORE
    # ======================================================

    score_operacional: Optional[float] = None
    score_comercial: Optional[float] = None

    classificacao: Optional[str] = None

    prioridade: Optional[str] = None
    nivel_risco: Optional[str] = None

    # ======================================================
    # CONVERSORES
    # ======================================================

    @classmethod
    def from_dict(cls, dados: dict):

        return cls(**dados)

    def to_dict(self):

        return asdict(self)
