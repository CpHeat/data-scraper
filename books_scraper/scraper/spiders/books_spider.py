from datetime import datetime, timezone
from pathlib import Path
from unittest import case

import scrapy
from scrapy.http import TextResponse
from scrapy.loader import ItemLoader
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from books_scraper.items import Book
from books_scraper.items import BookLoader


class BookSpider(CrawlSpider):
    name = "books"
    base_url = "https://books.toscrape.com/"
    start_urls = [
        "https://books.toscrape.com/catalogue/page-50.html"
    ]

    rules = (
        # Follow every index page
        Rule(
            LinkExtractor(allow=(r"catalogue/page-\d+\.html",)),
            follow=True
        ),
        # Handle every book encountered
        Rule(
            LinkExtractor(allow=(r"catalogue/.*\.html",), deny=(r"category/")),
            callback="_scrape_book",
            follow=False
        ),
    )

    """
    def parse(self, response: TextResponse) -> any:
        self.logger.info(f"Parsing {response.url}")

        # Follow the products
        products_rel = response.css("article.product_pod > h3 > a::attr(href)").extract()

        self.logger.info(f"📦 {len(products_rel)} products found on this page")
        for i, url in enumerate(products_rel, 1):
            full_url = response.urljoin(url)
            self.logger.info(f"  → Product {i}: {full_url}")

        yield from response.follow_all(products_rel, callback=self._scrape_book)

        # Get to next page
        next_page = response.css("li.next > a::attr(href)").get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)
        else:
            self.logger.info("✅ Scraping finished!")
    """

    def _scrape_book(self, response: TextResponse) -> Book:
        self.logger.info(f"📘 Scraping book {response.url}")

        availability: bool = self._get_availability(response)
        stock:int = 0
        if availability:
            stock = self._get_stock(response)

        book = BookLoader(item=Book(), response=response)
        book.add_css("type", "th:contains('Product Type') + *::text")
        book.add_css("title", "div.product_main > h1::text")
        book.add_css("thumbnail", "#product_gallery img::attr(src)")
        book.add_value("link", response.url)
        book.add_css("description", "#product_description + *::text")
        book.add_css("genre", "ul.breadcrumb li a::Text")
        book.add_css("rating", "p.star-rating::attr(class)")
        book.add_css("price", "p.price_color::text")
        book.add_value("availability", availability)
        book.add_value("stock", stock)
        book.add_css("upc", "th:contains('UPC') + *::text")
        book.add_css("tax", "th:contains('Tax') + *::text")
        book.add_css("reviews", "th:contains('Number of reviews') + *::text")
        book.add_value("scraped_at", datetime.now(timezone.utc))
        return book.load_item()

        """
        book = Book(
            product_type=self._get_product_type(response),
            title = self._get_title(response),
            thumbnail = self._get_thumbnail(response),
            description = self._get_description(response),
            genre = self._get_genre(response),
            rating = self._get_rating(response),
            price = self._get_price(response),
            availability = availability,
            stock = stock,
            upc = self._get_upc(response),
            tax = self._get_tax(response),
            reviews = self._get_reviews(response),
            scraped_at=datetime.now(timezone.utc),
        )
        

        print("BOOK/", book.items())

        return book
        """

    def _get_thumbnail(self, response: TextResponse) -> str:
        thumb_suffix = response.css("#product_gallery img::attr(src)").get()
        thumb_suffix = thumb_suffix.replace("../../", "")
        return response.urljoin(self.base_url + thumb_suffix)

    def _get_title(self, response: TextResponse) -> str:
        title = response.css("div.product_main > h1::text").get()
        return title

    def _get_price(self, response: TextResponse) -> int:
        price_as_str = response.css("p.price_color::text").get()
        price_as_float =  float(price_as_str.replace("£", ""))
        price_as_int = int(price_as_float * 100)
        return price_as_int

    def _get_availability(self, response: TextResponse) -> bool:
        try:
            response.css("i.icon-ok")
            availability = True
        except Exception as e:
            availability = False
        return availability

    def _get_stock(self, response: TextResponse) -> int:
        stock = response.xpath('//p[@class="instock availability"]/text()[2]').get()\
            .strip().replace("In stock (", "").replace(" available)", "")
        return stock

    def _get_rating(self, response: TextResponse) -> int:
        rating_wrapper = response.css("p.star-rating::attr(class)").get()
        rating = rating_wrapper.split(' ')[1]
        match rating:
            case "One":
                return 1
            case "Two":
                return 2
            case "Three":
                return 3
            case "Four":
                return 4
            case "Five":
                return 5
            case _:
                return 0

    def _get_description(self, response: TextResponse) -> str:
        return response.css("#product_description + *::text").get()

    def _get_upc(self, response: TextResponse) -> str:
        return response.css("th:contains('UPC') + *::text").get()

    def _get_product_type(self, response: TextResponse) -> str:
        return response.css("th:contains('Product Type') + *::text").get()

    def _get_tax(self, response: TextResponse) -> int:
        tax_as_str = response.css("th:contains('Tax') + *::text").get().replace("£", "")
        tax_as_float = float(tax_as_str)
        tax_as_int = int(tax_as_float * 100)
        return tax_as_int

    def _get_reviews(self, response: TextResponse) -> int:
        return int(response.css("th:contains('Number of reviews') + *::text").get())

    def _get_genre(self, response: TextResponse) -> str:
        return response.css("ul.breadcrumb li a::Text").getall()[-1]