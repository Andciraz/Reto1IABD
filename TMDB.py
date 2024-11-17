import requests
import json
import datetime
import logging
import unicodedata
import re

logging.basicConfig(
    filename=f"Logs/TMBD.log",
    level = logging.DEBUG,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# BASE_URL = 'https://api.themoviedb.org/3/search/movie'
BASE_URL = "https://api.themoviedb.org/3/search/multi"

# Carpeta almacenamiento de los archivos json
R_PATH = 'Data/scrappy'
W_PATH = 'Data/apis'

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

PROVIDER_TYPES = {
    "flatrate": "gratuito",
    "rent": "alquiler",
    "buy": "compra"
}

BASE_CREDITS_URL = "https://api.themoviedb.org/3/"
ENDPOINT_CREDITS = "/credits?language=es-ES"

PAISES = {}

session = requests.session()

errores = []

archivo_json = f'{W_PATH}/peliculas_api.json'

def detalles_peli(pelicula): 
    logging.debug(f"Entrando a 'detalles_peli({pelicula["nombre"]})'")

    try:
        titulo = pelicula["nombre"]

        if "Series" in pelicula["categoria"]:
            titulo = titulo.rsplit("–", maxsplit=1)[0].strip()

        params = {
            "query": titulo,
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

            logging.debug(f"{pelicula["nombre"]} cargada en el mapa")    
    except Exception as e: 
        logging.error(e)
        errores.append(pelicula["nombre"])
        return None
    
    return pelicula

def providers_peli(peli_detalles):
    providers = []

    if "id" in peli_detalles.keys():       
        url = f"https://api.themoviedb.org/3/movie/{peli_detalles["id"]}/watch/providers"

        if "Series" in peli_detalles["categoria"]:
            url = f"https://api.themoviedb.org/3/tv/{peli_detalles["id"]}/watch/providers"

        try:
            logging.debug("")
            response = session.get(url, headers=HEADERS)

            if response.status_code == 200:
                data_response = response.json()
                peli_id = data_response["id"]

                for pais in data_response["results"]:
                    provs = data_response["results"][pais]
                    for prov_type in PROVIDER_TYPES:

                        if prov_type in provs.keys():
                            for prov in provs[prov_type]:
                                provider = {
                                    "id": peli_id,
                                    "pais": pais,
                                    "proveedor": prov["provider_name"],
                                    "tipo": PROVIDER_TYPES[prov_type]
                                }

                                if pais in PAISES.keys():
                                    provider["pais"] += f"-{PAISES[pais]}" 

                                providers.append(provider)

        except requests.exceptions.HTTPError as http_err: 
            logging.error(f'Error HTTP: {http_err}')
        except requests.exceptions.ConnectionError as conn_err: 
            logging.error(f'Error de conexion: {conn_err}')
        except requests.exceptions.Timeout as timeout_err: 
            logging.error(f'Error de timeout: {timeout_err}')
        except requests.exceptions.RequestException as req_err: 
            logging.error(f'Error en la solicitud: {req_err}')
        except Exception as e: 
            logging.error(f'Error inesperado: {e}')
        finally:
            return providers

def cargar_paises():
    try: 
        response = session.get("https://api.themoviedb.org/3/configuration/countries", headers=HEADERS)

        if response.status_code == 200:
            data_response = response.json()

            for pais in data_response:
                PAISES[pais["iso_3166_1"]] = pais["english_name"]

    except Exception as e: 
        logging.error(f'Error inesperado: {e}')

def get_credits(id, serie=False):
    url = BASE_CREDITS_URL
    if serie:
        url += f"tv/{id}/aggregate_credits?language=es-ES"
    else:
        url += f"movie/{id}/credits?language=es-ES"
    response = session.get(url, headers=HEADERS)
    credits = {
        'cast': {},
        'crew': {},
    }
    if response.status_code == 200:
        data_response = response.json()
        if serie:
            for cast in data_response['cast']:
                if not credits['cast'].get(cast['name'], False):
                    roles = []
                    for role in cast['roles']:
                        roles.append(role['character'])
                    credits['cast'][cast['name']] = roles
                else:
                    for role in cast['roles']:
                        credits['cast'][cast['name']].append(role['character'])
            for crew in data_response['crew']:
                if not credits['crew'].get(crew['name'], False):
                    jobs = []
                    for job in crew['jobs']:
                        jobs.append(job['job'])
                    credits['crew'][crew['name']] = jobs
                else:
                    for job in crew['jobs']:
                        credits['crew'][crew['name']].append(job['job'])
        else:
            for cast in data_response['cast']:
                if not credits['cast'].get(cast['name'], False):
                    credits['cast'][cast['name']] = cast['character'].split("/")
                else:
                    for char in cast['character'].split("/"):
                        credits['cast'][cast['name']].append(char)
            for crew in data_response['crew']:
                if not credits['crew'].get(crew['name'], False):
                    credits['crew'][crew['name']] = crew['job'].split("/")
                else:
                    for job in crew['job'].split("/"):
                        credits['crew'][crew['name']].append(job)
    return credits

def datos_tmdb():
    try:
        peliculas_blog = json.load(open(f'{R_PATH}/blogDePelis.json', encoding="utf8"))
        peliculas = []
        providers = []

        cargar_paises()

        for pelicula in peliculas_blog.values():
            peli_detalles = detalles_peli(pelicula)
            if peli_detalles:
                # peli_detalles["credits"] = get_credits(peli_detalles["id"], "Series" in peli_detalles["categoria"])
                peliculas.append(peli_detalles) 

                try:
                    provs = providers_peli(peli_detalles)
                    if provs and len(provs) > 0:
                        providers.extend(provs)
                except Exception as e:
                    logging.error(e)

        archivo_json = f'{W_PATH}/peliculas.json'

        with open(archivo_json, "w", encoding="utf-8") as file: 
            json.dump(peliculas, file, ensure_ascii=False,  indent=4)
            logging.info("Archivo json peliculas generado correctamente.")

        archivo_json = f'{W_PATH}/providers.json'

        with open(archivo_json, "w", encoding="utf-8") as file: 
            json.dump(providers, file, ensure_ascii=False,  indent=4)
            logging.info("Archivo json providers generado correctamente.")

        

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



