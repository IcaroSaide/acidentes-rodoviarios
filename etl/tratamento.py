import warnings

import janitor
import pandas as pd
import numpy as np

from config import diretorios
from etl.de_para import (
    veiculos,
    vitimas,
    concessionarias,
    sentidos,
    causa,
    clima,
)
from etl.de_para import (
    visibilidade,
    classe,
    subclasse,
    local,
    pista_perfil,
)

warnings.filterwarnings("ignore")

class TratarDados:
    def __init__(
        self,
        df_acidentes: pd.DataFrame,
        df_veiculos: pd.DataFrame,
        df_vitimas: pd.DataFrame,
    ):
        self.df_acidentes = df_acidentes
        self.df_veiculos = df_veiculos
        self.df_vitimas = df_vitimas

        self.dir_dados_auxiliares = diretorios.DIR_DADOS_AUXILIARES

    def preparar_veiculos(self) -> pd.DataFrame:
        # Remove nulos e vazios
        self.df_veiculos = self.df_veiculos.dropna(
            subset=["Desc_Grupo_Veic_Concessionaria"]
        )

        self.df_veiculos = self.df_veiculos[
            self.df_veiculos["Desc_Grupo_Veic_Concessionaria"] != ""
        ]

        # Normaliza nomes
        self.df_veiculos["Desc_Grupo_Veic_Concessionaria"] = (
            self.df_veiculos["Desc_Grupo_Veic_Concessionaria"]
            .str.upper()
            .str.strip()
            .replace(veiculos.map_veiculos)
        )

        # Agrupa e conta
        df_grouped = (
            self.df_veiculos.groupby(
                [
                    "Cod_Concessionaria",
                    "Num_Ocorrencia",
                    "Desc_Grupo_Veic_Concessionaria",
                ]
            )
            .size()
            .reset_index(name="QUANTIDADE")
        )

        # Cria coluna "VEÍCULO=QUANTIDADE"
        df_grouped["VEICULOS_ENVOLVIDOS"] = (
            df_grouped["Desc_Grupo_Veic_Concessionaria"]
            + "="
            + df_grouped["QUANTIDADE"].astype(str)
        )

        # Retorna o consolidado por ocorrência
        return (
            df_grouped.groupby(["Cod_Concessionaria", "Num_Ocorrencia"])[
                "VEICULOS_ENVOLVIDOS"
            ]
            .apply("|".join)
            .reset_index()
        )

    def preparar_vitimas(self) -> pd.DataFrame:
        # Mapeia situação da vítima
        self.df_vitimas["Cod_Situacao"] = (
            self.df_vitimas["Cod_Situacao"].astype("Int64").map(vitimas.map_vitimas)
        )

        # Pivot para contar vítimas por gravidade
        return self.df_vitimas.pivot_table(
            index=["Cod_Concessionaria", "Num_Ocorrencia"],
            columns="Cod_Situacao",
            aggfunc="size",
            fill_value=0,
        ).reset_index()

    def merge_veiculos_vitimas(self) -> None:
        self.df_acidentes = self.df_acidentes.merge(
            self.df_veiculos,
            on=["Cod_Concessionaria", "Num_Ocorrencia"],
            how="left",
        ).merge(
            self.df_vitimas,
            on=["Cod_Concessionaria", "Num_Ocorrencia"],
            how="left",
        )

    def ajusta_coordenadas(self) -> None:
        df_coords = pd.read_csv(self.dir_dados_auxiliares / "coords.csv")

        df_coords = df_coords.astype(
            {
                "LAT": "float64",
                "LON": "float64",
                "RODOVIA": str,
                "KM": int,
                "LOTE": str,
            }
        )

        self.df_acidentes = self.df_acidentes.merge(
            df_coords[["RODOVIA", "KM", "LAT", "LON"]],
            left_on=["Nome_Reduzido_Rodovia", "Num_Km"],
            right_on=["RODOVIA", "KM"],
            how="left",
        )

        self.df_acidentes["Cod_Latitude"] = np.where(
            (
                self.df_acidentes["Cod_Latitude"].isna()
                | (self.df_acidentes["Cod_Latitude"] == "NÃO INFORMADO")
            ),
            self.df_acidentes["LAT"],
            self.df_acidentes["Cod_Latitude"],
        )

        self.df_acidentes["Cod_Longitude"] = np.where(
            (
                self.df_acidentes["Cod_Longitude"].isna()
                | (self.df_acidentes["Cod_Longitude"] == "NÃO INFORMADO")
            ),
            self.df_acidentes["LON"],
            self.df_acidentes["Cod_Longitude"],
        )

        # Atualiza o DataFrame da classe
        self.df_acidentes = self.df_acidentes.drop(
            columns=["RODOVIA", "KM", "LON", "LAT"]
        )

    def criar_colunas(self) -> None:
        self.df_acidentes[["Num_Km", "Qtd_Complemento"]] = (
            self.df_acidentes[["Num_Km", "Qtd_Complemento"]].fillna(0).astype("Int64")
        )

        self.df_acidentes["KM"] = (
            self.df_acidentes["Num_Km"].astype(str)
            + "."
            + self.df_acidentes["Qtd_Complemento"].astype(str)
        ).astype(float)

        self.df_acidentes["RODOVIA_KM"] = (
            self.df_acidentes["Nome_Reduzido_Rodovia"]
            + " KM "
            + self.df_acidentes["Num_Km"].astype(str)
        )

        self.df_acidentes["FERIDOS"] = (
            self.df_acidentes["LEVE"]
            + self.df_acidentes["MODERADA"]
            + self.df_acidentes["GRAVE"]
        ).fillna(0)

        condicoes = [
            self.df_acidentes["FATAL"] > 0,
            ((self.df_acidentes["FERIDOS"] > 0) & (self.df_acidentes["FATAL"] == 0)),
        ]

        categorias = [
            "ACIDENTE FATAL",
            "ACIDENTE COM FERIDOS",
        ]

        self.df_acidentes["CATEGORIA"] = np.select(
            condicoes,
            categorias,
            default="ACIDENTE SEM VITIMAS",
        )

        self.df_acidentes["ID_EXTENSAO"] = (
            self.df_acidentes["Cod_Concessionaria"].astype(str).str[1:3]
            + "_"
            + self.df_acidentes["Nome_Reduzido_Rodovia"].astype(str)
        )

    def join_rodovias(self) -> None:
        # Faz join condicional com dados auxiliares de rodovias
        df_rodovias = pd.read_excel(
            self.dir_dados_auxiliares / "CCI_MALHA_RODOVIARIA_SP.xlsx",
            sheet_name="MALHA_RODOVIARIA_SP",
        )

        df_rodovias[["KM_INICIAL", "KM_FINAL"]] = df_rodovias[
            ["KM_INICIAL", "KM_FINAL"]
        ].astype("float64")

        df_rodovias["RODOVIA"] = df_rodovias["RODOVIA"].str.replace(" ", "")

        self.df_acidentes = self.df_acidentes.conditional_join(
            df_rodovias,
            ("Nome_Reduzido_Rodovia", "RODOVIA", "=="),
            ("KM", "KM_INICIAL", ">="),
            ("KM", "KM_FINAL", "<="),
            right_columns=[
                "MUNICIPIO",
                "JURISDICAO",
                "REGIONAL_DER",
                "REG_ADM_SP",
            ],
            how="left",
        )

        self.df_acidentes["Nome_Municipio"] = np.where(
            (
                self.df_acidentes["Nome_Municipio"].isna()
                | (self.df_acidentes["Nome_Municipio"] == "NÃO INFORMADO")
            ),
            self.df_acidentes["MUNICIPIO"],
            self.df_acidentes["Nome_Municipio"],
        )

        self.df_acidentes = self.df_acidentes.drop(columns=["MUNICIPIO"])

    def padronizar_colunas(self) -> None:
        # Coordenadas
        self.df_acidentes[["Cod_Longitude", "Cod_Latitude"]] = self.df_acidentes[
            ["Cod_Longitude", "Cod_Latitude"]
        ].astype("float64")

        # Padronização das colunas de texto
        for col in self.df_acidentes.select_dtypes(include=["object", "string"]):
            self.df_acidentes[col] = (
                self.df_acidentes[col]
                .fillna("NÃO INFORMADO")
                .replace("", "NÃO INFORMADO")
                .str.upper()
                .str.strip()
            )

        # Ajusta colunas numéricas de vítimas
        cols_vitimas = [
            "ILESA",
            "LEVE",
            "MODERADA",
            "GRAVE",
            "FATAL",
            "SEMINFO",
        ]

        self.df_acidentes[cols_vitimas] = (
            self.df_acidentes[cols_vitimas].fillna(0).astype(int)
        )

        # Data
        self.df_acidentes["Data_Ocorrencia"] = pd.to_datetime(
            self.df_acidentes["Data_Ocorrencia"].astype(str),
            format="%Y%m%d",
            errors="coerce",
        ).dt.date

        # Hora
        self.df_acidentes["Hora_Ocorrencia"] = pd.to_datetime(
            self.df_acidentes["Hora_Ocorrencia"],
            format="%H%M%S",
            errors="coerce",
        ).dt.time

        # Aplica mapeamentos
        self.df_acidentes["Cod_Concessionaria"] = self.df_acidentes[
            "Cod_Concessionaria"
        ].replace(concessionarias.map_concessionaria)

        self.df_acidentes["Cod_Sentido_Pista"] = self.df_acidentes[
            "Cod_Sentido_Pista"
        ].replace(sentidos.map_sentido)

        self.df_acidentes["Desc_Local_Ocorr_Concessionaria"] = self.df_acidentes[
            "Desc_Local_Ocorr_Concessionaria"
        ].replace(local.map_local)

        self.df_acidentes["Cod_Causa_Provavel"] = (
            self.df_acidentes["Cod_Causa_Provavel"].replace(causa.map_causa).astype(str)
        )

        self.df_acidentes["Desc_Cond_Meteorol_Concessionaria"] = self.df_acidentes[
            "Desc_Cond_Meteorol_Concessionaria"
        ].replace(clima.map_clima)

        self.df_acidentes["Desc_Perfil_Pista"] = self.df_acidentes[
            "Desc_Perfil_Pista"
        ].replace(pista_perfil.map_pista_perfil)

        self.df_acidentes["Desc_Cond_Visibil_Concessionaria"] = self.df_acidentes[
            "Desc_Cond_Visibil_Concessionaria"
        ].replace(visibilidade.map_visibilidade)

        self.df_acidentes["Ind_Iluminacao"] = (
            self.df_acidentes["Ind_Iluminacao"]
            .astype(str)
            .str.upper()
            .replace(
                ["TRUE", "FALSE"],
                ["SIM", "NÃO"],
            )
        )

        self.df_acidentes["Desc_Class_Acid_Concessionaria"] = self.df_acidentes[
            "Desc_Class_Acid_Concessionaria"
        ].replace(classe.map_classe)

        self.df_acidentes["Desc_Tipo_Acid_Concessionaria"] = self.df_acidentes[
            "Desc_Tipo_Acid_Concessionaria"
        ].replace(subclasse.map_subclasse)

        # Renomeia colunas
        rename_map = {
            "Num_Ocorrencia": "ID_MITS",
            "Data_Ocorrencia": "DATA",
            "Hora_Ocorrencia": "HORA",
            "Cod_Concessionaria": "CONCESSIONARIA",
            "Num_Ocorr_Concessionaria": "NUMERO_OCORRENCIA",
            "Nome_Reduzido_Rodovia": "RODOVIA",
            "Cod_Sentido_Pista": "SENTIDO",
            "Cod_Latitude": "LATITUDE",
            "Cod_Longitude": "LONGITUDE",
            "Desc_Class_Acid_Concessionaria": "CLASSE",
            "Desc_Tipo_Acid_Concessionaria": "SUBCLASSE",
            "Cod_Causa_Provavel": "CAUSA_PROVAVEL",
            "ILESA": "VITIMA_ILESA",
            "LEVE": "VITIMA_LEVE",
            "MODERADA": "VITIMA_MODERADA",
            "GRAVE": "VITIMA_GRAVE",
            "FATAL": "VITIMA_FATAL",
            "SEMINFO": "VITIMAS_SEM_INFO",
            "Desc_Fator_Externo": "FATOR_EXTERNO",
            "Desc_Detalhe_Nivel1": "DETALHE_NIVEL_1",
            "Desc_Detalhe_Nivel2": "DETALHE_NIVEL_2",
            "Desc_Detalhe_Nivel3": "DETALHE_NIVEL_3",
            "Desc_Detalhe_Nivel4": "DETALHE_NIVEL_4",
            "Desc_Detalhe_Nivel5": "DETALHE_NIVEL_5",
            "Desc_Detalhe_Nivel6": "DETALHE_NIVEL_6",
            "Desc_Sequencia": "SEQUENCIA",
            "Desc_Sequencia_Detalhe": "SEQUENCIA_DETALHE",
            "Desc_Operacional_Momento": "OPERACIONAL_MOMENTO",
            "Desc_Operacional_Momento_Detalhe": ("OPERACIONAL_MOMENTO_DETALHE"),
            "Desc_Operacional_Pos": "OPERACIONAL_POS",
            "Desc_Operacional_Pos_Detalhe": ("OPERACIONAL_POS_DETALHE"),
            "Desc_Cond_Visibil_Concessionaria": "VISIBILIDADE",
            "Desc_Cond_Meteorol_Concessionaria": ("CONDICAO_METERIOLOGICA"),
            "Desc_Cond_Meteorol_Detalhe": ("CONDICAO_METERIOLOGICA_DETALHE"),
            "Desc_Cond_Meteorol_Detalhe2": ("CONDICAO_METERIOLOGICA_DETALHE_2"),
            "Desc_Pavimento": "PAVIMENTO",
            "Desc_Interferencia": "INTERFERENCIA",
            "Desc_Interferencia_Detalhe": ("INTERFERENCIA_DETALHE"),
            "Desc_Polo_Gerador": "POLO_GERADOR",
            "Ind_Iluminacao": "ILUMINACAO",
            "Desc_Tipo_Pista": "TIPO_PISTA",
            "Desc_Tracado_Pista": "TRACADO_PISTA",
            "Desc_Perfil_Pista": "PERFIL_PISTA",
            "Desc_Carac_Lindeira": "CARACTERISTICA_LINDEIRA",
            "Desc_Elemento_Estradal": "ELEMENTO_ESTRADAL",
            "Desc_Local_Nivel1": "LOCAL_NIVEL_1",
            "Desc_Local_Nivel2": "LOCAL_NIVEL_2",
            "Desc_Local_Ocorr_Concessionaria": ("LOCAL_OCORRENCIA"),
            "Nome_Municipio": "MUNICIPIO",
            "REG_ADM_SP": "REGIAO_ADMINISTRATIVA",
        }

        self.df_acidentes = self.df_acidentes.rename(columns=rename_map)

        # Reordena colunas principais
        colunas_finais = [
            "ID_MITS",
            "ID_EXTENSAO",
            "DATA",
            "HORA",
            "CONCESSIONARIA",
            "NUMERO_OCORRENCIA",
            "RODOVIA",
            "KM",
            "RODOVIA_KM",
            "SENTIDO",
            "LATITUDE",
            "LONGITUDE",
            "CATEGORIA",
            "CLASSE",
            "SUBCLASSE",
            "CAUSA_PROVAVEL",
            "VITIMA_ILESA",
            "VITIMA_LEVE",
            "VITIMA_MODERADA",
            "VITIMA_GRAVE",
            "VITIMA_FATAL",
            "VITIMAS_SEM_INFO",
            "FERIDOS",
            "VEICULOS_ENVOLVIDOS",
            "MUNICIPIO",
            "REGIAO_ADMINISTRATIVA",
            "REGIONAL_DER",
            "JURISDICAO",
            "FATOR_EXTERNO",
            "DETALHE_NIVEL_1",
            "DETALHE_NIVEL_2",
            "DETALHE_NIVEL_3",
            "DETALHE_NIVEL_4",
            "DETALHE_NIVEL_5",
            "DETALHE_NIVEL_6",
            "OPERACIONAL_POS",
            "OPERACIONAL_POS_DETALHE",
            "SEQUENCIA",
            "SEQUENCIA_DETALHE",
            "OPERACIONAL_MOMENTO",
            "OPERACIONAL_MOMENTO_DETALHE",
            "VISIBILIDADE",
            "CONDICAO_METERIOLOGICA",
            "CONDICAO_METERIOLOGICA_DETALHE",
            "CONDICAO_METERIOLOGICA_DETALHE_2",
            "PAVIMENTO",
            "INTERFERENCIA",
            "INTERFERENCIA_DETALHE",
            "POLO_GERADOR",
            "ILUMINACAO",
            "TIPO_PISTA",
            "TRACADO_PISTA",
            "PERFIL_PISTA",
            "CARACTERISTICA_LINDEIRA",
            "ELEMENTO_ESTRADAL",
            "LOCAL_OCORRENCIA",
            "LOCAL_NIVEL_1",
            "LOCAL_NIVEL_2",
        ]

        self.df_acidentes = self.df_acidentes[colunas_finais]

        self.df_acidentes = self.df_acidentes.drop_duplicates()

    def processar(self) -> pd.DataFrame:
        """
        Executa todas as etapas do tratamento dos dados
        e retorna o DataFrame final.
        """

        self.df_veiculos = self.preparar_veiculos()
        self.df_vitimas = self.preparar_vitimas()

        self.merge_veiculos_vitimas()
        self.ajusta_coordenadas()
        self.criar_colunas()
        self.join_rodovias()
        self.padronizar_colunas()

        return self.df_acidentes