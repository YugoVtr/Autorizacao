.PHONY: all run api dev deploy bootstrap

APIKEY = 0cb86e0da29249e8a5f15982f9495452

all: 
ifneq ($(wildcard scrapinghub.yml),)
	make api
else
	make dev
endif

run:
	scrapy crawl geap

api: 
	curl -u $(APIKEY): https://app.scrapinghub.com/api/run.json \
		-d project=425142 \
		-d spider=geap \
		-d job_settings='{"LOG_LEVEL": "WARNING"}' \
		-a solicitacao={"numero_cartao" : "901004143630084","numero_conselho" : "8158","uf_conselho" : "52","indicacao_clinica" : "FORTES DORES ABDOMINAIS","procedimento" : "40808041","quantidade_solicitada" : "2","caminho_anexo": "oniAutorizacao/resources/anexos/anexo.pdf"}
	curl -u $(APIKEY): https://storage.scrapinghub.com/items/425142/1

dev: 
	echo > oniAutorizacao/resources/logs/itens.json
	scrapy crawl geap -o oniAutorizacao/resources/logs/itens.json \
		-a solicitacao='{"numero_cartao" : "901004143630084","numero_conselho" : "8158","uf_conselho" : "52","indicacao_clinica" : "FORTES DORES ABDOMINAIS","procedimento" : "40808041","quantidade_solicitada" : "2","caminho_anexo": "oniAutorizacao/resources/anexos/anexo.pdf"}'
	}

deploy:
	shub deploy 425142

bootstrap: 
	pip install -r requirements.txt
