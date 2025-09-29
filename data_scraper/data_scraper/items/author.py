import scrapy


class Author(scrapy.Item):
    slug = scrapy.Field(serializer=str)
    name = scrapy.Field(serializer=str)
    link = scrapy.Field(serializer=str)