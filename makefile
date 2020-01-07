.PHONY: run clean bootstrap

run:
	scrapy crawl geap

clean:
	rm -rf ./logs/*

bootstrap: 
	pip install -r requirements.txt
	make clean
