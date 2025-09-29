from datetime import datetime, timezone

import chompjs

from scrapy.http import TextResponse
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from data_scraper.itemloaders.quote_loader import QuoteLoader
from data_scraper.items.quote import Quote

from data_scraper.itemloaders.author_loader import AuthorLoader
from data_scraper.items.author import Author


class QuotesSpider(CrawlSpider):
    name = "quotes"
    base_url = "https://quotes.toscrape.com/js"
    start_urls = [
        "https://quotes.toscrape.com/js/page/1"
    ]

    rules = (
        # Follow every index page
        Rule(
            LinkExtractor(
                restrict_css="li.next > a",
                allow=(r"js/page/\d+\/",),
            ),
            callback="_scrape_quotes",
            follow=True
        ),
    )

    def _scrape_quotes(self, response: TextResponse):
        self.logger.info(f"Scraping from {response.url} ...")

        js_data = response.css("script::text").get()

        data_list = chompjs.parse_js_object(js_data)

        for data in data_list:
            quote_loader = QuoteLoader(item=Quote())
            quote_loader.add_value("content", data['text'])
            quote_loader.add_value("author", data['author']['slug'])
            quote_loader.add_value("tags", data['tags'])
            quote_loader.add_value("scraped_at", datetime.now(timezone.utc))
            yield quote_loader.load_item()

            author_loader = AuthorLoader(item=Author())
            author_loader.add_value("slug", data['author']['slug'])
            author_loader.add_value("name", data["author"]["name"])
            author_loader.add_value("link", data["author"]["goodreads_link"])
            yield author_loader.load_item()


        """
        for quote in quotes:
            quote_loader = QuoteLoader(item=Quote(), response=quote)
            quote_loader.add_css("content", "div.quote > span.text::text")
            quote_loader.add_css("author", "span > small.author::text")
            quote_loader.add_css("tags", "th:contains('Product Type') + *::text")
        """
