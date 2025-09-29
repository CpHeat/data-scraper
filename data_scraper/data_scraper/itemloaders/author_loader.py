from urllib.parse import urljoin

from itemloaders.processors import TakeFirst, MapCompose
from scrapy.loader import ItemLoader


base_url = "https://www.goodreads.com"

def compose_link_url(value) -> str:
    return urljoin(base_url, value)

class AuthorLoader(ItemLoader):
    default_output_processor = TakeFirst()

    link_in = MapCompose(compose_link_url)