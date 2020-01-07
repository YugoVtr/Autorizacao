.PHONY: all run clean bootstrap

all: 
ifneq ($(wildcard logs),)
	make http
else
	make bootstrap
	make http
endif

http: 
	scrapyrt -p 3000

run:
	scrapy crawl geap

clean:
	rm -rf ./logs/*

bootstrap: 
	pip install -r requirements.txt
	mkdir -p logs
