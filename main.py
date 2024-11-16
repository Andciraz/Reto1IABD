import scrapper
import logging
from datetime import datetime
from IngestaOpenDataPelis import openData
from TMDB import datos_tmdb

logging.basicConfig(
    filename=f"Data/Logs/main-logs-{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

BLOG_URL="https://www.blogdepelis.top/"


events = {}
movies = {}

try:
    logging.info(f"Iniciando scrappy de {BLOG_URL}")
    categories = scrapper.scrap_categories(BLOG_URL)
    for category in categories:
        pages_count = scrapper.scrap_category_pages(category)
        for count in range(1, int(pages_count) + 1):
            logging.info(f"RECORRIENDO PAGINA {count} DE LA CATEGORIA {category.get_text(strip=True)}")
            page = "page/" + str(count) if count != 1 else ""
            page_url = category['href'] + "/" + page
            movies_in_page = scrapper.scrap_category_page(page_url)
            for movie in movies_in_page:
                scrapper.scrap_movie(movies, movie, category)
except Exception as e:
    logging.critical(f"ERROR INESPERADO SCRAPEANDO: {e}")
else:
    logging.info(f"Scrappy ejecutado sin errores críticos")
finally: 
    # Se guardan siempre las peliculas debido a un error 'Connection aborted' que puede aparecer y no se puede controlar
    scrapper.save_movies(movies)

try:
    logging.info(f"Iniciando ingesta de eventos culturales de Open data")
    openData()
except Exception as e:
    logging.critical(f"ERROR INESPERADO DESCARGANDO EVENTOS: {e}")
else:
    logging.info(f"Ingesta ejecutada sin errores críticos")

try:
    logging.info(f"Iniciando ingesta de datos adicionales para las peliculas en TMDB")
    datos_tmdb()
except Exception as e:
    logging.critical(f"ERROR INESPERADO DESCARGANDO DATOS DE TMDB: {e}")
else:
    logging.info(f"Ingesta ejecutada sin errores críticos")


# movies = json.loads(scrappy_file.read())
# for movie in movies.values():
#     movie.get()

# try:
#     main()
#     with open(f'Data/scrappy/blogDePelis.json', 'r',
#                   encoding="utf-8") as scrappy_file:
#         main(scrappy_file)
# except Exception as e:
#     logging.critical(f"ERROR INESPERADO: {e}")