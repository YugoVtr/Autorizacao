# -*- coding: utf-8 -*-
import scrapy, logging, json, re, pkgutil, time, requests
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError


class GeapSpider(scrapy.Spider):
    name = "geap"
    allowed_domains = ["geap.com.br"]
    start_urls = [
        "https://www.geap.com.br/Login.aspx?ReturnUrl=regulacaoTiss/default.aspx&Procedure=ww_usr_CheckWWWPrestador"
    ]

    def __init__(self, solicitacao={}, *args, **kwargs):
        super(GeapSpider, self).__init__(*args, **kwargs)

        solicitacao = self.str_to_json(solicitacao)

        # valida parametros
        assert "numero_cartao" in solicitacao
        assert "numero_conselho" in solicitacao
        assert "uf_conselho" in solicitacao
        assert "indicacao_clinica" in solicitacao
        assert "procedimento" in solicitacao
        assert "quantidade_solicitada" in solicitacao
        assert "anexo_url" in solicitacao

        self.solicitacao = solicitacao

    # Faz o login
    def parse(self, response):
        form_autenticacao = self.json_file_to_dict("autenticacao")
        return scrapy.FormRequest.from_response(
            response, formdata=form_autenticacao, callback=self.abrir_formulario
        )

    def abrir_formulario(self, response):
        return scrapy.FormRequest(
            url="https://www.geap.com.br/regulacaoTiss/solicitacoes/SolicitacaoSADT.aspx",
            method="POST",
            formdata={"Transaction": "FormNew"},
            callback=self.preencher_formulario,
        )

    def preencher_formulario(self, response):
        formulario = self.json_file_to_dict("form_new")
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
        ] = self.solicitacao["quantidade_solicitada"]

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
            logging.info("id da solicitacao => {}".format(id_solicitacao))
            base = (
                "https://www.geap.com.br/regulacaotiss/Anexacao_Laudo/AnexaLaudo.aspx"
            )
            bind = (
                "?NroCartao={cartao}&NroGspSolicitacao={id}&NroContratado={contratado}"
            )
            param = bind.format(
                cartao=nro_cartao, id=id_solicitacao, contratado=nro_contratado
            )
            url = "{0}{1}".format(base, param)
            return response.follow(url=url, callback=self.anexar)

    def anexar(self, response):
        path = self.solicitacao["caminho_anexo"]
        file_name = path.split("/")[-1]
        inputs = self.get_all_inputs_from_response(response)
        viewstate = inputs["__VIEWSTATE"]
        viewstategenerator = inputs["__VIEWSTATEGENERATOR"]

        files = {
            "__VIEWSTATE": (None, viewstate),
            "__VIEWSTATEGENERATOR": (None, viewstategenerator),
            "fupDoc": (file_name, open(path, "rb"), "application/pdf"),
            "btnAdicionar.x": (None, "12"),
            "btnAdicionar.y": (None, "8"),
        }

        cookies = self.raw_header_to_dict(response.request.headers["Cookie"])
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

            inputs = self.get_all_inputs_from_response(response)
            viewstate = inputs["__VIEWSTATE"]
            viewstategenerator = inputs["__VIEWSTATEGENERATOR"]

            content = content.format(
                boundary="X-ONI-AUTORIZACAO",
                viewstate=viewstate,
                viewstategenerator=viewstategenerator,
            )

            cookies = self.raw_header_to_dict(response.request.headers["Cookie"])
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
            base = "https://www.geap.com.br/regulacaoTiss/solicitacoes/SolicitacaoSADT.aspx"
            param = "?Transaction=FormEdit&NroGspSolicitacao={}&NroTpoSolicitacao=3".format(
                id_requisicao
            )
            return response.follow(url=base + param, callback=self.concluir_formulario)

    def concluir_formulario(self, response):
        formulario = self.json_file_to_dict("concluir")
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
            yield {"status": "error", "message": msg_error}
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
        yield {"numero_guia": id_requisicao, "senha": senha, "status": status}

    ############################# FUNCOES HELPERS #############################
    def json_file_to_dict(self, file_name):
        content = pkgutil.get_data(
            "oniAutorizacao", "resources/formularios/{}.json".format(file_name)
        )
        return dict(json.loads(content))

    def raw_header_to_dict(self, raw):
        header = {}
        for i in raw.decode("utf-8").split(";"):
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

    def str_to_json(self, json_string):
        if isinstance(json_string, str):
            try:
                return json.loads(json_string)
            except:
                return {}
        elif isinstance(json_string, dict):
            return json_string
        else:
            return {}
