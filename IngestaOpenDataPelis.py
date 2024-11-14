import logging.config
import requests
import json
import logging
from bs4 import BeautifulSoup
import unicodedata
import re

# Api de eventos culturales
BASE_URL = 'https://api.euskadi.eus/culture/events/'
TMBD_URL = "https://api.themoviedb.org/3/search/multi"

# Carpeta almacenamiento de los archivos json
BASE_PATH = './Data/apis'

# Lista de atributos de interes para guardar en el json
ATTRS = [
    "typeEs", "nameEs", "startDate", "endDate", "publicationDate", "language",
    "openingHoursEs", "sourceNameEs", "sourceUrlEs", "municipalityEs",
    "establishmentEs", "urlEventEs"
]

# Tipos de eventos culturales de los que extraer los datos
EVENT_TYPES = [
    "Cine y audiovisuales", "Actividad Infantil"
]

# Headers para la api de TMDB
HEADERS = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZjU1MzAyMmE0ZDg2YzA4OWUxZTNiZjgwZmZhNGYyZiIsIm5iZiI6MTcyODQ4ODczOS45NDI4NDQsInN1YiI6IjY3MDZhNDE4NTk3YzEyNmYwN2RkZDZiNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.H874m0N8DVjqDkjAudBq9YEYRKK_KnLAzMMIICHIlkI"
}

ATTRS_PELICULA = {
    "id": "id_pelicula"
}

logging.basicConfig(
    filename=f"Logs/openData.log",
    level = logging.DEBUG,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Sesión que se reutiliza a lo largo del codigo para reutilizar las cookies y agilizar la ejecución
session = requests.sessions.session()

def quitar_tildes(texto):
    """ Elimina tildes y caracteres especiales del texto que se pasa como parámetro utilizando la libreria unicodedata"""
    # Normalizamos el texto a una forma compatible (NFKD descompone los caracteres acentuados)
    texto_normalizado = unicodedata.normalize('NFKD', texto)

    # Filtramos los caracteres que no sean de la categoría "Mn" (caracteres diacríticos como tildes)
    texto_sin_tildes = ''.join([c for c in texto_normalizado if not unicodedata.combining(c)])

    return texto_sin_tildes

def limpiar_str(texto):
    """
    Llama a la función 'quitar_tildes', pone el texto en minúsculas y elimina los espacios en blanco de los extremos,
    Se utiliza para las keys de los mapas
    """
    try:
        texto = quitar_tildes(texto)
        texto = texto.strip().lower()
    except Exception as e: 
            logging.critical(f'Error limpiando el string: {texto}, {e}') 
    return texto

def formatear(item):
    """"
    Devuelve un mapeo los elementos obtenidos de la api, además de formatear la descripción de los mismos a un formato no html
    """
    
    pelicula = {}

    for attr in ATTRS: 
        if attr in item: 
            pelicula[attr] = item[attr]

    if ("descriptionEs" in item.keys()) and len(item["descriptionEs"].strip()) > 0:
        try:
            soup = BeautifulSoup(item["descriptionEs"], "html.parser")

            try:
                ps = soup.find_all("p")

                descripcion = ""
                for p in ps:
                    descripcion += p.get_text()

                if "Ficha técnica:" in descripcion:
                    descripcion = descripcion.replace("Ficha técnica:", "")

                try:
                    tablas = soup.find_all("ul")

                    if tablas:
                        for tabla in tablas:
                            for li in tabla.find_all("li"):

                                li_txt = li.get_text()

                                if ":" in li_txt:

                                     # Separa la 'key' del value dividiendo el string por el primer ':'
                                    str = li_txt.split(":", maxsplit=1)
                                    key = limpiar_str(str[0])

                                    if "," in str[1]:
                                        # Si el value contiene una lista en forma de string lo transforma a un objeto lista,
                                        # sino, guarda el value
                                        patron = r',| y '

                                        frags = re.split(patron, str[1])
                                        for i in range(0, len(frags)):
                                            frags[i] = frags[i].strip()
                                        pelicula[key] = frags
                                    else:
                                        pelicula[key] = str[1].strip()
                                else: 
                                    if "datos" not in pelicula.keys():
                                        pelicula["datos"] = []

                                    pelicula["datos"].append(li_txt)
                except Exception as e: 
                    logging.critical(f'{e}') #TODO

                pelicula["description"] = descripcion

            except Exception as e: 
                logging.error(f'{e}') #TODO
            
        except Exception as e: 
            logging.error(f'{e}') #TODO

    return pelicula

errores = []

def detalles_peli(evento): 
    """
    Busca coincidencias de las peliculas de los eventos con la api de TMDB y le añade al evento la id de la pelicula en caso de que la encuentre
    """
    logging.debug(f"Entrando a 'detalles_peli({evento["nameEs"]})'")

    titulo = evento["nameEs"]
    if "\"" in titulo: 
        titulo = titulo[titulo.find("\"")+1:titulo.rfind("\"")]

    try: 
        params = {
            "query": titulo,
            "language": "es-ES",
            "include_adult": True
        }

        response = session.get(TMBD_URL, headers=HEADERS, params=params)

        if response.status_code == 200:
            data_response = response.json()
            peli_api = {}

            if data_response["results"] and len(data_response["results"]) > 0:
                peli_api = data_response["results"][0]
                
                for attr_key, attr_value in ATTRS_PELICULA.items():
                    if attr_key in peli_api.keys():
                        evento[attr_value] = peli_api[attr_key]
                
            else: 
                raise Exception(f"No se ha encontrado coincidencias en {evento['nameEs']}") 

            logging.debug(f"{evento["nameEs"]} cargada en el mapa")    
    except Exception as e: 
        logging.error(f'Error al extraer detalles de {titulo}: {e}')
        errores.append(titulo)
    finally: 
        return evento


# Extraccion de los codigos de tipos de eventos
try: 
    logging.info("Iniciando ingesta eventos opendata")
    endpoint = "v1.0/eventType"

    logging.info(f'Realizando conexion a la api {BASE_URL}')

    # Llamada al endpoint que devuelve los tipos de ventos culturales junto con sus ids
    response = session.get(BASE_URL + endpoint)

    if response.status_code == 200:
        logging.info(f"Peticion a {endpoint} realizada correctamente.")
        data_response = response.json()

        eventos = []
        idTipo = -1
        for tipo in data_response:
            if tipo["nameEs"] in EVENT_TYPES:
                idTipo = tipo["id"]
                logging.info(f"ID de {tipo["nameEs"]}: {idTipo}")
                endpoint = f"v1.0/events/byType/{idTipo}"

                # Se extraen los eventos del tipo cuyo id ha sido previamente obtenido
                response = session.get(BASE_URL + endpoint)

                if response.status_code == 200:
                    logging.info(f"Peticion a {endpoint} realizada correctamente.")
                    data_response = response.json()

                    totalPages = data_response["totalPages"] 
                    currentPage = data_response["currentPage"]
                    
                    for item in data_response["items"]:
                        evento = formatear(item)

                        if evento:
                            eventos.append(detalles_peli(evento))

                    # La api devuelve la informacion paginada, por lo que se hacen varias peticiones hasta extraer toda la información
                    while currentPage <= totalPages:
                        currentPage += 1
                        params = {
                            # Atributo que especifica el número de página devuelto por la api
                            "_page": currentPage 
                        }

                        try:
                            response = session.get(BASE_URL + endpoint, params=params)
                            data_response = response.json()

                            for item in data_response["items"]:
                                evento = formatear(item)

                                if evento:
                                    eventos.append(detalles_peli(evento))
                        except Exception as e: 
                            logging.critical(f'Error inesperado al extraer la pagina {currentPage}: {e}')

                    # Una vez que se han obtenido los eventos de todos los tipos de interés se corta el bucle
                    EVENT_TYPES.remove(tipo["nameEs"])
                    if len(EVENT_TYPES) == 0: 
                        break

        if idTipo == -1:
            raise Exception("Error al extraer la id de los tipos: {EVENT_TYPES}")

        # archivo_json = f'{BASE_PATH}/datos_eventos_openData_{datetime.datetime.now().strftime("%Y%m%d")}.json'
        archivo_json = f'{BASE_PATH}/datos_eventos_openData.json'

        with open(archivo_json, "w", encoding="utf-8") as file: 
            json.dump(eventos, file, ensure_ascii=False,  indent=4)
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
    logging.info(errores)



