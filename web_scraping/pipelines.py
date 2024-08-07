# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import csv

class WebScrapingPipeline:
    def process_item(self, item, spider):
        return item

class CsvWriterPipeline:
    def __init__(self):
        self.file = open('evanscycles_data.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.file, fieldnames=[
            'Url', 'Brand', 'Price', 'sku', 'Availability',
            'Barcode','BarcodeType', 'Description', 'Title', 'hasVariations',
            'isPriceExcVAT', 'mpn', 'Offer', 'Size','Color', 'Image', 'Images'
        ])
        self.writer.writeheader()

    def process_item(self, item, spider):
        self.writer.writerow(item)
        return item

    def close_spider(self, spider):
        self.file.close()