# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from datetime import datetime


class ScrapPipeline(object):
    def process_item(self, item, spider):
        return item

import pymongo


class MongoPipeline(object):

    collection_name = 'members'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'intranet')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        # http://docs.mongodb.org/manual/reference/operator/update/setOnInsert/
#        if item.get_collection_name() == "members":
#            try:
#                self.db[item.get_collection_name()].insert(dict(item))
#            except pymongo.errors.DuplicateKeyError:
#                if "id" in dict(item).keys():
#                    self.db[item.get_collection_name()].update(
#                        { "id": item["id"]},
#                        { "$set": dict(item) }
#                    )
#        else:
        self.db[item.get_collection_name()].update(
                dict(item),
                {
                    "$set": dict(item),
                    "$setOnInsert": { "timestamp": datetime.now() }
                },
                upsert=True
            )

        return item
