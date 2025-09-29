from urllib.parse import urljoin

from itemloaders.processors import MapCompose, TakeFirst
from scrapy.loader import ItemLoader


base_url = "https://books.toscrape.com/"

def convert_raw_price_str_to_int(value):
    return int(float(value.replace("£", "")) * 100)

def compose_thumbnail_url(value) -> str:
    value = value.replace("../../", "")
    return urljoin(base_url, value)

def take_last(values):
    return values[-1]

def format_rating(values):
    rating = values.split(' ')[1]
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

class BookLoader(ItemLoader):
    default_output_processor = TakeFirst()

    price_in = MapCompose(convert_raw_price_str_to_int)
    thumbnail_in = MapCompose(compose_thumbnail_url)
    genre_out = take_last
    rating_in = MapCompose(format_rating)
    tax_in = MapCompose(convert_raw_price_str_to_int)