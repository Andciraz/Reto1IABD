from bs4 import BeautifulSoup
from unidecode import unidecode
import requests

MOVIE = False
def scrap_categories(base_url, movies):
    try:
        base_request = requests.get(base_url)
        if base_request.status_code == 200:
            main_soup = BeautifulSoup(base_request.content, 'html.parser')
            filtered_categories = []
            for i in range(16):
                filtered_categories.append(main_soup.select("a[href*='category']")[i])
            filtered_categories.remove(filtered_categories[14])
            for category in filtered_categories:
                category_request = requests.get(category['href'])
                if category_request.status_code == 200:
                    category_soup = BeautifulSoup(category_request.content, 'html.parser')
                    pages_count = category_soup.find_all(class_="page-numbers")[5].get_text(strip=True)
                    for count in range(1, int(pages_count)+1):
                        page = "page/" + str(count) if count != 1 else ""
                        category_page = unidecode(category.get_text(strip=True).lower()) if unidecode(category.get_text(strip=True).lower()) != "misterio" else "misterio-2"
                        page_request = requests.get(base_url + "category/" + category_page + "/" + page)
                        if page_request.status_code == 200:
                            movies_found = BeautifulSoup(page_request.content, 'html.parser').find(class_="blog-section-grid-posts clearfix").find_all(class_="title front-view-title")
                            for movie in movies_found:
                                MOVIE = movie
                                movie_request = requests.get(movie.find_next('a')['href'])
                                if movie_request.status_code == 200:
                                    movie_page = BeautifulSoup(movie_request.content, 'html.parser')
                                    content_1 = movie_page.find(style="font-family: Trebuchet MS, sans-serif;")
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

                                    portada = movie_page.find('img',fetchpriority="high")
                                    imagen = False
                                    if portada:
                                        imagen = portada['src']

                                    if not movies.get(movie.get_text(strip=True)[:movie.get_text(strip=True).rfind('(')-1], False):
                                        movies[
                                            movie.get_text(strip=True)[:movie.get_text(strip=True).rfind('(') - 1]] = {
                                            "nombre": movie.get_text(strip=True)[:movie.get_text(strip=True).rfind('(') - 1],
                                            "año": movie.get_text(strip=True)[
                                                   movie.get_text(strip=True).rfind('(') + 1:len(
                                                       movie.get_text(strip=True)) - 1],
                                            "descripción": desc_1 or desc_2 or "No se ha encontrado",
                                            "categoria": [category.get_text(strip=True)],
                                            "video": video,
                                            "portada": imagen,
                                        }
                                    else:
                                        movie_categories = movies.get(movie.get_text(strip=True)[:movie.get_text(strip=True).rfind('(')-1]).get("categoria")
                                        movie_categories.append(category.get_text(strip=True))
                                        movies.get(movie.get_text(strip=True)[:movie.get_text(strip=True).rfind('(') - 1])["categoria"] = movie_categories
                                else:
                                    raise Exception(f"Error al realizar petición: {movie.find_next('a')['href']}")
                        else:
                            raise Exception(f"Error al realizar petición: {base_url + page}")
                else:
                    raise Exception(f"Error al realizar petición: {category['href']}")
            return movies
        else:
            raise Exception(f"Error al realizar petición: {base_url}")
    except Exception as e:
        print(MOVIE)
        raise e


