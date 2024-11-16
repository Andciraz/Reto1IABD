from bs4 import BeautifulSoup
from unidecode import unidecode
import requests
import logging
from datetime import datetime

logging.basicConfig(
    filename=f"Data/scrappy-logs-{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

BASE_CREDITS_URL = "https://api.themoviedb.org/3/"
ENDPOINT_CREDITS = "/credits?language=es-ES"
BASE_SEARCH_URL = "https://api.themoviedb.org/3/search/"

HEADERS = {
    "accept": "application/json",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZjU1MzAyMmE0ZDg2YzA4OWUxZTNiZjgwZmZhNGYyZiIsIm5iZiI6MTcyODQ4ODczOS45NDI4NDQsInN1YiI6IjY3MDZhNDE4NTk3YzEyNmYwN2RkZDZiNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.H874m0N8DVjqDkjAudBq9YEYRKK_KnLAzMMIICHIlkI"
}

SESSION = requests.Session()

def get_id(nombre, serie=False):
    id = False
    url = BASE_SEARCH_URL
    if serie:
        url += f"tv?query={nombre}&include_adult=false&language=es-ES&page=1"
    else:
        url += f"movie?query={nombre}&include_adult=false&language=es-ES&page=1"
    response = SESSION.get(url, headers=HEADERS)
    if response.status_code == 200:
        data_response = response.json()
        if len(data_response["results"]) > 0:
            found = data_response['results'][0]
            if found:
                id = found['id']
    if not id:
        logging.critical(f"NO SE HA ENCONTRADO {nombre}")
    return id

def get_credits(id, serie=False):
    url = BASE_CREDITS_URL
    if serie:
        url += f"tv/{id}/aggregate_credits?language=es-ES"
    else:
        url += f"movie/{id}/credits?language=es-ES"
    response = SESSION.get(url, headers=HEADERS)
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

