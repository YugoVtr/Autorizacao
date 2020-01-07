# -*- coding: utf-8 -*-
import scrapy
import json
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class GeapSpider(scrapy.Spider):
    name = 'geap'
    allowed_domains = ['geap.com.br']
    start_urls = ['http://geap.com.br/']

    # Faz o login 
    def parse(self, response):
        form_autenticacao = self.json_file_to_dict('autenticacao')
        return scrapy.FormRequest.from_response(
            response,
            formdata=form_autenticacao,
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
            callback=self.submit_form
        )

    # Criar o formulario com autorizacao e submiter
    def submit_form(self, response):
        formulario = self.json_file_to_dict('concluir')
        formulario["__VIEWSTATE"] = response.selector.xpath('//*[@id="__VIEWSTATE"]/@value').get()
        formulario["TabContainerControl1_ClientState"] = response.selector.xpath('//*[@id="TabContainerControl1_ClientState"]/@value').get()
        return scrapy.FormRequest.from_response(
            response, 
            formdata=formulario, 
            callback=self.callback
        )

    # Carregar formulario e submeter
    def callback(self, response): 
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

    ############################# FUNCOES HELPERS #############################
    def json_file_to_dict(self, file_name):
        relative_path = "formularios/{}.json".format(file_name)
        with open(relative_path, 'r') as file:
            return dict( json.loads( file.read() ))

