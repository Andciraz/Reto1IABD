
# GENERAL
APIS_DATA_PATH = 'Data/apis'

# OPENDATA
OPENDATA_URL = 'https://api.euskadi.eus/culture/events/'

# Lista de atributos de interes para guardar en el json
EVENT_ATTRS = [
    "typeEs", "nameEs", "startDate", "endDate", "publicationDate", "language",
    "openingHoursEs", "sourceNameEs", "sourceUrlEs", "municipalityEs",
    "establishmentEs", "urlEventEs", "images"
]

# Tipos de eventos culturales de los que extraer los datos
EVENT_TYPES = [
    "Cine y audiovisuales", "Actividad Infantil"
]

OPENDATA_HEADERS = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZjU1MzAyMmE0ZDg2YzA4OWUxZTNiZjgwZmZhNGYyZiIsIm5iZiI6MTcyODQ4ODczOS45NDI4NDQsInN1YiI6IjY3MDZhNDE4NTk3YzEyNmYwN2RkZDZiNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.H874m0N8DVjqDkjAudBq9YEYRKK_KnLAzMMIICHIlkI"
}

# TMBD
TMBD_ATTRS_PELICULA = {
    "id": "id_pelicula",
    "original_language": "idioma_original",
    "original_title": "titulo_original", 
    "popularity": "popularidad",
    "release_date": "fecha_estreno",
    "vote_average": "media_votos",
    "vote_count": "num_votos"
}

TMBD_MULTI_URL = "https://api.themoviedb.org/3/search/multi"