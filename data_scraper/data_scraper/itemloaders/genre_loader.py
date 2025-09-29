from scrapy.loader import ItemLoader


def take_last(values):
    return values[-1]

class GenreLoader(ItemLoader):
    default_output_processor = take_last