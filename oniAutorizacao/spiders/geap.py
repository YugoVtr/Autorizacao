# -*- coding: utf-8 -*-
import scrapy

class GeapSpider(scrapy.Spider):
    name = 'geap'
    allowed_domains = ['geap.com.br']
    start_urls = ['http://geap.com.br/']

    def parse(self, response):
        settings = scrapy.conf.settings
        form_data = {
            'seletor': settings['SELETOR'],
            'NroCPFCliente':'',
            'senha': settings['SENHA'],
            'NroContratado': settings['NROCONTRATADO'],
            'NroConveniada':'',
            'SglConveniada':'',
            'NroCPF':'',
            'NmeUsuario':''
        }
        return scrapy.FormRequest.from_response(
            response,
            formdata=form_data,
            callback=self.scrape_pages
        )
    
    def scrape_pages(self, response):
        url = 'https://www.geap.com.br/prestador/RedirectRegulacaoTiss.asp'
        return scrapy.Request(url=url, callback=self.solicitacaoSADT)

    def solicitacaoSADT(self, response):
        url = 'https://www.geap.com.br/regulacaoTiss/solicitacoes/SolicitacaoSADT.aspx'
        return scrapy.Request(url=url, callback=self.autorizacao)

    def autorizacao(self, response):
        scrapy.utils.response.open_in_browser(response)

