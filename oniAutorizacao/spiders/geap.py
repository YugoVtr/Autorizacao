# -*- coding: utf-8 -*-
import scrapy, logging, json, re, pkgutil
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
            method='POST',
            formdata={"Transaction":"FormNew"},
            callback=self.criar_nro_gsp_solicitacao
        )

    def criar_nro_gsp_solicitacao(self, response):
        formulario = self.json_file_to_dict('form_new')

        formulario["__VIEWSTATE"] = response.selector.xpath('//*[@id="__VIEWSTATE"]/@value').get()
        formulario["DtaSolicitacao"] = response.selector.xpath('//*[@id="DtaSolicitacao"]/@value').get()
        formulario["NroContratadoPrestadorExecutante"] = response.selector.xpath('//*[@id="NroContratadoPrestadorExecutante"]/@value').get()
        formulario["NmeContratadoPrestadorExecutante"] = response.selector.xpath('//*[@id="NmeContratadoPrestadorExecutante"]/@value').get()
        
        formulario["TabContainerControl1$TabGeral$NroCartao"] = "901004143630084" 
        formulario["TabContainerControl1$TabGeral$NroConselhoProfissionalSolicitante"] = "8158" 
        formulario["TabContainerControl1$TabGeral$NroUFConselhoProfissionalSolicitante"] = "52" 
        formulario["TabContainerControl1$TabGeral$DesIndicacaoClinica"] = "DORES ABDOMINAIS" 
        formulario["TabContainerControl1$TabProcedimento$NroServicoGridRegulacao"] = "40808041" 
        formulario["TabContainerControl1$TabProcedimento$QtdSolicitadaGridRegulacao"] = "1" 

        return scrapy.FormRequest.from_response(
            response,
            method='POST',
            formdata=formulario,
            callback=self.submit_form
        )

    # Criar o formulario com autorizacao e submiter
    def submit_form(self, response):
        formulario = self.json_file_to_dict('concluir')

        formulario["RegistroAns"] = response.selector.xpath('//*[@id="RegistroAns"]/@value').get()
        formulario["NroGspSolicitacao"] = response.selector.xpath('//*[@id="NroGspSolicitacao"]/@value').get()
        formulario["DtaValidadeCartao"] = response.selector.xpath('//*[@id="DtaValidadeCartao"]/@value').get()
        formulario["NmeCliente"] = response.selector.xpath('//*[@id="NmeCliente"]/@value').get()
        formulario["NroCNS"] = response.selector.xpath('//*[@id="NroCNS"]/@value').get()
        formulario["DtaSolicitacao"] = response.selector.xpath('//*[@id="DtaSolicitacao"]/@value').get()
        formulario["NroContratadoPrestadorExecutante"] = response.selector.xpath('//*[@id="NroContratadoPrestadorExecutante"]/@value').get()
        formulario["NmeContratadoPrestadorExecutante"] = response.selector.xpath('//*[@id="NmeContratadoPrestadorExecutante"]/@value').get()
        formulario["NroContratado"] = response.selector.xpath('//*[@id="NroContratado"]/@value').get()
        formulario["TabContainerControl1$TabGeral$NroConselhoProfissionalSolicitante"] = response.selector.xpath('//*[@id="TabContainerControl1$TabGeral$NroConselhoProfissionalSolicitante"]/@value').get()
        formulario["TabContainerControl1$TabGeral$NroCartao"] = response.selector.xpath('//*[@id="TabContainerControl1$TabGeral$NroCartao"]/@value').get()
        formulario["TabContainerControl1$TabGeral$NroUFConselhoProfissionalSolicitante"] = response.selector.xpath('//*[@id="TabContainerControl1$TabGeral$NroUFConselhoProfissionalSolicitante"]/@value').get()
        formulario["TabContainerControl1$TabGeral$DesIndicacaoClinica"] = response.selector.xpath('//*[@id="TabContainerControl1$TabGeral$DesIndicacaoClinica"]/@value').get()
        
        return scrapy.FormRequest.from_response(
            response, 
            method='POST',
            formdata=formulario, 
            callback=self.callback
        )

    # Carregar formulario e submeter
    def callback(self, response): 
        # import ipdb; ipdb.set_trace()
        scrapy.utils.response.open_in_browser(response)
        
        msg_error = response.selector.xpath('//*[@class="ErrorMessage"]/text()').get()
        if msg_error:
            
            for i in range(2):
                if i == 0:
                    yield { "status": "error", "message": msg_error }
                
                else: 
                    url_voltar = response.selector.xpath('//*[@id="btnVoltar"]/@onclick').get()
                    nro_gsp_solicitacao = re.findall("(\?|\&)([^=]+)\=([^&]+)", url_voltar)[1][2]

                    # cancelar a edicao que obteve erro
                    if nro_gsp_solicitacao: 
                        yield scrapy.FormRequest.from_response(
                            response, 
                            method='POST',
                            formdata={
                                "Transaction": "Cancelar",
                                "PostBack": "false",
                                "NroGspSolicitacao": nro_gsp_solicitacao
                            }, 
                            callback=self.cancelar
                        )

    def cancelar(self, response): 
        form_action = response.selector.xpath('//*[@id="MainForm"]/@action').get()
        nro_gsp_solicitacao = re.findall("(\?|\&)([^=]+)\=([^&]+)", form_action)[1][2]
        yield { "action": "cancelar", "status": "success", "nro_gsp_solicitacao":nro_gsp_solicitacao }

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
        content = pkgutil.get_data("oniAutorizacao","resources/formularios/{}.json".format(file_name))
        return dict( json.loads( content ))

