# 🚧 Acidentes Rodoviários — Pipeline de Dados

Pipeline de **extração, tratamento, enriquecimento e disponibilização de dados de acidentes rodoviários**, desenvolvido em Python.

O projeto automatiza o processamento dos registros de acidentes, veículos e vítimas, transformando dados operacionais em uma base estruturada e preparada para utilização em **análises de dados, Power BI e aplicações geoespaciais**.

> Projeto desenvolvido com foco em **Engenharia de Dados e Análise de Dados**, aplicando conceitos de ETL, tratamento de dados, integração entre fontes, processamento paralelo e armazenamento geoespacial.

---

## 📌 Sobre o projeto

O objetivo deste projeto é automatizar o fluxo de preparação dos dados de acidentes rodoviários.


## 🎯 Objetivos

O projeto foi desenvolvido com os seguintes objetivos:

* Automatizar a coleta de dados de acidentes rodoviários;
* Centralizar informações de acidentes, veículos e vítimas;
* Padronizar os dados provenientes das fontes operacionais;
* Corrigir e complementar informações geográficas;
* Enriquecer os registros com informações sobre rodovias e municípios;
* Criar uma classificação dos acidentes de acordo com a gravidade;
* Gerar arquivos estruturados para consumo por ferramentas de BI;
* Disponibilizar os dados geográficos em um banco PostGIS;
* Reduzir atividades manuais no processo de atualização dos dados.

---

## 🛠️ Tecnologias utilizadas

### Linguagem

* **Python**

### Manipulação e tratamento de dados

* **Pandas**
* **NumPy**
* **PyJanitor**

### Dados geoespaciais

* **GeoPandas**
* **Shapely**
* **PyProj**
* **GeoAlchemy2**

### Bancos de dados

* **SQL Server**
* **PostgreSQL + PostGIS**

### Conectividade

* **SQLAlchemy**
* **PyODBC**
* **psycopg2**

### Formatos de dados

* CSV
* Parquet
* Excel

### Processamento

* `ProcessPoolExecutor`
* Processamento paralelo por período

### Configuração

* `python-dotenv`

As principais dependências estão documentadas em `requirements.txt`.

---

# 🗂️ Estrutura do projeto

```text
acidentes-rodoviarios/
│
├── config/
│   ├── diretorios.py
│   └── log.py
│   
│
├── dados_auxiliares/
│   ├── coords.csv
│   └── CCI_MALHA_RODOVIARIA_SP.xlsx
│   
│
├── etl/
│   ├── extracao.py
│   ├── tratamento.py
│   ├── exportar.py
│   ├── de_para/
│   │   ├── causa.py
│   │   ├── clima.py
│   │   ├── classe.py
│   │   ├── concessionarias.py
│   │   ├── local.py
│   │   ├── sentidos.py
│   │   ├── subclasse.py
│   │   ├── veiculos.py
│   │   ├── vitimas.py
│   │   ├── visibilidade.py
│   │   └── pista_perfil.py
│
├── saida/
│   ├── acidentes_2020.csv
│   ├── acidentes_2021.csv
│   ├── ...
│   └── acidentes.parquet
│
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

A estrutura atual do repositório separa configuração, dados auxiliares, processamento ETL e arquivos de saída.

---

# 📈 Fluxo de dados

```text
                    ┌─────────────────────┐
                    │      SQL Server     │
                    │                     │
                    │  Acidentes          │
                    │  Veículos           │
                    │  Vítimas            │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      EXTRAÇÃO       │
                    │     extracao.py     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     TRATAMENTO      │
                    │    tratamento.py    │
                    │                     │
                    │ • Limpeza           │
                    │ • Padronização      │
                    │ • De-para           │
                    │ • Join              │
                    │ • Geolocalização    │
                    │ • Indicadores       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    CONSOLIDAÇÃO     │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
             ┌───────┐    ┌──────────┐   ┌─────────┐
             │  CSV  │    │ Parquet  │   │ PostGIS │
             └───┬───┘    └────┬─────┘   └────┬────┘
                 │             │              │
                 ▼             ▼              ▼
             Dados          Power BI       Análises
             abertos                        espaciais
```


# 🔄 Pipeline ETL

## 1. Extração

A etapa de extração é responsável por consultar o banco de dados operacional e obter três conjuntos principais:

### Acidentes

São extraídas informações como:

* Data e horário;
* Rodovia;
* Km;
* Município;
* Concessionária;
* Tipo e classificação do acidente;
* Causa provável;
* Condições meteorológicas;
* Visibilidade;
* Pavimento;
* Iluminação;
* Coordenadas;
* Características da pista;
* Localização da ocorrência.

A consulta também aplica filtros para selecionar registros finalizados e localizados dentro do escopo das rodovias consideradas pelo projeto.

### Veículos

São obtidas informações sobre os grupos de veículos envolvidos em cada ocorrência.

Esses dados posteriormente são agregados por ocorrência para gerar uma representação consolidada dos veículos envolvidos.

### Vítimas

São extraídos os registros das vítimas associadas às ocorrências, permitindo posteriormente calcular a quantidade de vítimas por situação/gravidade.

---

# 2. Tratamento dos dados

Após a extração, os diferentes conjuntos de dados são integrados e tratados.

## Veículos

Os dados de veículos passam por:

1. Remoção de registros nulos;
2. Remoção de valores vazios;
3. Padronização dos nomes;
4. Aplicação de mapeamentos;
5. Agrupamento por ocorrência;
6. Contagem dos veículos por categoria.

O resultado é uma coluna consolidada semelhante a:

```text
AUTOMOVEL=2|CAMINHAO=1|MOTOCICLETA=1
```

Isso permite representar em um único registro os diferentes tipos de veículos envolvidos em determinada ocorrência.

---

## Vítimas

As vítimas são transformadas através de uma operação de pivot, permitindo representar a quantidade de vítimas por categoria de gravidade.

Entre as categorias utilizadas estão:

* Vítima ilesa;
* Vítima leve;
* Vítima moderada;
* Vítima grave;
* Vítima fatal;
* Vítima sem informação.

Essas informações são posteriormente incorporadas à base principal de acidentes.

---

# Tratamento das coordenadas

O pipeline possui uma etapa específica para melhorar a qualidade das coordenadas geográficas.

Quando latitude ou longitude não estão disponíveis, o projeto consulta uma base auxiliar contendo informações de:

* Rodovia;
* Km;
* Latitude;
* Longitude;
* Lote.

O cruzamento é realizado utilizando a combinação:

```text
RODOVIA + KM
```

Quando uma coordenada original não está disponível, a coordenada da base auxiliar é utilizada como alternativa.

Essa etapa é especialmente importante para permitir a utilização posterior dos dados em mapas e análises espaciais.

---

# Enriquecimento das informações das rodovias

O projeto também utiliza uma base auxiliar contendo informações da malha rodoviária.

A partir dela, os registros de acidentes são enriquecidos com informações como:

* Município;
* Jurisdição;
* Regional DER;
* Região administrativa.

O relacionamento é realizado considerando a rodovia e o intervalo de quilômetros em que a ocorrência está localizada.

```text
RODOVIA
   +
KM
   │
   ▼
Malha Rodoviária
   │
   ├── Município
   ├── Jurisdição
   ├── Regional DER
   └── Região Administrativa
```

Esse processo transforma os dados originalmente operacionais em uma base mais adequada para análises geográficas e administrativas.

---

# Criação de indicadores

Durante o tratamento são criadas novas variáveis para facilitar as análises.

## Quilometragem

É criada uma coluna `KM` combinando o quilômetro principal e o complemento da ocorrência.

Também é criada uma identificação textual:

```text
RODOVIA_KM
```

Exemplo:

```text
SP330 KM 120
```

---

## Feridos

A quantidade total de feridos é calculada através da soma das categorias:

```text
VITIMA_LEVE
+
VITIMA_MODERADA
+
VITIMA_GRAVE
```

---

## Categoria do acidente

Cada ocorrência recebe uma classificação de acordo com a gravidade:

```text
ACIDENTE FATAL
ACIDENTE COM FERIDOS
ACIDENTE SEM VITIMAS
```

A regra utilizada é:

```text
Se houver vítima fatal
        ↓
ACIDENTE FATAL

Caso contrário, se houver feridos
        ↓
ACIDENTE COM FERIDOS

Caso contrário
        ↓
ACIDENTE SEM VITIMAS
```

Essa categorização facilita a criação de indicadores e análises no Power BI.

---

# Padronização

Antes da exportação, os dados passam por uma etapa final de padronização.

Entre os tratamentos realizados estão:

* Conversão de coordenadas para valores numéricos;
* Tratamento de valores nulos;
* Padronização de textos;
* Conversão de datas;
* Conversão de horários;
* Padronização das categorias;
* Aplicação de tabelas de-para;
* Renomeação das colunas;
* Organização da ordem das colunas;
* Remoção de registros duplicados.

Os textos são normalizados para maiúsculas e espaços desnecessários são removidos. Valores ausentes ou vazios são representados como `NÃO INFORMADO`.

---

# 📤 Saídas

O pipeline possui quatro principais destinos para os dados.

## CSV — Dados abertos

Para cada ano processado é criado um arquivo:

```text
saida/acidentes_2020.csv
saida/acidentes_2021.csv
saida/acidentes_2022.csv
...
```

Os arquivos possuem um conjunto selecionado de campos para disponibilização dos dados.

---

## Parquet — Power BI

Após a consolidação dos dados, o pipeline gera:

```text
saida/acidentes.parquet
```

O formato Parquet foi escolhido para disponibilizar uma estrutura mais adequada ao consumo analítico e ao Power BI.

---

## PostgreSQL + PostGIS

Os registros com coordenadas válidas são transformados em dados geográficos e enviados para:

```text
artesp.tbr_acidentes
```

Isso permite utilizar os dados em análises espaciais, mapas e sistemas geográficos.

---

## Relatório por e-mail

O projeto também possui uma funcionalidade preparada para gerar um relatório diário.

A função `relatorio_e_mail()` seleciona os acidentes ocorridos no dia anterior e consolida:

* Quantidade de acidentes;
* Quantidade de feridos;
* Quantidade de vítimas fatais;
* Informações por concessionária.

O resultado é enviado como um e-mail em HTML.

Essa funcionalidade está implementada no projeto, porém sua execução está atualmente desativada no `main.py`.

Para habilitá-la, a chamada correspondente precisa ser ativada no fluxo principal.

---

# ⚙️ Configuração

As credenciais e configurações de acesso são obtidas através de variáveis de ambiente.

O projeto disponibiliza um arquivo:

```text
.env.example
```

com exemplos de configuração para:

* Banco SQL Server;
* Banco PostgreSQL/PostGIS;
* E-mail.

## Exemplo

```env
DB_MITS_HOST=localhost
DB_MITS_USER=usuario_mits
DB_MITS_PASS=senha_mits
DB_MITS_NAME=database_mits

DB_HOST_GIS=localhost
DB_USER_GIS=usuario_gis
DB_PASS_GIS=senha_gis
DB_NAME_GIS=database_gis
```

Para envio de e-mails:

```env
EMAIL_REMETENTE=seu-email@empresa.com
EMAIL_PASS=sua-senha-ou-app-password
EMAIL_DESTINO=usuario1@empresa.com,usuario2@empresa.com
```

> **Importante:** não versione o arquivo `.env` contendo credenciais reais.

---

# 🚀 Instalação

## 1. Clonar o repositório

```bash
git clone https://github.com/IcaroSaide/acidentes-rodoviarios.git
cd acidentes-rodoviarios
```

## 2. Criar um ambiente virtual

### Windows

```bash
python -m venv venv
```

Ative o ambiente:

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

O projeto utiliza bibliotecas como Pandas, NumPy, GeoPandas, SQLAlchemy, PyODBC, psycopg2, GeoAlchemy2 e PyArrow.

---

---

# 📁 Principais módulos

## `main.py`

Responsável pela orquestração do pipeline.

Principais responsabilidades:

* Definição dos períodos;
* Execução paralela;
* Chamada das etapas ETL;
* Consolidação dos DataFrames;
* Geração das saídas finais.

---

## `etl/extracao.py`

Responsável pela conexão com o SQL Server e extração dos dados.

Principais métodos:

```python
extrair_acidentes()
extrair_veiculos()
extrair_vitimas()
extrair_extensao_rodovias()
```

---

## `etl/tratamento.py`

Responsável pelo processamento e enriquecimento dos dados.

Entre as principais operações estão:

```python
preparar_veiculos()
preparar_vitimas()
merge_veiculos_vitimas()
ajusta_coordenadas()
criar_colunas()
join_rodovias()
padronizar_colunas()
```

---

## `etl/exportar.py`

Responsável pela geração dos resultados.

Principais métodos:

```python
arquivo_dados_abertos()
arquivo_power_bi()
banco_postgis()
relatorio_e_mail()

```

# 📊 Possibilidades de análise

A base produzida pelo pipeline permite realizar análises como:

### Análise temporal

* Evolução dos acidentes por ano;
* Acidentes por mês;
* Acidentes por dia;
* Distribuição por horário;
* Comparação entre períodos.

### Análise geográfica

* Acidentes por rodovia;
* Acidentes por município;
* Acidentes por km;
* Identificação de pontos críticos;
* Distribuição espacial dos acidentes.

### Análise de gravidade

* Acidentes fatais;
* Acidentes com feridos;
* Acidentes sem vítimas;
* Quantidade de feridos;
* Quantidade de vítimas fatais.

### Análise operacional

* Acidentes por concessionária;
* Acidentes por jurisdição;
* Condições meteorológicas;
* Condições da pista;
* Iluminação;
* Visibilidade;
* Causas prováveis.

### Business Intelligence

O arquivo Parquet gerado pelo pipeline pode ser utilizado como fonte para dashboards e análises no **Power BI**.

---

# 🧠 Conceitos aplicados

Este projeto demonstra a aplicação prática de conceitos importantes de dados:

* ETL;
* Engenharia de Dados;
* Integração de múltiplas fontes;
* SQL;
* Manipulação de DataFrames;
* Data Cleaning;
* Data Wrangling;
* Data Quality;
* Padronização de dados;
* Tabelas de-para;
* Processamento paralelo;
* Dados geoespaciais;
* PostgreSQL;
* PostGIS;
* Parquet;
* Integração com Power BI;
* Automação de processos.

---


---

# 🔒 Segurança

O projeto utiliza variáveis de ambiente para armazenar informações sensíveis.

Credenciais de banco de dados e e-mail **não devem ser armazenadas diretamente no código-fonte**.

Utilize:

```text
.env
```

e mantenha esse arquivo fora do controle de versão.

O repositório disponibiliza apenas um modelo através de `.env.example`.

---

# ⚠️ Requisitos para execução

Para executar o pipeline completo, é necessário possuir acesso às fontes e infraestrutura utilizadas pelo projeto, incluindo:

* Banco SQL Server com os dados de origem;
* Driver ODBC compatível;
* Banco PostgreSQL com PostGIS para a saída geográfica;
* Arquivos auxiliares presentes em `dados_auxiliares`;
* Credenciais configuradas no `.env`.

Portanto, o repositório contém o código do pipeline, mas a execução completa depende da infraestrutura de dados utilizada pelo ambiente.

---