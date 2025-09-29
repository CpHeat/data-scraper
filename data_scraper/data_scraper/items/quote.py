import scrapy


class Quote(scrapy.Item):
    content = scrapy.Field(serializer=str)
    author = scrapy.Field(serializer=str)
    tags = scrapy.Field(serializer=str)
    scraped_at = scrapy.Field(serializer=str)