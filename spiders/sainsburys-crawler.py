import scrapy
import json

class SainburysSpider(scrapy.Spider):
    name = "sainburys_crawler" 
    start_urls = ["https://www.sainsburys.co.uk/shop/AjaxGetImmutableZDASView?requesttype=ajax&storeId=10151&langId=44&catalogId=10241&slot="]
                  
    custom_settings = {
        'FEEDS': {
            'sainburys_crawler.json': {
                'format': 'json',
                'overwrite': True,
                'indent': 4,
            },
        },
        'FEED_EXPORT_ENCODING': 'utf-8',
    }
    def parse(self, response):
        data = json.loads(response.text)
        for item in data.get('navList', []):
            category_id = item.get('id')
            url = f'https://www.sainsburys.co.uk/shop/CategorySeeAllView?listId=&catalogId=10241&searchTerm=&beginIndex=0&pageSize=120&orderBy=FAVOURITES_FIRST&top_category=&langId=44&storeId=10151&categoryId={category_id}&promotionId=&parent_category_rn='
            yield scrapy.Request(url, callback=self.parse_categories, meta={"category_id": category_id})    

    def parse_categories(self, response):
        yield from self.parse_products(response)
        category_id = response.meta['category_id']
        index_count = response.meta.get('index_count', 0)
        next_page = response.xpath("//li[@class='next']/a/@href").get()
        if next_page:
            index_count += 120
            url = f'https://www.sainsburys.co.uk/shop/CategorySeeAllView?listId=&catalogId=10241&searchTerm=&beginIndex={index_count}&pageSize=120&orderBy=FAVOURITES_FIRST&top_category=&langId=44&storeId=10151&categoryId={category_id}&promotionId=&parent_category_rn='
            yield scrapy.Request(url, callback=self.products, meta={'category_id': category_id, 'index_count': index_count})
   
    def parse_products(self,response):
        products_url= response.xpath("//div[contains(@class,'productNameAndPromotions')]//a/@href").extract()
        for product in products_url:
            url = product.split("product/")[1]
            product_url= f'https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product?filter[product_seo_url]=gb%2Fgroceries%2{url}&include[ASSOCIATIONS]=true&include[PRODUCT_AD]=citrus'
            yield scrapy.Request(product_url, callback=self.fetch_details)

    def fetch_details(self,response):    
        data=json.loads(response.body)
        for detail in data['products']:
            yield {
                "Title" : detail["name"],
                "image" : detail["image"],
                "url" : detail["full_url"],
                "available" : detail["is_available"],
            }

