import scrapy, json, subprocess, time, os, logging
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
        "anexo_url": fields.String(required=True, description=""),
    },
)

def geap_spider(solicitacao):
    response = {}
    post_data = "solicitacao=%s" % json.dumps(solicitacao)
    temp_file_name = hash(time.time())

    try:
        output_path = "oniAutorizacao/resources/logs/%d.json" % temp_file_name
        subprocess.check_output(["scrapy", "crawl", "geap", "-o", output_path, "-a", post_data])
        with open(output_path, "r") as file:
            response = json.loads( file.read() )
    except:
        pass
    finally:
        os.remove(output_path)
    return response

@geap_name_space.route("")
class GeapClass(Resource):
    @app.doc(responses={200: "OK", 400: "Invalid Argument", 500: "Mapping Key Error"})
    @app.expect(model)
    def post(self):
        try:
            item = geap_spider(app.payload)
            return item
        except KeyError as e:
            geap_name_space.abort(
                500, e.__doc__, status="Could not save information", statusCode="500"
            )
        except Exception as e:
            geap_name_space.abort(
                400, e.__doc__, status="Could not save information", statusCode="400"
            )
