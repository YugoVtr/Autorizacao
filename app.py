import scrapy, json, subprocess
from flask import Flask, request
from flask_restplus import Api, Resource, fields

from oniAutorizacao.spiders.geap import GeapSpider

# Examples: https://github.com/kb22/Understanding-Flask-and-Flask-RESTPlus

flask_app = Flask(__name__)
app = Api(
    app=flask_app,
    version="1.0",
    title="ONI Autorizacao",
    description="Autorização para varias operadoras",
)

geap_name_space = app.namespace("geap", description="Autorização para GEAP")

model = app.model(
    "solicitacao",
    {
        "numero_cartao": fields.String(required=True, description=""),
        "numero_conselho": fields.String(required=True, description=""),
        "uf_conselho": fields.String(required=True, description=""),
        "indicacao_clinica": fields.String(required=True, description=""),
        "procedimento": fields.String(required=True, description=""),
        "quantidade_solicitada": fields.Integer(required=True, description=""),
        "caminho_anexo": fields.String(required=True, description=""),
    },
)


def geap_spider(solicitacao):
    output_path = "oniAutorizacao/resources/logs/itens.json"
    subprocess.check_output(["scrapy", "crawl", "geap", "-o", output_path])
    with open(output_path) as response:
        return json.loads(response.read())


@geap_name_space.route("")
class GeapClass(Resource):
    @app.doc(responses={200: "OK", 400: "Invalid Argument", 500: "Mapping Key Error"})
    @app.expect(model)
    def post(self):
        try:
            item = geap_spider(app.payload)
            return {"status": "Nova Autorização criada", "item": item}
        except KeyError as e:
            geap_name_space.abort(
                500, e.__doc__, status="Could not save information", statusCode="500"
            )
        except Exception as e:
            geap_name_space.abort(
                400, e.__doc__, status="Could not save information", statusCode="400"
            )
