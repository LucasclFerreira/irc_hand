import ee
import sys
import time
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopy.geocoders import Nominatim


def get_coordinates(df: pd.DataFrame, address_column: str) -> ee.FeatureCollection:
    """
    Receives a DataFrame with addresses and finds the corresponding coordinates. Returns the FeatureCollection containing the address and point geometry of the coordinates.
    """

    print("pegando coordenadas...")
    geolocator = Nominatim(user_agent="hand_irb")
    geometries = []
    
    for address in df[address_column]:
        location = geolocator.geocode(address)

        if location:
            geometries.append(Point(location.longitude, location.latitude))
        else:
            geometries.append(None)

        time.sleep(1)
    
    df["geometry"] = geometries
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326").dropna()

    geojson = json.loads(gdf.to_json())
    feature_collection = ee.FeatureCollection(geojson)
    
    return feature_collection


def get_hand_values_per_point(points: ee.FeatureCollection) -> pd.DataFrame:
    """
    Receives a FeatureCollection with the addresses' point geometries.
    """

    print("amostrando o hand")
    hand = ee.Image("projects/ee-irc/assets/handCategorizado")
    
    points_hand = hand.sampleRegions(collection=points)

    points_df = ee.data.computeFeatures({
        "expression": points_hand,
        "fileFormat": "PANDAS_DATAFRAME"
    })
    
    formatted_points_df = points_df \
        .drop("geo", axis=1) \
        .rename(columns={"b1": "categoria_hand"}) \
        .assign(
            categoria_hand=lambda x: x.categoria_hand.map({
                1: "Muito Baixo (> 25m)",
                2: "Baixo (10-25m)",
                3: "Médio (5-10m)",
                4: "Alto (1-5m)",
                5: "Muito Alto (< 1m)"
            })
        )

    return formatted_points_df


def main():
    ee.Initialize(project="ee-paulomoraes") # isso aqui deve ser mudado para o nome do projeto

    if len(sys.argv) < 3:
        print("Missing arguments, either 'file_path', 'address_column' or both.")
        exit()

    file_path = sys.argv[1]
    file_extension = file_path.split(".")[-1]
    address_column = sys.argv[2]
  
    if file_extension == "csv":
        df = pd.read_csv(file_path)
    elif file_extension in ["xls", "xlsx"]:
        df = pd.read_excel(file_path)
    else:
        print("Invalid file format... Try again with a csv or excel file.")
        exit()

    collection = get_coordinates(df, address_column)
    result = get_hand_values_per_point(collection)

    result.to_csv("output.csv", index=False)


if __name__ == "__main__":
    main()

"""
    
    1. Dropa as linhas que não tem coordenadas
    2. Rola de mexer para ele pegar mais pontos válidos
    3. Preciso de trocar o main ser um arg para um metodo de classe. Atualmente tem um parâmetro indicando qual o nome da coluna
    4. Duas colunas, uma latitude e outra longitude    
    
"""