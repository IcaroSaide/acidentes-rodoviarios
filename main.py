import time
import warnings
import datetime as dt
import pandas as pd

from config import log
from etl import exportar, extracao, tratamento
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore")

class DadosAcidentes:
    def __init__(self):
        self.lista_anos = list(range(2020, 2027))

    @staticmethod
    def _processar_ano(ano: int):
        # Define intervalo de datas
        data_inicial = int(f"{ano}0101")
        data_final = (
            int(dt.date.today().strftime("%Y%m%d"))
            if ano == dt.date.today().year
            else int(f"{ano}1231")
        )

        # Extração
        banco = extracao.ExtracaoBanco(data_inicial, data_final)
        df_acidentes = banco.extrair_acidentes()
        df_veiculos = banco.extrair_veiculos()
        df_vitimas = banco.extrair_vitimas()

        # Tratamento
        df_acidentes = tratamento.TratarDados(
            df_acidentes, df_veiculos, df_vitimas
        ).processar()

        # Exportação
        gerador = exportar.GerarArquivos(df_acidentes)
        gerador.arquivo_dados_abertos(ano)
        return df_acidentes

    def executar(self):
        """Executa processamento paralelo para todos os anos."""
        inicio = time.time()
        log.info("Iniciando processamento...")

        with ProcessPoolExecutor() as executor:
            resultados = list(executor.map(self._processar_ano, self.lista_anos))

        df_consolidado = pd.concat(resultados, ignore_index=True)

        gerador = exportar.GerarArquivos(df_consolidado)
        gerador.arquivo_power_bi()
        gerador.banco_postgis()
        # gerador.relatorio_e_mail()

        log.info(f"Tempo total: {dt.timedelta(seconds=round(time.time() - inicio))}")

if __name__ == "__main__":
    DadosAcidentes().executar()
