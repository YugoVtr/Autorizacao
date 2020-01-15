# -*- coding: utf-8 -*-
import scrapy, logging, json, re, pkgutil
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class GeapSpider(scrapy.Spider):
    name = 'geap'
    allowed_domains = ['geap.com.br']
    start_urls = ['https://www.geap.com.br/Login.aspx?ReturnUrl=regulacaoTiss/default.aspx&Procedure=ww_usr_CheckWWWPrestador']
    
    # Faz o login 
    def parse(self, response):
        form_autenticacao = self.json_file_to_dict('autenticacao')
        return scrapy.FormRequest.from_response(
            response,
            formdata=form_autenticacao,
            callback=self.abrir_formulario
        )   

    def abrir_formulario(self, response): 
        return scrapy.FormRequest(
            url="https://www.geap.com.br/regulacaoTiss/solicitacoes/SolicitacaoSADT.aspx",
            method='POST',
            formdata={"Transaction":"FormNew"},
            callback=self.preencher_formulario
        )

    def preencher_formulario(self, response):
        formulario = self.json_file_to_dict('form_new')      
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
            callback=self.concluir_formulario
        )

    # Criar o formulario com autorizacao e submiter
    def concluir_formulario(self, response):
        formulario = self.json_file_to_dict('concluir')

        return scrapy.FormRequest.from_response(
            response, 
            method='POST',
            formdata=formulario, 
            callback=self.callback
        )

    # Carregar formulario e submeter
    def callback(self, response): 
        # import ipdb; ipdb.set_trace()
        # scrapy.utils.response.open_in_browser(response)
        
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


    ############################# FUNCOES HELPERS #############################
    def json_file_to_dict(self, file_name):
        content = pkgutil.get_data("oniAutorizacao","resources/formularios/{}.json".format(file_name))
        return dict( json.loads( content ))

