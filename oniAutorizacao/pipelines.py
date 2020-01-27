# -*- coding: utf-8 -*-
from datetime import datetime
import os 
class OniautorizacaoPipeline(object):
    def process_item(self, item, spider):
        item.setdefault('numero_guia', "")
        item.setdefault('senha', "")
        item.setdefault('status', "")
        item.setdefault('erro', None)
        return item

    def open_spider(self, spider):
        spider.started_on = datetime.now() 
    
    def close_spider(self, spider):
        if spider.anexo_path: 
            os.remove( spider.anexo_path )
        work_time = datetime.now() - spider.started_on
        spider.logger.info('Ended in %8.3f seconds', work_time.total_seconds())

