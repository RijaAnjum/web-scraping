from web_scraping.spiders.utils import barcode_type, clean_text
from web_scraping.items import SainsburysCrawlerItem
import scrapy
import json

class SainburysSpider(scrapy.Spider):
    name = "sainsburys_crawler" 
    start_urls = ["https://www.sainsburys.co.uk/shop/AjaxGetImmutableZDASView?requesttype=ajax&storeId=10151&langId=44&catalogId=10241&slot="]
    seen_skus = set()
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
        try:
            products_url = response.xpath("(//h2[contains(@data-test-id,'product-tile-description')] | //div[contains(@class,'productNameAndPromotions')]//h3/a/@href)").extract()
            yield from response.follow_all(products_url, callback=self.parse_product_api)
        except:
            print("Exception in parse_products Method!!")      

    def parse_product_api(self, response):
        try:
            product_path = response.url.split("/product/")[1].replace("/", "%2F")
            product_url = f"https://www.sainsburys.co.uk/groceries-api/gol-services/product/v1/product?filter[product_seo_url]=gb%2Fgroceries%2F{product_path}&include[ASSOCIATIONS]=true&include[PRODUCT_AD]=citrus"
            yield scrapy.Request(product_url, callback=self.parse_details)
        except:
            print("Exception in parse_product_api Method!!")  

    def parse_details(self, response):    
        try:  
            data = json.loads(response.body)
            for detail in data.get('products', []):
                has_variants = bool(detail.get('multivariants', []))     
                for variant in (detail.get('multivariants', []) if has_variants else [None]):
                    item = SainsburysCrawlerItem()
                    if has_variants and variant:
                        item['Url'] = detail.get("full_url", '')+"?ah="+variant.get('product_uid', '')
                        item['sku'] = variant.get('product_uid', '')
                        item['Price'] = float(variant.get("retail_price", {}).get('price', 0) or 0.0)
                        item['Title'] = clean_text(detail.get("name", '')) + " " +clean_text(variant.get('display_name', ''))
                        item['hasVariations'] = True
                    else:
                        item['Url'] = detail.get("full_url", '')
                        item['sku'] = detail.get("reviews", {}).get('product_uid', '')
                        item['Price'] = float(detail.get("retail_price", {}).get('price', 0) or 0.0)
                        item['Title'] = clean_text(detail.get("name", ''))
                        item['hasVariations'] = False
                    
                    item['Brand'] = clean_text(detail.get('attributes', {}).get('brand', ''))
                    item['Availability'] = detail.get('is_available', False)
                    item['Barcode'] = str(detail.get('eans', [''])[0]) if detail.get('eans').isdigit() else ''
                    item['BarcodeType'] = barcode_type(item['Barcode'])
                    item['Description'] = clean_text(detail.get('description', '')) 
                    item['isPriceExcVAT'] = False  
                    item['mpn'] = ""  
                    item['Offer'] = clean_text(detail.get('promotions', [{}])[0].get('strap_line', '') if detail.get('promotions') else '')
                    item['Size'] = ""  
                    item['Color'] = ""     
                    item['Image'] = next(
                                    (size.get('url')
                                    for image in detail.get('assets', {}).get('images', [])
                                    for size in image.get('sizes', [])
                                    if image.get('sizes') and image.get('id') == "1"),
                                    None
                    )
                    item['Images'] = [image['sizes'][0].get('url') 
                                        for image in detail.get('assets', {}).get('images', [])
                                        if image.get('sizes') 
                                        ]

                    if item['sku'] and item['sku'] not in self.seen_skus:
                        self.seen_skus.add(item['sku'])
                        yield item
        except:
            print("Exception in parse_details Method!!")              