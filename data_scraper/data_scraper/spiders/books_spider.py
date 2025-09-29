from datetime import datetime, timezone
from pathlib import Path
from unittest import case

import scrapy
from scrapy.http import TextResponse
from scrapy.loader import ItemLoader
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from data_scraper.items.book import Book
from data_scraper.itemloaders.book_loader import BookLoader

from data_scraper.itemloaders.genre_loader import GenreLoader
from data_scraper.items.genre import Genre


class BooksSpider(CrawlSpider):
    name = "books"
    base_url = "https://books.toscrape.com/"
    start_urls = [
        "https://books.toscrape.com/catalogue/page-1.html"
    ]

    rules = (
        # Follow every index page
        Rule(
            LinkExtractor(
                restrict_css="li.next > a",
                allow=(r"catalogue/page-\d+\.html",),
            ),
            follow=True
        ),
        # Handle every book encountered
        Rule(
            LinkExtractor(
                allow=(r"catalogue/.*\.html",),
                deny=(r"category/", r"catalogue/page-\d+\.html",)
            ),
            callback="_scrape_book",
            follow=False
        ),
    )

    def _scrape_book(self, response: TextResponse) -> Book:
        self.logger.info(f"📘 Scraping book {response.url}")

        genre_loader = GenreLoader(item=Genre(), response=response)
        genre_loader.add_css("genre", "ul.breadcrumb li a::Text")
        yield genre_loader.load_item()

        availability: bool = self._get_availability(response)
        stock:int = 0
        if availability:
            stock = self._get_stock(response)

        book_loader = BookLoader(item=Book(), response=response)
        book_loader.add_css("type", "th:contains('Product Type') + *::text")
        book_loader.add_css("title", "div.product_main > h1::text")
        book_loader.add_css("thumbnail", "#product_gallery img::attr(src)")
        book_loader.add_value("link", response.url)
        book_loader.add_css("description", "#product_description + *::text")
        book_loader.add_css("genre", "ul.breadcrumb li a::Text")
        book_loader.add_css("rating", "p.star-rating::attr(class)")
        book_loader.add_css("price", "p.price_color::text")
        book_loader.add_value("availability", availability)
        book_loader.add_value("stock", stock)
        book_loader.add_css("upc", "th:contains('UPC') + *::text")
        book_loader.add_css("tax", "th:contains('Tax') + *::text")
        book_loader.add_css("reviews", "th:contains('Number of reviews') + *::text")
        book_loader.add_value("scraped_at", datetime.now(timezone.utc))
        yield book_loader.load_item()

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