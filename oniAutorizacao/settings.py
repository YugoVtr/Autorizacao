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

# Login 
NROCONTRATADO = "23022809"
SENHA = "cjl38050"
SELETOR = '1'

