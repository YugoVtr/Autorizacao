.PHONY: all run api dev deploy clean bootstrap

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
		-d job_settings='{"LOG_LEVEL": "WARNING"}'
	curl -u $(APIKEY): https://storage.scrapinghub.com/items/425142/1

dev: 
	echo > oniAutorizacao/resources/logs/itens.json
	scrapy crawl geap -o oniAutorizacao/resources/logs/itens.json

deploy:
	shub deploy 425142

clean:
	rm -rf ./logs/*

bootstrap: 
	pip install -r requirements.txt
	mkdir -p logs
