# -*- coding: utf-8 -*-
import scrapy, logging, json, re, pkgutil, time, requests, codecs
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
            callback=self.preencher_formulario)

    def preencher_formulario(self, response):
        formulario = self.json_file_to_dict('form_new')
        formulario["TabContainerControl1$TabGeral$NroCartao"] = "901004143630084"
        formulario["TabContainerControl1$TabGeral$NroConselhoProfissionalSolicitante"] = "8158"
        formulario["TabContainerControl1$TabGeral$NroUFConselhoProfissionalSolicitante"] = "52"
        formulario["TabContainerControl1$TabGeral$DesIndicacaoClinica"] = "DORES ABDOMINAIS"
        formulario["TabContainerControl1$TabProcedimento$NroServicoGridRegulacao"] = "40808050"
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

        if id_solicitacao and nro_cartao and nro_contratado:
            logging.warning("id da solicitacao => {}".format(id_solicitacao))
            base = "https://www.geap.com.br/regulacaotiss/Anexacao_Laudo/AnexaLaudo.aspx"
            bind = "?NroCartao={cartao}&NroGspSolicitacao={id}&NroContratado={contratado}"
            param = bind.format(cartao=nro_cartao, id=id_solicitacao, contratado=nro_contratado)
            url="{0}{1}".format(base, param)
            return response.follow(url=url, callback=self.anexar)

    def anexar(self, response):
        base_path = "oniAutorizacao/resources"

        inputs = self.get_all_inputs_from_response(response)
        viewstate = inputs['__VIEWSTATE']
        viewstategenerator = inputs['__VIEWSTATEGENERATOR']

        files = {
            "__VIEWSTATE":(None, viewstate),
            "__VIEWSTATEGENERATOR":(None, viewstategenerator),
            "fupDoc": ('anexo.pdf', open("{}/anexos/anexo.pdf".format(base_path), "rb"), "application/pdf"),
            "btnAdicionar.x": (None, "12"),
            "btnAdicionar.y": (None, "8")    
        }

        cookies = self.raw_header_to_dict(response.request.headers['Cookie'])
        prepare = requests.Request('POST', response.url, files=files, cookies=cookies).prepare()
        headers = prepare.headers
        body = prepare.body

        return scrapy.Request(
            url=response.url,
            headers=headers,
            cookies=cookies,
            body=body,
            method="POST",
            callback=self.concluir_anexo
        )

    def concluir_anexo(self, response):
        base_path = "oniAutorizacao/resources"
        with open("{}/body2.txt".format(base_path), "r") as file:
            content = file.read()

            boundary = hash(time.time())
            inputs = self.get_all_inputs_from_response(response)
            eventtarget = ""
            eventargument = ""
            viewstate = inputs['__VIEWSTATE']
            viewstategenerator = inputs['__VIEWSTATEGENERATOR']

            content = content.format(
                boundary=boundary,
                viewstate=viewstate,
                viewstategenerator=viewstategenerator,
                eventtarget=eventtarget,
                eventargument=eventargument
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
                callback=self.redirecionar_para_edicao
            )
            return request

    def redirecionar_para_edicao(self, response):
        menssagem = response.selector.xpath('//*[@id="lblMessage"]/text()').get()
        parametros = re.findall("[0-9]+", menssagem)
        base = "https://www.geap.com.br/regulacaoTiss/solicitacoes/SolicitacaoSADT.aspx"
        param = "?Transaction=FormEdit&NroGspSolicitacao={}&NroTpoSolicitacao=3".format(parametros[0])
        return response.follow(
            url= base + param, 
            callback=self.concluir_formulario
        )

    def concluir_formulario(self, response):
        return {}
        formulario = self.json_file_to_dict('concluir')

        return scrapy.FormRequest.from_response(
            response,
            method='POST',
            formdata=formulario,
            callback=self.processar_resultado
        )

    def processar_resultado(self, response):
        msg_error = response.selector.xpath('//*[@class="ErrorMessage"]/text()').get()
        if msg_error:
            yield { "status": "error", "message": msg_error }
        else: 
            regex = '"\/regulacaoTiss\/report\/resumoautorizacao\.aspx\?.*"'
            match = re.findall(regex, response.body.decode('UTF-8'))
            url = match[0].replace('"', '')
            return response.follow(url=url, callback=self.obter_senha)

    def obter_senha(self, response):
        import ipdb; ipdb.set_trace()

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
