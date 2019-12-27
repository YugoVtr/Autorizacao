# -*- coding: utf-8 -*-
from datetime import datetime

class OniautorizacaoPipeline(object):
    def process_item(self, item, spider):
        return item

    def open_spider(self, spider):
        spider.started_on = datetime.now() 
    
    def close_spider(self, spider):
        work_time = datetime.now() - spider.started_on
        spider.logger.info('Ended in %8.3f seconds', work_time.total_seconds())

