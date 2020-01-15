# -*- coding: utf-8 -*-
BOT_NAME = 'oniAutorizacao'

ITEM_PIPELINES = {
    'oniAutorizacao.pipelines.OniautorizacaoPipeline': 300
}

SPIDER_MODULES = ['oniAutorizacao.spiders']
NEWSPIDER_MODULE = 'oniAutorizacao.spiders'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

LOG_LEVEL = 'INFO'

AUTOTHROTTLE_ENABLED = False 
AUTOTHROTTLE_START_DELAY = 3.0
AUTOTHROTTLE_MAX_DELAY = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
