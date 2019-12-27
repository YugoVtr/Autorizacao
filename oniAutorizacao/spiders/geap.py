# -*- coding: utf-8 -*-
import scrapy
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class GeapSpider(scrapy.Spider):
    name = 'geap'
    allowed_domains = ['geap.com.br']
    start_urls = ['http://geap.com.br/']

    # Faz o login 
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
    
    # Caminha para a pagina de Autorizacao TISS
    def scrape_pages(self, response):
        url = '/prestador/RedirectRegulacaoTiss.asp'
        return response.follow(url=url, callback=self.solicitacaoSADT, errback=self.errback)

    # Pagina Inicial da Solicitacao SADT
    def solicitacaoSADT(self, response):
        url = '/regulacaoTiss/solicitacoes/SolicitacaoSADT.aspx'
        return response.follow(url=url, callback=self.new_form, errback=self.errback)

    # Pagina com formulario para solicitar a autorizacao
    def new_form(self, response): 
        return scrapy.FormRequest.from_response(
            response,
            formdata={"Transaction":"FormNew"},
            callback=self.autorizacao
        )

    # Criar o formulario com autorizacao e submiter
    def autorizacao(self, response):
        # import ipdb; ipdb.set_trace()
        scrapy.utils.response.open_in_browser(response)

    ########################## TRATAR ERROS NAS REQUESTS ##########################
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
