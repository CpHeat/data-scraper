from itemloaders.processors import TakeFirst, Join
from scrapy.loader import ItemLoader


class QuoteLoader(ItemLoader):
    default_output_processor = TakeFirst()

    tags_out = Join(',')