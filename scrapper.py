from bs4 import BeautifulSoup
from unidecode import unidecode
import requests
import json
import logging
import re
from datetime import datetime

logging.basicConfig(
    filename=f"Logs/scrappy-logs-{datetime.now().strftime('%Y%m%d')}.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S"
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
}

SESSION = requests.Session()
SESSION.headers = HEADERS


def save_movies(movies):
    with open(f'Data/scrappy/blogDePelis.json', 'w', encoding="utf-8") as file:
        json.dump(movies, file, ensure_ascii=False, indent=4)


def scrap_category_pages(category):
    try:
        logging.info(f"RECORRIENDO CATEGORIA {category.get_text(strip=True)}")
        category_request = SESSION.get(category['href'])
        if category_request.status_code == 200:
            category_soup = BeautifulSoup(category_request.content, 'html.parser')
            pages_count = category_soup.find_all(class_="page-numbers")[5].get_text(strip=True)
            logging.info(
                f"COMENZANDO A RECORRER PAGINAS ({int(pages_count)}) DE LA CATEGORIA {category.get_text(strip=True)}")
            return pages_count
        else:
            logging.error(f"Error al realizar petición: {category['href']}")
    except Exception as e:
        logging.critical(f"ERROR AL RECOGER INFORMACIÓN DE LA CATEGORIA: {category.get_text(strip=True)}")

    return True


def scrap_category_page(page_url):
    try:
        movies_found = False
        page_request = SESSION.get(page_url)
        if page_request.status_code == 200:
            movies_found = BeautifulSoup(page_request.content, 'html.parser').find(
                class_="blog-section-grid-posts clearfix").find_all(
                class_="title front-view-title")
        else:
            logging.error(f"Error al realizar petición: {page_url}")
        return movies_found
    except Exception as e:
        logging.critical(f"ERROR AL RECOGER INFORMACIÓN DE LA PAGINA {page_url}: {e}")
        raise e


def scrap_movie(movies, movie, category):
    try:
        logging.info(f"SCRAPPEANDO PELICULA {movie.get_text(strip=True)}")
        movie_request = SESSION.get(movie.find_next('a')['href'])
        if movie_request.status_code == 200:
            movie_page = BeautifulSoup(movie_request.content, 'html.parser')
            content_1 = movie_page.find(
                style="font-family: Trebuchet MS, sans-serif;")
            content_2 = movie_page.find(class_="thecontent")
            desc_1 = False
            desc_2 = False
            if content_1:
                desc_1 = content_1.find(text=True, recursive=False)
            if content_2:
                desc_2 = content_2.contents[3].get_text()

            reproductor = movie_page.find('iframe')
            video = False
            if reproductor:
                video = reproductor['src']

            portada = movie_page.find('img', fetchpriority="high")
            imagen = False
            if portada:
                imagen = portada['src']

            # movie_name_with_year = re.sub("– Temporada .+ ", "", re.sub("\(\+18\)", "", movie.get_text(strip=True)))
            movie_name_with_year = re.sub("– Temporada .+ ", "", movie.get_text(strip=True))
            movie_name_with_year = re.sub("\(\+18\)", "", movie_name_with_year)

            name = movie_name_with_year[:movie_name_with_year.rfind('(') - 1]
            year = movie_name_with_year[movie_name_with_year.rfind('(') + 1:len(movie_name_with_year) - 1]
            if not movies.get(name, False):
                logging.info(f"PELICULA AÑADIDA {movie.get_text(strip=True)}")
                movies[name] = {
                    "nombre": name,
                    "año": year,
                    "descripción": desc_1 or desc_2 or "No se ha encontrado",
                    "categoria": [category.get_text(strip=True)],
                    "video": video,
                    "portada": imagen,
                }

            else:
                logging.info(
                    f"PELICULA REPETIDA {movie.get_text(strip=True)} AÑADIENDO CATEGORIA {category.get_text(strip=True)}")
                movie_categories = movies.get(name).get("categoria")
                if category.get_text(strip=True) not in movie_categories:
                    movie_categories.append(category.get_text(strip=True))
                    movies.get(name)["categoria"] = movie_categories
            return movies.get(movie.get_text(strip=True), False)
        else:
            logging.error(
                f"Error al realizar petición: {movie.find_next('a')['href']}")
    except Exception as e:
        logging.critical(
            f"ERROR AL RECOGER INFORMACIÓN DE: {movie.find_next('a')['href']}")


def scrap_categories(base_url=None):
    try:
        categories = False
        base_request = SESSION.get(base_url)
        if base_request.status_code == 200:
            main_soup = BeautifulSoup(base_request.content, 'html.parser')

            categories = main_soup.find('ul', id="menu-menu").select("a[href*='category']")
            for category in categories:
                if category.get_text(strip=True) == "Otros":
                    categories.remove(category)
        else:
            logging.error(f"Error al realizar petición: {base_url}")
        return categories
    except Exception as e:
        logging.critical(f"ERROR AL RECOGER LAS CATEGORIAS: {e}")
        raise e


def scrap_all(movies, base_url="https://www.blogdepelis.top/"):
    """
    ESTE METODO PERMITE SCRAPEAR UNA PAGINA CON UNA ESTRUCTURA COMO

    https://www.blogdepelis.top/

    EN CASO DE NO RECIBIR NINGUNA URL SE SCRAPEA ESA PAGINA


    :param base_url:
    :param movies:
    :return:
    """
    try:

        base_request = SESSION.get(base_url)
        if base_request.status_code == 200:
            main_soup = BeautifulSoup(base_request.content, 'html.parser')

            filtered_categories = []
            for i in range(17):
                filtered_categories.append(main_soup.select("a[href*='category']")[i])
            filtered_categories.remove(filtered_categories[14])
            logging.info(f"COMENZANDO A RECORRER CATEGORIAS {filtered_categories}")
            for category in filtered_categories:
                try:
                    logging.info(f"RECORRIENDO CATEGORIA {category.get_text(strip=True)}")
                    category_request = SESSION.get(category['href'])
                    if category_request.status_code == 200:

                        category_soup = BeautifulSoup(category_request.content, 'html.parser')
                        pages_count = category_soup.find_all(class_="page-numbers")[5].get_text(strip=True)
                        logging.info(
                            f"COMENZANDO A RECORRER PAGINAS ({int(pages_count)}) DE LA CATEGORIA {category.get_text(strip=True)}")
                        for count in range(1, int(pages_count) + 1):
                            try:
                                logging.info(
                                    f"RECORRIENDO PAGINA {count} DE LA CATEGORIA {category.get_text(strip=True)}")
                                page = "page/" + str(count) if count != 1 else ""
                                page_request = SESSION.get(category['href'] + "/" + page)
                                if page_request.status_code == 200:

                                    movies_found = BeautifulSoup(page_request.content, 'html.parser').find(
                                        class_="blog-section-grid-posts clearfix").find_all(
                                        class_="title front-view-title")
                                    logging.info(f"COMENZANDO A RECORRER PELICULAS {movies_found}")
                                    for movie in movies_found:
                                        try:
                                            logging.info(f"SCRAPPEANDO PELICULA {movie.get_text(strip=True)}")
                                            movie_request = SESSION.get(movie.find_next('a')['href'])
                                            if movie_request.status_code == 200:
                                                movie_page = BeautifulSoup(movie_request.content, 'html.parser')
                                                content_1 = movie_page.find(
                                                    style="font-family: Trebuchet MS, sans-serif;")
                                                content_2 = movie_page.find(class_="thecontent")
                                                desc_1 = False
                                                desc_2 = False
                                                if content_1:
                                                    desc_1 = content_1.find(text=True, recursive=False)
                                                if content_2:
                                                    desc_2 = content_2.contents[3].get_text()

                                                reproductor = movie_page.find('iframe')
                                                video = False
                                                if reproductor:
                                                    video = reproductor['src']

                                                portada = movie_page.find('img', fetchpriority="high")
                                                imagen = False
                                                if portada:
                                                    imagen = portada['src']

                                                name = movie.get_text(strip=True)[
                                                       :movie.get_text(strip=True).rfind('(') - 1]
                                                if not movies.get(movie.get_text(strip=True)[
                                                                  :movie.get_text(strip=True).rfind('(') - 1], False):
                                                    logging.info(f"PELICULA AÑADIDA {movie.get_text(strip=True)}")
                                                    movies[
                                                        movie.get_text(strip=True)[
                                                        :movie.get_text(strip=True).rfind('(') - 1]] = {
                                                        "nombre": name,
                                                        "año": movie.get_text(strip=True)[
                                                               movie.get_text(strip=True).rfind('(') + 1:len(
                                                                   movie.get_text(strip=True)) - 1],
                                                        "descripción": desc_1 or desc_2 or "No se ha encontrado",
                                                        "categoria": [category.get_text(strip=True)],
                                                        "video": video,
                                                        "portada": imagen,
                                                    }

                                                else:
                                                    logging.info(
                                                        f"PELICULA REPETIDA {movie.get_text(strip=True)} AÑADIENDO CATEGORIA {category.get_text(strip=True)}")
                                                    movie_categories = movies.get(name).get("categoria")
                                                    movie_categories.append(category.get_text(strip=True))
                                                    movies.get(name)["categoria"] = movie_categories
                                            else:
                                                logging.error(
                                                    f"Error al realizar petición: {movie.find_next('a')['href']}")
                                        except Exception as e:
                                            logging.critical(
                                                f"ERROR AL RECOGER INFORMACIÓN DE: {movie.find_next('a')['href']}")
                                else:
                                    logging.error(f"Error al realizar petición: {base_url + page}")
                            except Exception as e:
                                logging.critical(
                                    f"ERROR AL RECOGER INFORMACIÓN DE LA PAGINA {count} DE LA CATEGORIA {category.get_text(strip=True)}")
                    else:
                        logging.error(f"Error al realizar petición: {category['href']}")
                except Exception as e:
                    logging.critical(f"ERROR AL RECOGER INFORMACIÓN DE LA CATEGORIA: {category.get_text(strip=True)}")
            return movies
        else:
            logging.error(f"Error al realizar petición: {base_url}")
    except Exception as e:
        raise e
