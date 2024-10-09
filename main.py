import scrapper
import logging
import json
from datetime import datetime
logging.basicConfig(
    filename=f"logs/requester-{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

URL="https://www.blogdepelis.top/"

try:
    FILE = f'responses/response-{"uwu"}-{datetime.now().strftime("%Y%m%d")}.json'
    events = []
    movies = {}
    movies = scrapper.scrap_categories(URL, movies)
    json.dump(movies, open(f'responses/response-{"uwu"}-{datetime.now().strftime("%Y%m%d")}.json', 'w', encoding="utf-8"), ensure_ascii=False, indent=4)
except Exception as e:
    logging.critical(f"ERROR INESPERADO: {e}")