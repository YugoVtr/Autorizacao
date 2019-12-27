# -*- coding: utf-8 -*-
import scrapy
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

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
        url = '/prestador/RedirectRegulacaoTiss.asp'
        return response.follow(url=url, callback=self.solicitacaoSADT, errback=self.errback)

    def solicitacaoSADT(self, response):
        url = '/regulacaoTiss/solicitacoes/SolicitacaoSADT.aspx'
        return response.follow(url=url, callback=self.autorizacao, errback=self.errback)

    def autorizacao(self, response):
        scrapy.utils.response.open_in_browser(response)

    # Tratar erros nas requests
    def errback(self, failure):
        if failure.check(scrapy.spidermiddlewares.httperror.HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

        else: 
            self.logger.error(repr(failure))

