# -*- coding: utf-8 -*-
import scrapy, logging, json, re, pkgutil, random, time
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
            formdata={"Transaction": "FormNew"},
            callback=self.verificar_anexo)

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
        id_solicitacao =  response.selector.xpath('//*[@id="NroGspSolicitacao"]/@value').get() or 358461440
        nro_cartao = response.selector.xpath('//*[@id="TabContainerControl1_TabGeral_NroCartao"]/@value').get() or 901004143630084
        nro_contratado = response.selector.xpath('//*[@id="NroContratadoPrestadorExecutante"]/@value').get() or 23022809

        if id_solicitacao and nro_cartao and nro_contratado:
            base = "https://www.geap.com.br/regulacaotiss/Anexacao_Laudo/AnexaLaudo.aspx"
            bind = "?NroCartao={cartao}&NroGspSolicitacao={id}&NroContratado={contratado}"
            param = bind.format(cartao=nro_cartao, id=id_solicitacao, contratado=nro_contratado)
            url="{0}{1}".format(base, param)
            return response.follow(url=url, callback=self.anexar)

    def anexar(self, response):
        base_path = "oniAutorizacao/resources"
        with open("{}/body.txt".format(base_path), "r") as file:
            content = file.read()

            boundary = hash(time.time())
            inputs = self.get_all_inputs_from_response(response)
            import ipdb; ipdb.set_trace()
            viewstate = inputs['__VIEWSTATE']
            viewstategenerator = inputs['__VIEWSTATEGENERATOR']

            with open("{}/anexos/anexo.pdf".format(base_path), "rb") as file_anexo:
                anexo = file_anexo.read()

            content = content.format(
                boundary=boundary,
                viewstate=viewstate,
                viewstategenerator=viewstategenerator,
                anexo=anexo
            )

            cookies = self.raw_header_to_dict(response.request.headers['Cookie'])
            headers = {
                "Content-Type": "multipart/form-data; boundary={}".format(boundary)
            }
            request = scrapy.Request(
                url=response.url,
                headers=headers,
                cookies=cookies,
                body=content,
                method="POST",
                callback=self.concluir_anexo
            )
            return request

    def concluir_anexo(self, response):
        pass

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

    def raw_header_to_dict(self, raw):
        header = {}
        for i in raw.decode('utf-8').split(";"):
            item = [j.strip() for j in i.split("=")]
            if len(item) == 2:
                header[item[0]] = item[1]
        return header

    def get_all_inputs_from_response(self, response):
        inputs = response.selector.xpath("//input")
        result = {}
        for i in inputs:
            result[i.xpath("@name").get()] = i.xpath("@value").get()
        return result
