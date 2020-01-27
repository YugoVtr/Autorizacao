from oniAutorizacao.util.estados import Estados
import requests
from requests.exceptions import MissingSchema

class GeapHandle(object):
    def validar_inicio_execucao(self, solicitacao):
        try:
            assert "numero_cartao" in solicitacao, "Campo 'numero_cartao' obrigatorio."
            assert "numero_conselho" in solicitacao, "Campo 'numero_conselho' obrigatorio."
            assert "uf_conselho" in solicitacao, "Campo 'uf_conselho' obrigatorio."
            assert "indicacao_clinica" in solicitacao, "Campo 'indicacao_clinica' obrigatorio."
            assert "procedimento" in solicitacao, "Campo 'procedimento' obrigatorio."
            assert "quantidade_solicitada" in solicitacao, "Campo 'quantidade_solicitada' obrigatorio."
            assert "anexo_url" in solicitacao, "Campo 'anexo_url' obrigatorio."
            assert solicitacao["uf_conselho"] in [ i.name for i in Estados ], "'uf_conselho' invalido"

            response = requests.head(solicitacao['anexo_url'])
            assert response.headers['Content-Type'] == 'application/pdf', "Indique um documento PDF como anexo"
            assert int( response.headers['Content-Length'] ) < (2 * 10 ** 6), "Anexo deve possuir tamanho maximo de 2MB"
            
            return None    
        except MissingSchema as error:
            return Exception("URL do anexo invalida")
        except Exception as error:
            return error
