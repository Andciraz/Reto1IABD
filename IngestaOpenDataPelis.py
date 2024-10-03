import requests
import json
import datetime
import logging
from bs4 import BeautifulSoup

# Api de eventos culturales
BASE_URL = 'https://api.euskadi.eus/culture/events/'
BASE_PATH = './Data/'
ATTRS = [
    "typeEs", "nameEs", "startDate", "endDate", "publicationDate", "language",
    "openingHoursEs", "sourceNameEs", "sourceUrlEs", "municipalityEs",
    "establishmentEs", "urlEventEs", "images", "attachment"
        ]

logging.basicConfig(
    filename=f"{BASE_PATH}openData.log",
    level = logging.DEBUG,
    format = '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Extraccion de los codigos de tipos de eventos
try: 
    endpoint = "v1.0/eventType"

    logging.info(f'Realizando conexion a la api {BASE_URL}')
    response = requests.get(BASE_URL + endpoint)

    if response.status_code == 200:
        logging.info(f"Peticion a {endpoint} realizada correctamente.")
        data_response = response.json()
        # print(data_response)

        idTipo = -1
        for tipo in data_response:
            if tipo["nameEs"] == "Cine y audiovisuales":
                idTipo = tipo["id"]
                logging.info(f"ID de Cine y audiovisuales: {idTipo}")
                break

        if idTipo == -1:
            raise Exception("Error al extraer la id del tipo 'Cine y audiovisuales'")

    # Extraccion de eventos 
    endpoint = f"v1.0/events/byType/{idTipo}"

    response = requests.get(BASE_URL + endpoint)

    if response.status_code == 200:
        logging.info(f"Peticion a {endpoint} realizada correctamente.")
        data_response = response.json()

        totalPages = data_response["totalPages"] # La api devuelve la informacion paginada
        currentPage = data_response["currentPage"]
        eventos = []
        for item in data_response["items"]:
            evento = {}

            for attr in ATTRS: 
                if attr in item: 
                    evento[attr] = item[attr]

            # print (item["descriptionEs"])

            try:
                soup = BeautifulSoup(item["descriptionEs"], "html.parser")
                evento["descriptionEs"] = soup.get_text()
                pelicula = {}

                # TODO: Controlar que no haya descripcion
                try:
                    ps = soup.find_all("p")

                    descripcion = ""
                    for p in ps:
                        descripcion += p.get_text()

                    if "Ficha técnica:" in descripcion:
                        descripcion = descripcion.replace("Ficha técnica:", "")

                    try:
                        tabla = soup.find("ul")
                        if tabla:
                            for li in tabla.find_all("li"):
                                    # TODO: quitar tildes y caracteres especiales
                                    str = li.get_text().split(":", maxsplit=1)
                                    print (tabla)
                                    pelicula[str[0]] = str[1]
                    except Exception as e: 
                        logging.critical(f'{e}') #TODO



                    pelicula["description"] = descripcion
                    # print (soup)
                except Exception as e: 
                    logging.critical(f'{e}') #TODO

                try:
                    print("")
                    lista = soup.find("ul")

                    # TODO: Sacar las listas separar : controlar ficha...

                    # print(soup.get_text())
                except Exception as e: 
                    logging.critical(f'{e}') #TODO

                evento["film"] = pelicula
                eventos.append(evento)
            except Exception as e: 
                logging.critical(f'{e}') #TODO

        while currentPage <= totalPages:
            currentPage += 1
            params = {
                "_page": currentPage
            }

            try:
                response = requests.get(BASE_URL + endpoint, params=params)
                data_response = response.json()

                for item in data_response["items"]:
                    eventos.append(item)
            except Exception as e: 
                logging.critical(f'Error inesperado al extraer la pagina {currentPage}: {e}')

        archivo_json = f'{BASE_PATH}datos_eventos_openData_{datetime.datetime.now().strftime("%Y%m%d")}.json'
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