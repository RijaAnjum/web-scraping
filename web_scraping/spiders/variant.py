from web_scraping.spiders.utils import barcode_type, clean_text
from web_scraping.items import SainsburysCrawlerItem
import scrapy
import json

class SainburysSpider(scrapy.Spider):
    name = "var" 
    start_urls = ["https://www.sainsburys.co.uk/shop/AjaxGetImmutableZDASView?requesttype=ajax&storeId=10151&langId=44&catalogId=10241&slot="]
    custom_settings = {
        'FEEDS': {
            'var.json': {
                'format': 'json',
                'overwrite': True,
                'indent': 4,
            },
        },
        'FEED_EXPORT_ENCODING': 'utf-8',
    }              
    def parse(self, response):
        try:
            data = json.loads(response.text)
            for item in data.get('navList', []):
                category_id = item.get('id')
                url = f'https://www.sainsburys.co.uk/shop/CategorySeeAllView?listId=&catalogId=10241&searchTerm=&beginIndex=0&pageSize=120&orderBy=FAVOURITES_FIRST&top_category=&langId=44&storeId=10151&categoryId={category_id}&promotionId=&parent_category_rn='
                yield scrapy.Request(url, callback=self.parse_categories, meta={"category_id": category_id})   
        except:
            print("Exception in parse Method!!")     

    def parse_categories(self, response):
        try:
            yield from self.parse_products(response)
            category_id = response.meta['category_id']
            index_count = response.meta.get('index_count', 0)
            next_page = response.xpath("//li[@class='next']/a/@href").get()
            if next_page:
                index_count += 120
                url = f'https://www.sainsburys.co.uk/shop/CategorySeeAllView?listId=&catalogId=10241&searchTerm=&beginIndex={index_count}&pageSize=120&orderBy=FAVOURITES_FIRST&top_category=&langId=44&storeId=10151&categoryId={category_id}&promotionId=&parent_category_rn='
                yield scrapy.Request(url, callback=self.parse_categories, meta={'category_id': category_id, 'index_count': index_count})
        except:
            print("Exception in parse_categories Method!!")
    def parse_products(self, response): 
        yield {
            "url": response.url
        }
