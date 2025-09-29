import scrapy


class Book(scrapy.Item):
    type = scrapy.Field(serializer=str)
    title = scrapy.Field(serializer=str)
    thumbnail = scrapy.Field(serializer=str)
    link = scrapy.Field(serializer=str)
    description = scrapy.Field(serializer=str)
    genre = scrapy.Field(serializer=str)
    rating = scrapy.Field(serializer=int)
    price = scrapy.Field(serializer=int)
    availability = scrapy.Field(serializer=bool)
    stock = scrapy.Field(serializer=int)
    upc = scrapy.Field(serializer=str)
    tax = scrapy.Field(serializer=int)
    reviews = scrapy.Field(serializer=int)
    scraped_at = scrapy.Field(serializer=str)