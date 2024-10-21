import requests
import json
import datetime
import logging
from bs4 import BeautifulSoup
import unicodedata
import re

# Api de eventos culturales
BASE_URL = 'https://api.euskadi.eus/culture/events/'

# Carpeta almacenamiento de los archivos json
BASE_PATH = './Data/apis'

# Lista de atributos de interes para guardar en el json
ATTRS = [
    "typeEs", "nameEs", "startDate", "endDate", "publicationDate", "language",
    "openingHoursEs", "sourceNameEs", "sourceUrlEs", "municipalityEs",
    "establishmentEs", "urlEventEs", "images", "attachment"
]

# Tipos de eventos culturales de los que extraer los datos
EVENT_TYPES = [
    "Cine y audiovisuales", "Actividad Infantil"
]

logging.basicConfig(
    filename=f"openData.log",
    level = logging.DEBUG,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

SESSION = requests.sessions.session()

# Elimina tildes y caracteres especiales del texto que se pasa como parámetro utilizando la libreria unicodedata
def quitar_tildes(texto):
    # Normalizamos el texto a una forma compatible (NFKD descompone los caracteres acentuados)
    texto_normalizado = unicodedata.normalize('NFKD', texto)

    # Filtramos los caracteres que no sean de la categoría "Mn" (caracteres diacríticos como tildes)
    texto_sin_tildes = ''.join([c for c in texto_normalizado if not unicodedata.combining(c)])

    return texto_sin_tildes

# Llama a la función 'quitar_tildes', pone el texto en minúsculas y elimina los espacios en blanco de los extremos,
# Se utiliza para las keys de los mapas
def limpiar_str(texto):
    try:
        texto = quitar_tildes(texto)
        texto = texto.strip().lower()
    except Exception as e: 
            logging.critical(f'Error limpiando el string: {texto}, {e}') 
    return texto

# Devuelve un mapeo los elementos obtenidos de la api, además de formatear la descripción de los mismos a un formato no html
def formatear(item):
    
    evento = {}

    for attr in ATTRS: 
        if attr in item: 
            evento[attr] = item[attr]

    if ("descriptionEs" in item.keys()) and len(item["descriptionEs"].strip()) > 0:
        try:
            soup = BeautifulSoup(item["descriptionEs"], "html.parser")

            # Mapa en el que guardar la información que se pueda extraer de la descripción
            pelicula = {}

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

            evento["info"] = pelicula
            
        except Exception as e: 
            logging.error(f'{e}') #TODO

    return evento


# Extraccion de los codigos de tipos de eventos
try: 
    endpoint = "v1.0/eventType"

    logging.info(f'Realizando conexion a la api {BASE_URL}')

    # Llamada al endpoint que devuelve los tipos de ventos culturales junto con sus ids
    response = SESSION.get(BASE_URL + endpoint)

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
                response = SESSION.get(BASE_URL + endpoint)

                if response.status_code == 200:
                    logging.info(f"Peticion a {endpoint} realizada correctamente.")
                    data_response = response.json()

                    totalPages = data_response["totalPages"] 
                    currentPage = data_response["currentPage"]
                    
                    for item in data_response["items"]:
                        evento = formatear(item)

                        if evento:
                            eventos.append(evento)

                    # La api devuelve la informacion paginada, por lo que se hacen varias peticiones hasta extraer toda la información
                    while currentPage <= totalPages:
                        currentPage += 1
                        params = {
                            # Atributo que especifica el número de página decuelto por la api
                            "_page": currentPage 
                        }

                        try:
                            response = SESSION.get(BASE_URL + endpoint, params=params)
                            data_response = response.json()

                            for item in data_response["items"]:
                                evento = formatear(item)

                                if evento:
                                    eventos.append(evento)
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



