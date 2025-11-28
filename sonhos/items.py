import scrapy

class SonhoItem(scrapy.Item):
    inicial = scrapy.Field()
    sonho = scrapy.Field()
    significado = scrapy.Field()
    
