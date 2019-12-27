# -*- coding: utf-8 -*-
import scrapy
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class GeapSpider(scrapy.Spider):
    name = 'geap'
    allowed_domains = ['geap.com.br']
    start_urls = ['http://geap.com.br/']
    login = {
        "nrocontratado":"23022809", 
        "senha":"cjl38050",
        "seletor":"1"
    }

    # Faz o login 
    def parse(self, response):
        form_data = {
            'seletor': self.login['seletor'],
            'NroCPFCliente':'',
            'senha': self.login['senha'],
            'NroContratado': self.login['nrocontratado'],
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
