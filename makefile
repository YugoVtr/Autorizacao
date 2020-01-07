run:
	scrapy crawl geap

clean:
	rm -rf log/*

bootstrap: _virtualenv
	_virtualenv/bin/pip install -e .
ifneq ($(wildcard requirements.txt),)
	_virtualenv/bin/pip install -r test-requirements.txt
endif
	make clean

_virtualenv:
	python3 -m venv _virtualenv
	_virtualenv/bin/pip install --upgrade pip
	_virtualenv/bin/pip install --upgrade setuptools
	_virtualenv/bin/pip install --upgrade wheel