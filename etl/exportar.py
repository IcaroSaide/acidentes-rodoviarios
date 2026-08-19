import geopandas as gpd  
import pandas as pd
import smtplib
import os

from email.message import EmailMessage
from datetime import date, timedelta

from config import log, diretorios
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

class GerarArquivos:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.caminho_repo = diretorios.DIR_REPO

        load_dotenv()
        self.db_host = os.getenv("DB_HOST_GIS")
        self.db_user = os.getenv("DB_USER_GIS")
        self.db_pass = os.getenv("DB_PASS_GIS")
        self.db_name = os.getenv("DB_NAME_GIS")

        self.email_remetente = os.getenv('EMAIL_REMETENTE')
        self.email_pass = os.getenv('EMAIL_PASS')
        raw_emails = os.getenv("EMAIL_DESTINO", "")
        self.email_destino = [
            email.strip()
            for email in raw_emails.split(",")
            if email.strip()
        ]

    def arquivo_dados_abertos(self, ano: int) -> None:
        # Selecionando as colonas que serão usandas no arquivo
        df = self.df[[
            'DATA',
            'HORA',
            'CONCESSIONARIA',
            'RODOVIA',
            'KM',
            'SENTIDO',
            'LATITUDE',
            'LONGITUDE',
            'CLASSE',
            'SUBCLASSE',
            'CAUSA_PROVAVEL',
            'VITIMA_ILESA',
            'VITIMA_LEVE',
            'VITIMA_MODERADA',
            'VITIMA_GRAVE',
            'VITIMA_FATAL',
            'VITIMAS_SEM_INFO',
            'VEICULOS_ENVOLVIDOS',
            'VISIBILIDADE',
            'CONDICAO_METERIOLOGICA',
            'MUNICIPIO',
            'REGIAO_ADMINISTRATIVA',
            'REGIONAL_DER',
            'JURISDICAO'
        ]]

        try:
            df.to_csv(self.caminho_repo / 'saida' / f'acidentes_{ano}.csv', index=False)
        except Exception as e:
            log.error(f'Erro ao gerar arquivo do dados abertos de {ano}, motivo : {e}')

    def arquivo_power_bi(self) -> None:
        df = self.df.drop(columns = ['VITIMA_LEVE', 'VITIMA_MODERADA', 'VITIMA_GRAVE','VITIMAS_SEM_INFO'])

        try:
            df.to_parquet(self.caminho_repo / 'saida' / f'acidentes.parquet', index=False)
            log.info(f'Gerado o arquivo acidentes.parquet utilizado no power bi')
        except Exception as e:
            log.error(f'Erro ao gerar arquivo do power bi motivo : {e}')

    def banco_postgis(self) -> None:
        df = self.df.copy()

        df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
        df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")

        #  Remove registros inválidos
        df = df.dropna(subset=["LONGITUDE", "LATITUDE"])

        # Cria GeoDataFrame a partir de lon/lat
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(
                df["LONGITUDE"],
                df["LATITUDE"]
            ),
            crs="EPSG:4674"  # SIRGAS 2000
        )

        gdf.columns = [c.lower() for c in gdf.columns]

        # 🔌 Conexão com o banco
        engine = create_engine(
            f"postgresql+psycopg2://{self.db_user}:{self.db_pass}@{self.db_host}/{self.db_name}"
        )

        try:
            # 🗑 Remove tabela existente
            with engine.begin() as conn:
                conn.execute(text(f"DROP TABLE IF EXISTS artesp.tbr_acidentes CASCADE"))

            # 📥 Insere no PostGIS
            gdf.to_postgis(
                name="tbr_acidentes",
                con=engine,
                schema="artesp",
                if_exists="replace",
                index=True
            )

            log.info("Os dados de acidentes foram inseridos no banco com sucesso.")

        except Exception as e:
            log.error(f"Não foi possível inserir os dados de acidentes no banco de dados: {e}")

    def relatorio_e_mail(self):
        ontem = date.today() - timedelta(days=1)

        df = self.df[self.df["DATA"].dt.date == ontem]

        df = df.groupby("CONCESSIONARIA", as_index=False).agg(
                ACIDENTES=("CONCESSIONARIA", "size"),
                FERIDOS=("FERIDOS", "sum"),
                VITIMA_FATAL=("VITIMA_FATAL", "sum")    
            )
        
        df = df.astype({
            'ACIDENTES': int,
            'FERIDOS': int,
            'VITIMA_FATAL':int
        })

        total_acidentes = df["ACIDENTES"].sum()
        total_feridos = df["FERIDOS"].sum()
        total_obitos = df["VITIMA_FATAL"].sum()
        linhas = ""

        for _, row in df.iterrows():
            linhas += f"""
            <tr>
                <td style="text-align:center; color:#000000; border:1px solid #cccccc;">
                    {row['CONCESSIONARIA']}
                </td>
                <td style="text-align:center; color:#000000; border:1px solid #cccccc;">
                    {row['ACIDENTES']}
                </td>
                <td style="text-align:center; color:#000000; border:1px solid #cccccc;">
                    {row['FERIDOS']}
                </td>
                <td style="text-align:center; color:#000000; border:1px solid #cccccc;">
                    {row['VITIMA_FATAL']}
                </td>
            </tr>
            """
        linhas += f"""
        <tr style="background-color:#f2f2f2; font-weight:bold;">
            <td style="text-align:center; color:#000000; border:1px solid #cccccc;">
                TOTAL
            </td>
            <td style="text-align:center; color:#000000; border:1px solid #cccccc;">
                {total_acidentes}
            </td>
            <td style="text-align:center; color:#000000; border:1px solid #cccccc;">
                {total_feridos}
            </td>
            <td style="text-align:center; color:#000000; border:1px solid #cccccc;">
                {total_obitos}
            </td>
        </tr>
        """

        html = f"""
        <html>
        <body>
            <table width="100%" cellpadding="8" cellspacing="0"
                style="
                    border-collapse:collapse;
                    background-color:#ffffff;
                    border:1px solid #cccccc;
                ">
                <thead>
                    <tr style="background-color:#0a7a0a; color:#ffffff;">
                        <th style="border:1px solid #cccccc;" align="center">CONCESSIONÁRIA</th>
                        <th style="border:1px solid #cccccc;" align="center">ACIDENTES</th>
                        <th style="border:1px solid #cccccc;" align="center">FERIDOS</th>
                        <th style="border:1px solid #cccccc;" align="center">ÓBITOS</th>
                    </tr>
                </thead>
                <tbody>
                    {linhas}
                </tbody>
            </table>

            <p style="font-size:12px; margin-top:15px; color:#000000;">
                E-mail gerado automaticamente.
            </p>
        </body>
        </html>
        """
        
        data_formatada = ontem.strftime("%d/%m/%Y")
        msg = EmailMessage()
        msg["From"] = self.email_remetente
        msg["To"] = ", ".join(self.email_destino)
        msg["Subject"] = f"Relatório Acidentes - {data_formatada}"

        msg.set_content("Seu cliente de e-mail não suporta HTML.")
        msg.add_alternative(html, subtype="html")

        try:
            with smtplib.SMTP("smtp.gmail.com", 25) as server:
                server.starttls()
                server.login(self.email_remetente, self.email_pass)
                server.send_message(msg)

            log.info("E-mail com o relatorio enviado com sucesso!")
            
        except Exception as e:
            log.error(f'E-mail com o relatorio não enviado: {e}')