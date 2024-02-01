import scrapy
import re

class WikimoviesSpider(scrapy.Spider):
    name = "wikimovies"
    allowed_domains = ["ru.wikipedia.org", "www.imdb.com"]
    start_urls = ["https://ru.wikipedia.org/wiki/Категория:Фильмы_по_алфавиту", "https://www.imdb.com"]


    def parse(self, response):
        mw_pages_div = response.css('div#mw-pages')
        if mw_pages_div:
            for movie in mw_pages_div.css('.mw-category-group li'):
                movie_title = movie.css('a::text').get()
                movie_link = movie.css('a::attr(href)').get()
                yield response.follow(url=response.urljoin(movie_link), callback=self.parse_movie_data, meta={'title': movie_title})
               
        next_page = response.xpath('//div[@id="mw-pages"]//a[contains(text(), "Следующая страница")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)


    def parse_movie_data(self, response):

        def clean_digit(str): 
            cleaned_str = ', '.join(part.strip() for part in re.split(r',', str) if any(word[0].isdigit() for word in part.split()))
            return cleaned_str
        
        def clean_alpha(str): 
            cleaned_str = ', '.join(part.strip() for part in re.split(r',', str) if any(word[0].isalpha() for word in part.split()))
            return cleaned_str
        
        title = response.meta['title']
        infobox = response.css('table.infobox')

        if infobox:
            genres = infobox.css('tr:contains("Жанр") td span::text, tr:contains("Жанр") td a::text').getall()
            movie_genres_str = ', '.join(map(str.strip, genres))
            directors = infobox.css('tr:contains("Режиссёр") td span::text, tr:contains("Режиссёр") td a::text, tr:contains("Режиссёр") td li::text').getall()
            movie_directors_str = ', '.join(map(str.strip, directors))
            countries = infobox.css('tr:contains("Стран") td span::text, tr:contains("Стран") td a::text').getall()
            movie_countries_str = ', '.join(map(str.strip, countries))
            years = infobox.css('tr:contains("Год") td').xpath('.//a//text()').getall() 
            movie_years_str = ', '.join(map(str.strip, years))

            imdb_link = infobox.css('th:contains("IMDb") + td span a::attr(href)').get()
            imdb_rating = None
          
            if imdb_link:
                yield scrapy.Request(url=imdb_link, callback=self.parse_imdb, 
                                     meta={'title': title, 'genres': clean_alpha(movie_genres_str), 'directors': clean_alpha(movie_directors_str), 'countries': clean_alpha(movie_countries_str), 'years': clean_digit(movie_years_str)})
            else:
                yield self.construct_output(title, clean_alpha(movie_genres_str), clean_alpha(movie_directors_str), clean_alpha(movie_countries_str), clean_digit(movie_years_str), imdb_rating)

    def parse_imdb(self, response):
        title = response.meta['title']
        movie_genres_str = response.meta['genres'] 
        movie_directors_str = response.meta['directors'] 
        movie_countries_str = response.meta['countries'] 
        movie_years_str = response.meta['years']
        imdb_rating = response.css('div[data-testid="hero-rating-bar__aggregate-rating__score"] span::text').get()

        yield self.construct_output(title, movie_genres_str, movie_directors_str, movie_countries_str, movie_years_str, imdb_rating)

    def construct_output(self, title, movie_genres_str, movie_directors_str, movie_countries_str, movie_years_str, imdb_rating):
        return {
            'Название': title,
            'Жанр': movie_genres_str,
            'Режиссер': movie_directors_str,
            'Страны': movie_countries_str,
            'Год': movie_years_str,
            'IMDb': imdb_rating,
        }

