# -*- coding: utf-8 -*-
import scrapy, logging, json, re, requests, os
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

from oniAutorizacao.items import OniautorizacaoItem
from oniAutorizacao.util.estados import Estados
from oniAutorizacao.util import helpers
from oniAutorizacao.util.handle import GeapHandle


class GeapSpider(scrapy.Spider):
    name = "geap"
    allowed_domains = ["geap.com.br"]
    start_urls = [
        "https://www.geap.com.br/Login.aspx?Procedure=ww_usr_CheckWWWPrestador"
    ]    

    def __init__(self, solicitacao={}, *args, **kwargs):
        super(GeapSpider, self).__init__(*args, **kwargs)
        self.solicitacao = solicitacao
        self.item = OniautorizacaoItem()
        self.anexo_path = None
        self.base_url = "https://www.geap.com.br"
        self.handle = GeapHandle()

    def parse(self, response):
        try:  # valida entradas
            self.solicitacao = helpers.str_to_json(self.solicitacao)
            error = self.handle.validar_inicio_execucao(self.solicitacao)
            if error:
                self.item["erro"] = str(error)
                return self.item
            self.solicitacao["uf_conselho"] = str(
                Estados[self.solicitacao["uf_conselho"]].value
            )
        except Exception as error:
            self.item["erro"] = str(error)
            return self.item

        form_autenticacao = helpers.json_file_to_dict("autenticacao")
        return scrapy.FormRequest.from_response(
            response, formdata=form_autenticacao, callback=self.abrir_formulario
        )

    def abrir_formulario(self, response):
        return scrapy.FormRequest(
            url="%s/regulacaoTiss/solicitacoes/SolicitacaoSADT.aspx" % self.base_url,
            method="POST",
            formdata={"Transaction": "FormNew"},
            callback=self.preencher_formulario,
        )

    def preencher_formulario(self, response):
        formulario = helpers.json_file_to_dict("form_new")
        formulario["TabContainerControl1$TabGeral$NroCartao"] = self.solicitacao[
            "numero_cartao"
        ]
        formulario[
            "TabContainerControl1$TabGeral$NroConselhoProfissionalSolicitante"
        ] = self.solicitacao["numero_conselho"]
        formulario[
            "TabContainerControl1$TabGeral$NroUFConselhoProfissionalSolicitante"
        ] = self.solicitacao["uf_conselho"]
        formulario[
            "TabContainerControl1$TabGeral$DesIndicacaoClinica"
        ] = self.solicitacao["indicacao_clinica"]
        formulario[
            "TabContainerControl1$TabProcedimento$NroServicoGridRegulacao"
        ] = self.solicitacao["procedimento"]
        formulario[
            "TabContainerControl1$TabProcedimento$QtdSolicitadaGridRegulacao"
        ] = str( self.solicitacao["quantidade_solicitada"] )

        return scrapy.FormRequest.from_response(
            response, method="POST", formdata=formulario, callback=self.verificar_anexo
        )

    def verificar_anexo(self, response):
        id_solicitacao = response.selector.xpath(
            '//*[@id="NroGspSolicitacao"]/@value'
        ).get()
        nro_cartao = response.selector.xpath(
            '//*[@id="TabContainerControl1_TabGeral_NroCartao"]/@value'
        ).get()
        nro_contratado = response.selector.xpath(
            '//*[@id="NroContratadoPrestadorExecutante"]/@value'
        ).get()

        if id_solicitacao and nro_cartao and nro_contratado:
            self.item["numero_guia"] = id_solicitacao
            base = "%s/regulacaotiss/Anexacao_Laudo/AnexaLaudo.aspx" % self.base_url
            bind = (
                "?NroCartao={cartao}&NroGspSolicitacao={id}&NroContratado={contratado}"
            )
            param = bind.format(
                cartao=nro_cartao, id=id_solicitacao, contratado=nro_contratado
            )
            url = "{0}{1}".format(base, param)
            return response.follow(url=url, callback=self.anexar)

    def anexar(self, response):
        self.anexo_path = helpers.save_pdf_from_url(self.solicitacao["anexo_url"])
        file_name = self.anexo_path.split("/")[-1]
        inputs = helpers.get_all_inputs_from_response(response)
        viewstate = inputs["__VIEWSTATE"]
        viewstategenerator = inputs["__VIEWSTATEGENERATOR"]

        files = {
            "__VIEWSTATE": (None, viewstate),
            "__VIEWSTATEGENERATOR": (None, viewstategenerator),
            "fupDoc": (file_name, open(self.anexo_path, "rb"), "application/pdf"),
            "btnAdicionar.x": (None, "12"),
            "btnAdicionar.y": (None, "8"),
        }

        cookies = helpers.raw_header_to_dict(response.request.headers["Cookie"])
        prepare = requests.Request(
            "POST", response.url, files=files, cookies=cookies
        ).prepare()
        headers = prepare.headers
        body = prepare.body

        return scrapy.Request(
            url=response.url,
            headers=headers,
            cookies=cookies,
            body=body,
            method="POST",
            callback=self.concluir_anexo,
        )

    def concluir_anexo(self, response):
        base_path = "oniAutorizacao/resources"
        with open("{}/body.txt".format(base_path), "r") as file:
            content = file.read()

            inputs = helpers.get_all_inputs_from_response(response)
            viewstate = inputs["__VIEWSTATE"]
            viewstategenerator = inputs["__VIEWSTATEGENERATOR"]

            content = content.format(
                boundary="X-ONI-AUTORIZACAO",
                viewstate=viewstate,
                viewstategenerator=viewstategenerator,
            )

            cookies = helpers.raw_header_to_dict(response.request.headers["Cookie"])
            headers = {
                "Content-Type": "multipart/form-data; boundary=X-ONI-AUTORIZACAO"
            }
            id_requisicao = re.findall(
                "[0-9]+", response.selector.xpath("//form/@action").get()
            )[1]
            return scrapy.Request(
                url=response.url,
                headers=headers,
                cookies=cookies,
                body=content,
                method="POST",
                cb_kwargs={"id_requisicao": id_requisicao},
                callback=self.redirecionar_para_edicao,
            )

    def redirecionar_para_edicao(self, response, id_requisicao):
        if id_requisicao:
            base = "%s/regulacaoTiss/solicitacoes/SolicitacaoSADT.aspx" % self.base_url
            param = (
                "?Transaction=FormEdit&NroGspSolicitacao=%s&NroTpoSolicitacao=3"
                % id_requisicao
            )
            return response.follow(url=base + param, callback=self.concluir_formulario)

    def concluir_formulario(self, response):
        formulario = helpers.json_file_to_dict("concluir")
        id_requisicao = response.selector.xpath(
            "//*[@id='NroGspSolicitacao']/@value"
        ).get()

        return scrapy.FormRequest.from_response(
            response,
            method="POST",
            formdata=formulario,
            cb_kwargs={"id_requisicao": id_requisicao},
            callback=self.verificar_resultado,
        )

    def verificar_resultado(self, response, id_requisicao):
        msg_error = response.selector.xpath('//*[@class="ErrorMessage"]/text()').get()
        if msg_error:
            self.item["erro"] = re.sub(r"\r|\n|\t", "", msg_error).strip()
            yield self.item

        elif id_requisicao:
            yield scrapy.FormRequest.from_response(
                response,
                method="POST",
                formdata={
                    "Transaction": "FormEdit",
                    "PostBack": "false",
                    "NroGspSolicitacao": id_requisicao,
                },
                callback=self.finalizar,
            )

    def finalizar(self, response):
        id_requisicao = response.selector.xpath(
            "//*[@id='NroGspSolicitacao']/@value"
        ).get()
        status = response.selector.xpath('//*[@id="StaSolicitacao_fixed"]/text()').get()

        match_senha = re.match(
            "[0-9]+",
            response.selector.xpath(
                "//*[@id='NroSenhaAutorizacao_fixed']/text()"
            ).get(),
        )
        senha = match_senha.group(0) if match_senha else ""

        self.item["numero_guia"] = id_requisicao
        self.item["senha"] = senha
        self.item["status"] = status
        yield self.item
