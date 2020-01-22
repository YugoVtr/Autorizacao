import scrapy 
from scrapy.crawler import CrawlerProcess 
from oniAutorizacao.spiders.geap import GeapSpider

if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        'FEED_URI': 'oniAutorizacao/resources/logs/itens.json'
    })

    solicitacao = {
        "numero_cartao" : "901004143630084",
        "numero_conselho" : "8158",
        "uf_conselho" : "52",
        "indicacao_clinica" : "FORTES DORES ABDOMINAIS",
        "procedimento" : "40808041",
        "quantidade_solicitada" : "2",
        "caminho_anexo": "oniAutorizacao/resources/anexos/anexo.pdf"
    }

    process.crawl(GeapSpider, solicitacao=solicitacao)
    process.start()