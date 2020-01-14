.PHONY: all run http dev clean bootstrap

all: 
ifneq ($(wildcard logs),)
	make http
else
	make bootstrap
	make http
endif

run:
	scrapy crawl geap

http: 
	scrapyrt -p 3000

dev: 
	echo > resources/logs/itens.json
	scrapy crawl geap -o resources/logs/itens.json

clean:
	rm -rf ./logs/*

bootstrap: 
	pip install -r requirements.txt
	mkdir -p logs
