import scrapy

class Genre(scrapy.Item):
    genre = scrapy.Field(serializer=str)