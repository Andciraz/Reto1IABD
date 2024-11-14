import scrapper
import tmdb_api
import logging
import json
from datetime import datetime
logging.basicConfig(
    filename=f"Data/main-logs-{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

BLOG_URL="https://www.blogdepelis.top/"

def main(scrappy_file=None, open_data_file=None):
    events = {}
    movies = {}

    if not scrappy_file:
        categories = scrapper.scrap_categories(BLOG_URL)
        for category in categories:
            # movies_in_page = scrapper.scrap_category_page("https://www.blogdepelis.top/?s=temporada")
            # for movie in movies_in_page:
            #     movie_in_dict = scrapper.scrap_movie(movies, movie, categories[14])
            #     if movie_in_dict:
            #         tmdb_id = tmdb_api.get_id(movie_in_dict.get('nombre'), 'Series' in movie_in_dict.get('categoria'))
            #         if tmdb_id:
            #             movie_in_dict["credits"] = tmdb_api.get_credits(tmdb_id, 'Series' in movie_in_dict.get('categoria'))
            pages_count = scrapper.scrap_category_pages(category)
            for count in range(1, int(pages_count) + 1):
                logging.info(f"RECORRIENDO PAGINA {count} DE LA CATEGORIA {category.get_text(strip=True)}")
                page = "page/" + str(count) if count != 1 else ""
                page_url = category['href'] + "/" + page
                movies_in_page = scrapper.scrap_category_page(page_url)
                for movie in movies_in_page:
                    movie_in_dict = scrapper.scrap_movie(movies, movie, category)
                    if movie_in_dict:
                        tmdb_id = tmdb_api.get_id(movie_in_dict.get('nombre'), 'Series' in movies.get(movie.get_text(strip=True), False).get('categoria'))
                        if tmdb_id:
                            credits = tmdb_api.get_credits(tmdb_id, 'Series' in movies.get(movie.get_text(strip=True), False).get('categoria'))
                            movie_in_dict["credits"] = credits

    else:
        movies = json.loads(scrappy_file.read())
        for movie in movies.values():
            movie.get()
try:
    main()
    with open(f'Data/scrappy/blogDePelis.json', 'r',
                  encoding="utf-8") as scrappy_file:
        main(scrappy_file)
except Exception as e:
    logging.critical(f"ERROR INESPERADO: {e}")