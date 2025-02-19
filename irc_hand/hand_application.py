"""
hand_calculator.py
==================

Módulo para processamento geoespacial e cálculo dos valores HAND (Height Above Nearest Drainage)
utilizando dados provenientes de arquivos CSV ou Excel e integrando a plataforma Google Earth Engine
(EE).

Este módulo fornece a classe `HandCalculator`, que encapsula todas as funcionalidades necessárias:
    - Carregamento e validação dos dados de entrada (CSV ou Excel).
    - Geocodificação dos endereços utilizando o Google Maps Geocoding API com inclusão das colunas
      'Latitude', 'Longitude' e 'geometry' ao DataFrame.
    - Conversão do DataFrame para um GeoDataFrame e, em seguida, para uma `ee.FeatureCollection` do Earth Engine.
    - Amostragem dos valores HAND a partir de uma imagem pré-processada do EE.
    - Mapeamento dos valores HAND para uma descrição categórica.
    - Salvamento dos resultados finais em um arquivo CSV.

Dependências:
-------------
    - ee (Google Earth Engine Python API)
    - sys
    - time
    - json
    - pandas
    - geopandas
    - shapely
    - geopy
    - asyncio
    - aiohttp
    - aiolimiter

Exemplo de uso via script de linha de comando:
-----------------------------------------------
    $ python hand_calculator.py <file_path> <address_column> <output_path> <project_name>

    Onde:
        - <file_path> é o caminho para o arquivo CSV ou Excel contendo os dados.
        - <address_column> é o nome da coluna que contém os endereços a serem geocodificados.
        - <output_path> é o caminho (incluindo o nome do arquivo) para salvar o CSV de saída.
        - <project_name> é o nome do projeto do Earth Engine.

Exemplo de uso via código:
--------------------------
    >>> from hand_calculator import HandCalculator
    >>> project_name = "seu-projeto-ee"
    >>> file_path = "dados.csv"
    >>> address_column = "endereco"
    >>> output_path = "resultado.csv"
    >>> calculator = HandCalculator(project_name)
    >>> calculator.run(file_path, address_column, output_path)

Notas:
------
    - Para evitar sobrecarga no serviço de geocodificação do Google Maps, é importante monitorar o uso da API.
    - As linhas com geocodificação malsucedida (ou seja, onde não foi possível obter coordenadas) são descartadas.
    - A conversão para `ee.FeatureCollection` requer a conversão intermediária para GeoJSON.
    - É necessário ter as credenciais e acesso apropriado configurado para o Google Earth Engine.
    - Para a versão assíncrona, utilizamos as bibliotecas aiohttp e aiolimiter para disparar requisições em paralelo
      (limitadas a 1 por segundo) sem bloquear a execução.

Licença:
--------
    Distribuído sob a licença MIT. Veja LICENSE para mais informações.

Autores:
--------
    Desenvolvido por [Seu Nome] - 2025

"""


import os
from dotenv import load_dotenv
load_dotenv()  

import ee
import sys
import time
import json
from typing import Optional, List

import asyncio
import aiohttp
from aiolimiter import AsyncLimiter

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import GoogleV3

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("A chave da API do Google Maps não foi encontrada no arquivo .env.")



async def async_geocode_address(session: aiohttp.ClientSession, address: str, limiter: AsyncLimiter):
    if not address or str(address).lower() == 'nan':
        print(f"[Async] Endereço inválido: {address}")
        return address, None, None

    print(f"[Async] Geocodificando: {address}")
    async with limiter:
        params = {
            'address': address,
            'key': GOOGLE_API_KEY,
            'region': 'br',
            'language': 'pt-BR'
        }
        async with session.get("https://maps.googleapis.com/maps/api/geocode/json", params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('status') == "OK" and data.get('results'):
                    location = data['results'][0]['geometry']['location']
                    lat = float(location['lat'])
                    lon = float(location['lng'])
                    print(f"[Async] Endereço encontrado: {address} -> ({lat}, {lon})")
                    return address, lat, lon
    print(f"[Async] Não foi possível encontrar: {address}")
    return address, None, None



async def geocode_all_addresses(addresses: list) -> list:
    """
    Cria uma sessão aiohttp e dispara tarefas assíncronas para todos os endereços.
    Utiliza um rate limiter para não exceder 1 requisição por segundo.
    """
    print(f"[Async] Iniciando geocodificação assíncrona para {len(addresses)} endereços...")
    limiter = AsyncLimiter(max_rate=1, time_period=1)
    async with aiohttp.ClientSession() as session:
        tasks = [async_geocode_address(session, address, limiter) for address in addresses]
        results = await asyncio.gather(*tasks)
    print("[Async] Geocodificação assíncrona concluída.")
    return results


class HandCalculator:
    """
    Classe para processamento geoespacial e cálculo dos valores HAND.

    Esta classe realiza os seguintes passos:
      1. Carregamento dos dados de um arquivo CSV ou Excel.
      2. Geocodificação dos endereços, com a criação das colunas 'Latitude', 'Longitude'
         e 'geometry'. As linhas sem sucesso na geocodificação são descartadas.
      3. Conversão dos dados geocodificados para um GeoDataFrame e, em seguida, para uma
         `ee.FeatureCollection` do Google Earth Engine.
      4. Amostragem dos valores HAND a partir de uma imagem predefinida do EE.
      5. Mapeamento dos valores HAND para uma descrição categórica.
      6. Salvamento dos resultados em um arquivo CSV.

    Attributes:
        _project_name (str): Nome do projeto para inicialização do Google Earth Engine.
        _df (Optional[pd.DataFrame]): DataFrame com os dados carregados, após a leitura do arquivo.
    """

    def __init__(self, project_name: Optional[str] = None):
        """
        Inicializa a instância com o nome do projeto do Earth Engine e inicializa o EE.

        Args:
            project_name (str): Nome do projeto do Earth Engine a ser utilizado.

        Raises:
            Exception: Se ocorrer erro durante a inicialização do Earth Engine.
        """
        print("[Init] Inicializando Google Earth Engine...")
        
        if project_name:
            self._project_name = project_name
            ee.Initialize(project=project_name)

        self._df: Optional[pd.DataFrame] = None
        print("[Init] Google Earth Engine inicializado com sucesso.")

    def load_data(self, file_path: str) -> None:
        """
        Carrega os dados de um arquivo CSV ou Excel.

        Este método identifica o formato do arquivo com base na sua extensão e carrega os dados
        para o atributo interno `_df`.

        Args:
            file_path (str): Caminho do arquivo de entrada.

        Raises:
            ValueError: Se o formato do arquivo não for CSV, XLS ou XLSX.
        """
        print(f"[Load Data] Carregando dados do arquivo: {file_path}")
        extension = file_path.split('.')[-1].lower()
        if extension == "csv":
            self._df = pd.read_csv(file_path, sep=';')
        elif extension in ["xls", "xlsx"]:
            self._df = pd.read_excel(file_path)
        else:
            raise ValueError("Formato de arquivo inválido. Utilize um arquivo CSV ou Excel.")
        self._df["id"] = self._df.index
        print(f"[Load Data] Dados carregados com sucesso. Total de registros: {len(self._df)}")

    def collect_coordinates(self, address_column: str) -> ee.FeatureCollection:
        """
        Realiza a geocodificação dos endereços de forma síncrona e retorna uma FeatureCollection do Earth Engine.

        Para cada endereço presente na coluna especificada, o método utiliza o serviço de geocodificação
        do Google Maps (via GoogleV3) para obter latitude e longitude. Além disso, ele adiciona três novas colunas ao DataFrame:
          - 'Latitude': Latitude obtida.
          - 'Longitude': Longitude obtida.
          - 'geometry': Objeto Point (do shapely) formado a partir das coordenadas.

        As linhas com falha na geocodificação (resultando em None) são descartadas posteriormente.

        Args:
            address_column (str): Nome da coluna que contém os endereços.

        Returns:
            ee.FeatureCollection: Coleção de features do Earth Engine contendo a geometria dos pontos.

        Raises:
            ValueError: Se os dados não tiverem sido carregados previamente com `load_data()`.
        """
        if self._df is None:
            raise ValueError("Dados não carregados. Chame o método load_data primeiro.")

        print("[Async] Iniciando geocodificação assíncrona...")
        addresses = list(self._df[address_column])
        results = asyncio.run(geocode_all_addresses(addresses))

        latitudes: List[Optional[float]] = []
        longitudes: List[Optional[float]] = []
        geometries: List[Optional[Point]] = []
        missing_addresses: List[bool] = []  # Lista para armazenar o status booleano da geocodificação

        for index, (address, lat, lon) in enumerate(results, start=1):
            print(f"[Async] Processando ({index}/{len(results)}): {address}")
            latitudes.append(lat)
            longitudes.append(lon)
            if lat is not None and lon is not None:
                geometries.append(Point(lon, lat))
                missing_addresses.append(False)  # Geocodificação bem-sucedida
            else:
                geometries.append(None)
                missing_addresses.append(True)   # Geocodificação falhou

        self._df["Latitude"] = latitudes
        self._df["Longitude"] = longitudes
        self._df["geometry"] = geometries
        self._df["MISSING_ADDRESS"] = missing_addresses  # Coluna agora com valores booleanos

        print("[Async] Conversão para GeoDataFrame...")
        # Cria o GeoDataFrame completo...
        gdf = gpd.GeoDataFrame(self._df, crs="EPSG:4326")
        # E filtra apenas os registros com geometria válida para enviar ao Earth Engine:
        gdf_valid = gdf[gdf["geometry"].notnull()]
        geojson = json.loads(gdf_valid.to_json())
        feature_collection = ee.FeatureCollection(geojson)
        print("[Async] Geocodificação assíncrona concluída.")

        return feature_collection

    def collect_coordinates_async(self, address_column: str) -> ee.FeatureCollection:
        """
        Realiza a geocodificação dos endereços de forma assíncrona e retorna uma FeatureCollection do Earth Engine.

        Para cada endereço presente na coluna especificada, o método utiliza requisições assíncronas para
        o serviço de geocodificação do Google Maps (usando aiohttp e aiolimiter) para obter latitude e longitude.
        Além disso, ele adiciona três novas colunas ao DataFrame:
        - 'Latitude': Latitude obtida.
        - 'Longitude': Longitude obtida.
        - 'geometry': Objeto Point (do shapely) formado a partir das coordenadas.
        - 'MISSING_ADDRESS': Booleano que indica True se a geocodificação falhar ou False caso contrário.

        As linhas com falha na geocodificação (resultando em None) serão descartadas na conversão para GeoDataFrame,
        mas a coluna "MISSING_ADDRESS" ficará disponível no DataFrame final.

        Args:
            address_column (str): Nome da coluna que contém os endereços.

        Returns:
            ee.FeatureCollection: Coleção de features do Earth Engine contendo a geometria dos pontos.

        Raises:
            ValueError: Se os dados não tiverem sido carregados previamente com `load_data()`.
        """
        if self._df is None:
            raise ValueError("Dados não carregados. Chame o método load_data primeiro.")

        print("[Async] Iniciando geocodificação assíncrona...")
        addresses = list(self._df[address_column])
        results = asyncio.run(geocode_all_addresses(addresses))

        latitudes: List[Optional[float]] = []
        longitudes: List[Optional[float]] = []
        geometries: List[Optional[Point]] = []
        missing_addresses: List[bool] = []  # Lista para armazenar o status booleano da geocodificação

        for index, (address, lat, lon) in enumerate(results, start=1):
            print(f"[Async] Processando ({index}/{len(results)}): {address}")
            latitudes.append(lat)
            longitudes.append(lon)
            if lat is not None and lon is not None:
                geometries.append(Point(lon, lat))
                missing_addresses.append(False)  # Geocodificação bem-sucedida
            else:
                geometries.append(None)
                missing_addresses.append(True)   # Geocodificação falhou

        self._df["Latitude"] = latitudes
        self._df["Longitude"] = longitudes
        self._df["geometry"] = geometries
        self._df["MISSING_ADDRESS"] = missing_addresses  # Coluna agora com valores booleanos

        print("[Async] Conversão para GeoDataFrame...")
        gdf = gpd.GeoDataFrame(self._df, crs="EPSG:4326")
        gdf = gdf.dropna(subset=["geometry"])
        geojson = json.loads(gdf.to_json())
        feature_collection = ee.FeatureCollection(geojson)
        print("[Async] Geocodificação assíncrona concluída.")

        return feature_collection


    def calculate_hand_values(self, points: ee.FeatureCollection) -> pd.DataFrame:
        """
        Amostra e calcula os valores HAND a partir da FeatureCollection dos pontos.

        O método utiliza uma imagem pré-processada do Earth Engine (identificada pelo ID
        "projects/ee-irc/assets/handCategorizado") e amostra os valores HAND nos pontos informados.
        Em seguida, formata os resultados:
            - Remove a coluna 'geo'.
            - Renomeia a coluna de amostragem de 'b1' para 'categoria_hand'.
            - Mapeia os valores numéricos para descrições categóricas conforme o seguinte dicionário:
                  { 1: "Muito Baixo (> 25m)",
                    2: "Baixo (10-25m)",
                    3: "Médio (5-10m)",
                    4: "Alto (1-5m)",
                    5: "Muito Alto (< 1m)" }

        Args:
            points (ee.FeatureCollection): Coleção de pontos a serem amostrados.

        Returns:
            pd.DataFrame: DataFrame contendo os resultados amostrados e formatados.
        """
        print("[HAND] Iniciando amostragem dos valores HAND...")
        hand_image = ee.Image("projects/ee-irc/assets/handCategorizado")
        points_hand = hand_image.sampleRegions(collection=points)

        points_df = ee.data.computeFeatures({
            "expression": points_hand,
            "fileFormat": "PANDAS_DATAFRAME"
        })

        # Mapeia os valores HAND para as descrições categóricas
        formatted_df = (
            points_df
            .drop("geo", axis=1)
            .rename(columns={"b1": "categoria_hand"})
            .assign(
                categoria_hand=lambda df: df.categoria_hand.map({
                    1: "Muito Baixo (> 25m)",
                    2: "Baixo (10-25m)",
                    3: "Médio (5-10m)",
                    4: "Alto (1-5m)",
                    5: "Muito Alto (< 1m)"
                })
            )
        )
        print("[HAND] Amostragem e mapeamento dos valores HAND concluídos.")

        # Realiza o merge dos resultados com o DataFrame original (usando a coluna 'id')
        # Assim, os registros sem geocodificação (que não foram amostrados) terão os campos HAND vazios.
        final_df = self._df.merge(formatted_df[['id', 'categoria_hand']], on='id', how='left')

        return final_df
    def save_results(self, df: pd.DataFrame, output_path: str) -> None:
        """
        Salva os resultados finais em um arquivo CSV.

        Este método recebe um DataFrame contendo os resultados do processamento e o salva no
        caminho especificado pelo parâmetro `output_path`.

        Args:
            df (pd.DataFrame): DataFrame com os resultados finais.
            output_path (str): Caminho completo (incluindo nome do arquivo) onde o CSV será salvo.

        Exemplo:
            >>> calculator.save_results(result_df, "saida/resultados.csv")
        """
        print(f"[Save] Salvando resultados em: {output_path}")
        df.to_csv(output_path, index=False)
        print("[Save] Resultados salvos com sucesso.")

    def run(self, file_path: str, address_column: str, output_path: str, use_async: bool = True) -> None:
        """
        Executa o fluxo completo de processamento dos dados.

        Esse método integra todas as etapas:
            1. Carrega os dados do arquivo informado.
            2. Geocodifica os endereços a partir da coluna especificada.
            3. Calcula os valores HAND utilizando o Earth Engine.
            4. Salva os resultados no arquivo CSV definido.

        Args:
            file_path (str): Caminho do arquivo de entrada (CSV ou Excel).
            address_column (str): Nome da coluna que contém os endereços para geocodificação.
            output_path (str): Caminho para salvar o arquivo CSV de saída.
            use_async (bool, opcional): Define se a geocodificação será feita de forma assíncrona.
                                        Padrão é True.
        """
        print("[Run] Iniciando processamento completo...")
        self.load_data(file_path)
        if use_async:
            points = self.collect_coordinates_async(address_column)
        else:
            points = self.collect_coordinates(address_column)
        result_df = self.calculate_hand_values(points)
        self.save_results(result_df, output_path)
        print("[Run] Processamento concluído com sucesso.")

    @classmethod
    def run_from_cli(cls) -> None:
        """
        Método de classe para execução do fluxo completo a partir da linha de comando.

        Este método interpreta os argumentos passados via sys.argv e executa a sequência:
            1. file_path: Caminho do arquivo de entrada.
            2. address_column: Nome da coluna que contém os endereços.
            3. output_path: Caminho para salvar o CSV de saída.
            4. project_name: Nome do projeto do Earth Engine.

        Caso os argumentos sejam insuficientes, o método informa o uso correto e encerra a execução.

        Exemplo:
            $ python hand_calculator.py dados.csv endereco saida.csv meu_projeto_ee
        """
        if len(sys.argv) < 5:
            print(
                "Argumentos insuficientes.\n"
                "Uso: python hand_calculator.py <file_path> <address_column> <output_path> <project_name>"
            )
            sys.exit(1)

        file_path = sys.argv[1]
        address_column = sys.argv[2]
        output_path = sys.argv[3]
        project_name = sys.argv[4]

        instance = cls(project_name)
        instance.run(file_path, address_column, output_path)


if __name__ == "__main__":
    hand = HandCalculator(project_name="ee-paulomoraes")
    hand.run(
        'teste.csv',
        'ADDRESSES',
        'output.csv'
    )