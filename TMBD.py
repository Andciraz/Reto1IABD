import requests
import json
import datetime
import logging
from bs4 import BeautifulSoup
import unicodedata
import re

logging.basicConfig(
    filename=f"TMBD.log",
    level = logging.DEBUG,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# BASE_URL = 'https://api.themoviedb.org/3/search/movie'
BASE_URL = "https://api.themoviedb.org/3/search/multi"

# Carpeta almacenamiento de los archivos json
R_PATH = './Data/scrappy'
W_PATH = './Data/apis'

HEADERS = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZjU1MzAyMmE0ZDg2YzA4OWUxZTNiZjgwZmZhNGYyZiIsIm5iZiI6MTcyODQ4ODczOS45NDI4NDQsInN1YiI6IjY3MDZhNDE4NTk3YzEyNmYwN2RkZDZiNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.H874m0N8DVjqDkjAudBq9YEYRKK_KnLAzMMIICHIlkI"
}

ATTRS = {
    "id": "id",
    "original_language": "idioma_original",
    "original_title": "titulo_original", 
    "popularity": "popularidad",
    "release_date": "fecha_estreno",
    "vote_average": "media_votos",
    "vote_count": "num_votos"
}

session = requests.session()

errores = []

archivo_json = f'{W_PATH}/peliculas_api.json'

def detalles_peli(pelicula): 
    logging.debug(f"Entrando a 'detalles_peli({pelicula["nombre"]})'")

    try:
        params = {
            "query": pelicula["nombre"],
            "language": "es-ES",
            "include_adult": True
        }

        response = session.get(BASE_URL, headers=HEADERS, params=params)

        if response.status_code == 200:
            data_response = response.json()
            peli_api = {}

            if data_response["results"] and len(data_response["results"]) > 0:
                peli_api = data_response["results"][0]
                
                for attr_key, attr_value in ATTRS.items():
                    if attr_key in peli_api.keys():
                        pelicula[attr_value] = peli_api[attr_key]
                
            else: 
                raise Exception(f"No se ha encontrado coincidencias en {pelicula['nombre']}") 

            logging.info(f"{pelicula["nombre"]} cargada en el mapa")    
    except Exception as e: 
        logging.error(e)
        errores.append(pelicula["nombre"])
    finally: 
        return pelicula

# def formatear_peliculas():
try:
    peliculas_blog = json.load(open(f'{R_PATH}/Scrappy-pruebas.json', encoding="utf8"))
    peliculas = {}

    for pelicula in peliculas_blog.values():
        peliculas[pelicula["nombre"]] = detalles_peli(pelicula)

    with open(archivo_json, "w", encoding="utf-8") as file: 
        json.dump(peliculas, file, ensure_ascii=False,  indent=4)
        logging.info("Archivo json generado correctamente.")

except requests.exceptions.HTTPError as http_err: 
    logging.error(f'Error HTTP: {http_err}')
except requests.exceptions.ConnectionError as conn_err: 
    logging.error(f'Error de conexion: {conn_err}')
except requests.exceptions.Timeout as timeout_err: 
    logging.error(f'Error de timeout: {timeout_err}')
except requests.exceptions.RequestException as req_err: 
    logging.error(f'Error en la solicitud: {req_err}')
except Exception as e: 
    logging.critical(f'Error inesperado: {e}')
else: 
    logging.info("Ingesta completada correctamente.")
finally:
    logging.debug(f"Errores: {errores}")



