import os
import warnings
import pandas as pd

warnings.filterwarnings("ignore")

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv
from config import log


class ExtracaoBanco:
    def __init__(self, data_inicial: int, data_final: int):
        self.data_inicial = data_inicial
        self.data_final = data_final

        load_dotenv()
        self.db_host = os.getenv("DB_MITS_HOST")
        self.db_user = os.getenv("DB_MITS_USER")
        self.db_pass = os.getenv("DB_MITS_PASS")
        self.db_name = os.getenv("DB_MITS_NAME")

        self.engine = create_engine(
            URL.create(
                drivername="mssql+pyodbc",
                username=self.db_user,
                password=self.db_pass,
                host=self.db_host,
                database=self.db_name,
                query={"driver": "ODBC Driver 17 for SQL Server"},
            )
        )

    def _executar_query(self, query: str) -> pd.DataFrame:
        """
        Executa uma query parametrizada e retorna um DataFrame.
        """
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            log.error(f"Erro ao executar query: {e}")
            return pd.DataFrame()

    def extrair_acidentes(self) -> pd.DataFrame:
        query = f"""
        SELECT 
            a.Cod_Concessionaria,
            a.Num_Ocorrencia,
            a.Desc_Tipo_Acid_Concessionaria,
            a.Desc_Class_Acid_Concessionaria,
            a.Desc_Cond_Meteorol_Concessionaria,
            a.Desc_Cond_Visibil_Concessionaria,
            a.Cod_Causa_Provavel,
            a.Desc_Fator_Externo,
            a.Desc_Detalhe_Nivel1,
            a.Desc_Detalhe_Nivel2,
            a.Desc_Detalhe_Nivel3,
            a.Desc_Detalhe_Nivel4,
            a.Desc_Detalhe_Nivel5,
            a.Desc_Detalhe_Nivel6,
            a.Desc_Sequencia,
            a.Desc_Sequencia_Detalhe,
            a.Desc_Operacional_Momento,
            a.Desc_Operacional_Momento_Detalhe,
            a.Desc_Operacional_Pos,
            a.Desc_Operacional_Pos_Detalhe,
            a.Desc_Cond_Meteorol_Detalhe,
            a.Desc_Pavimento,
            a.Desc_Interferencia,
            a.Desc_Interferencia_Detalhe,
            a.Desc_Polo_Gerador,
            a.Ind_Iluminacao,
            a.Desc_Cond_Meteorol_Detalhe2,
            o.Data_Ocorrencia,
            o.Num_Ocorr_Concessionaria,
            o.Hora_Ocorrencia,
            o.Nome_Reduzido_Rodovia,
            o.Num_Km,
            o.Qtd_Complemento,
            o.Cod_Sentido_Pista,
            o.Nome_Municipio,
            o.Desc_Tipo_Pista,
            o.Desc_Tracado_Pista,
            o.Desc_Perfil_Pista,
            o.Desc_Carac_Lindeira,
            o.Cod_Latitude,
            o.Cod_Longitude,
            o.Desc_Elemento_Estradal,
            o.Desc_Local_Ocorr_Concessionaria,
            o.Desc_Local_Nivel1,
            o.Desc_Local_Nivel2
        FROM
            dbo.MapaCCO_Acidente a
        INNER JOIN
            dbo.MapaCCO_Ocorrencia o
            ON a.Cod_Concessionaria = o.Cod_Concessionaria
            AND o.Num_Ocorrencia = a.Num_Ocorrencia
        WHERE 
            o.Data_Ocorrencia BETWEEN {self.data_inicial} AND {self.data_final}
            AND a.Cod_Status IN ('F')
            AND o.Cod_Status IN ('F')
            AND o.Ind_Relatorio_Concessionaria IN (1)
            AND COALESCE(o.Ind_Fora_Concessao, 0) = 0
            AND COALESCE(o.Ind_Nao_Localizado, 0) = 0
            AND o.Nome_Reduzido_Rodovia NOT IN ('SP000', 'FORA')
        """
        return self._executar_query(query)

    def extrair_veiculos(self) -> pd.DataFrame:
        query = f"""
        SELECT
            v.Desc_Grupo_Veic_Concessionaria,
            v.Cod_Concessionaria,
            v.Num_Ocorrencia
        FROM
            dbo.MapaCCO_Veiculo_Envolvido v
        INNER JOIN
            dbo.MapaCCO_Ocorrencia o
            ON v.Num_Ocorrencia = o.Num_Ocorrencia
            AND v.Cod_Concessionaria = o.Cod_Concessionaria
        WHERE 
            o.Data_Ocorrencia BETWEEN {self.data_inicial} AND {self.data_final}
            AND v.Cod_Status IN ('F')
    """
        return self._executar_query(query)

    def extrair_vitimas(self) -> pd.DataFrame:
        query = f"""
        SELECT
            v.Cod_Situacao,
            v.Cod_Concessionaria,
            v.Num_Ocorrencia
        FROM
            dbo.MapaCCO_Vitima v
         INNER JOIN
            dbo.MapaCCO_Ocorrencia o
            ON v.Num_Ocorrencia = o.Num_Ocorrencia
            AND v.Cod_Concessionaria = o.Cod_Concessionaria
        WHERE 
            o.Data_Ocorrencia BETWEEN {self.data_inicial} AND {self.data_final}
            AND v.Cod_Status IN ('F')
        """
        return self._executar_query(query)

    def extrair_extensao_rodovias(self) -> pd.DataFrame:
        df = pd.read_excel(
            r"C:\Repos\acidentes-rodoviarios\dados_auxiliares\CCI_MALHA_RODOVIARIA_SP.xlsx",
            sheet_name="MALHA_RODOVIARIA_SP",
        )

        df = df[df["ADMINISTRACAO"] == "ARTESP"]

        df = df.groupby(["LOTE", "RODOVIA"]).agg({"EXTENSAO": "sum"}).reset_index()

        df["ID_EXTENSAO"] = (
            df["LOTE"].astype(str).str.zfill(2) + "_" + df["RODOVIA"].astype(str)
        )
        return df
