# -*- coding: utf-8 -*-
import scrapy, logging, json, re, pkgutil, random
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
            callback=self.verificar_anexo
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
            callback=self.verificar_anexo
        )

    def verificar_anexo(self, response):
        id_solicitacao =  response.selector.xpath('//*[@id="NroGspSolicitacao"]/@value').get()
        nro_cartao = response.selector.xpath('//*[@id="TabContainerControl1_TabGeral_NroCartao"]/@value').get()
        nro_contratado = response.selector.xpath('//*[@id="NroContratadoPrestadorExecutante"]/@value').get()

        if True:# id_solicitacao and nro_cartao and nro_contratado:
            base = "https://www.geap.com.br/regulacaotiss/Anexacao_Laudo/AnexaLaudo.aspx"
            bind = "?NroCartao={cartao}&NroGspSolicitacao={id}&NroContratado={contratado}"
            param = bind.format(cartao=nro_cartao, id=id_solicitacao, contratado=nro_contratado)
            url="{0}{1}".format(base, param)
            url="https://www.geap.com.br/regulacaotiss/Anexacao_Laudo/AnexaLaudo.aspx?NroCartao=901004143630084&NroGspSolicitacao=358159700&NroContratado=23022809"
            return response.follow(url=url, callback=self.anexar)            
    
    def anexar(self, response):
        file_name = "anexo"
        anexo = ""
        payload = ""
        boundary = ("-" * 27) + str( random.randint(10**14, 10**15) )
        viewstate = response.selector.xpath('//*[@id="__VIEWSTATE"]/@value').get()
        viewstategenerator = response.selector.xpath('//*[@id="__VIEWSTATEGENERATOR"]/@value').get()
        eventvalidation = response.selector.xpath('//*[@id="__EVENTVALIDATION"]/@value').get()

        base_path = "oniAutorizacao/resources"
        path_anexo = "{base}/anexos/{file_name}.pdf".format(base=base_path, file_name=file_name)
        with open(path_anexo, "rb") as file:
            anexo = file.read()

        with open("{base}/anexo_body.txt".format(base=base_path), "r") as file:
            payload = file.read().format(
                file_name=file_name,
                anexo=anexo,
                boundary=boundary,
                viewstate=viewstate,
                viewstategenerator=viewstategenerator, 
                eventvalidation=eventvalidation
            )

        content_type = "multipart/form-data; boundary={0}".format(boundary)
        content_length = len(payload)
        return scrapy.FormRequest.from_response(
            response, 
            body=payload, 
            headers={
                "Content-Length": content_length,
                "Content-Type": content_type
            }, 
            callback=self.teste
        )

    def teste(self, response):
        import ipdb; ipdb.set_trace()
        
    def concluir_formulario(self, response):
        formulario = self.json_file_to_dict('concluir')

        return scrapy.FormRequest.from_response(
            response, 
            method='POST',
            formdata=formulario, 
            callback=self.callback
        )

    def callback(self, response): 
        # import ipdb; ipdb.set_trace()
        # scrapy.utils.response.open_in_browser(response)
        
        msg_error = response.selector.xpath('//*[@class="ErrorMessage"]/text()').get()
        if msg_error:
            yield { "status": "error", "message": msg_error }

    ############################# FUNCOES HELPERS #############################
    def json_file_to_dict(self, file_name):
        content = pkgutil.get_data("oniAutorizacao","resources/formularios/{}.json".format(file_name))
        return dict( json.loads( content ))

