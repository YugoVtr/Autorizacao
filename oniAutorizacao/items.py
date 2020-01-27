# -*- coding: utf-8 -*-
import scrapy

class OniautorizacaoItem(scrapy.Item):
    numero_guia = scrapy.Field()
    senha = scrapy.Field()
    status = scrapy.Field()
    erro = scrapy.Field()
    
