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

BASE_URL = 'https://api.themoviedb.org/3/search/movie'

# Carpeta almacenamiento de los archivos json
BASE_PATH = './Data/scrappy'

HEADERS = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZjU1MzAyMmE0ZDg2YzA4OWUxZTNiZjgwZmZhNGYyZiIsIm5iZiI6MTcyODQ4ODczOS45NDI4NDQsInN1YiI6IjY3MDZhNDE4NTk3YzEyNmYwN2RkZDZiNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.H874m0N8DVjqDkjAudBq9YEYRKK_KnLAzMMIICHIlkI"
}

session = requests.session()

errores = []



try:
    peliculas_blog = json.load(open(f'{BASE_PATH}/Scrappy-pruebas.json',encoding="utf8"))

    for pelicula in peliculas_blog.values():
        # print(pelicula)
        if "Series" in pelicula["categoria"]:
            continue #TODO

        else:
            try:
                params = {
                    "query": pelicula["nombre"],
                    "language": "es-ES"
                }

                # params = "?query=sagutxoa&include_adult=false&language=es-ES&page=1"
                response = session.get(BASE_URL, headers=HEADERS, params=params)

                if response.status_code == 200:
                    # print(response)
                    logging.info(f"Peticion a  realizada correctamente.")
                    data_response = response.json()
                    peli_api = {}

                    if data_response["results"] and len(data_response["results"]) > 0:
                        peli_api = peli_api = data_response["results"][0]
                    else: 
                        raise Exception(f"No se ha encontrado coincidencias en {pelicula['nombre']}")
                    
                    

            except Exception as e: 
                logging.critical(f'Error inesperado: {e}')
                errores.append(pelicula["nombre"])


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

print(errores)
