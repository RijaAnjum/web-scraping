import scrapy
import json
import re
from web_scraping.spiders.utils import clean_text,barcode_type
from web_scraping.items import BeautyOutletItem

class BeautyOutletSpider(scrapy.Spider):
    name = "beauty_outlet_crawler"
    start_urls = ["https://www.beautyoutlet.co.uk"]
    seen_skus = set()
    def parse(self, response):
        try:
            major_categories = response.xpath("(//a[contains(@id,'shop-all')])[position()<8]/@href").extract()
            yield from response.follow_all(major_categories, callback=self.parse_sub_categories) 
        except:
            print("Exception in parse!!")

    def parse_sub_categories(self, response):
        try:
            sub_categories = list(set(response.xpath('//span[@class="icon-wrap"]/preceding::h3/a/@href').extract()))
            yield from self.parse_pagination(response)
            yield from response.follow_all(sub_categories or '', callback=self.parse_sub_categories) 
        except:
            print("Exception in parse_sub_categories!!")

    def parse_pagination(self, response):
        try:
            yield from self.parse_product(response)
            next_page = response.xpath('//a[@aria-label="Next page"]/@href').get()
            yield response.follow(next_page or '', callback=self.parse_pagination) 
        except:
            print("Exception in parse_pagination!!")    

    def parse_product(self, response):
        try:
            products = response.xpath('//h3[@class="card__heading h5"]/a/@href').extract()
            yield from response.follow_all(products, callback=self.parse_variants)
        except:
            print("Exception in parse_product!!")
        
    def parse_variants(self, response):
        try:
            script_tag = response.xpath("//script[contains(text(), 'var meta = ')]/text()").get()
            if not script_tag: return
            pattern = re.compile(r'var meta = ({.*?});', re.DOTALL)
            match = pattern.search(script_tag)
            if not match: return
            meta_json = match.group(1)
            meta_data = json.loads(meta_json)
            list_of_variants = meta_data.get('product', {}).get('variants', [])   
            for variant in list_of_variants:
                variant_id = variant.get('id')
                url = f"{response.url}?variant={variant_id}"
                yield scrapy.Request(url, callback=self.parse_details)
        except:
            print("Exception in parse_variants!!")    
    
    def parse_details(self, response):
        try:
            selected_variant = response.xpath("//script[@type='application/json' and @data-selected-variant]/text()").get()
            single_variant = response.xpath("(//script[@type='application/ld+json']/text())[2]").get()
            
            variant_data = json.loads(selected_variant) if selected_variant else json.loads(single_variant)

            item = BeautyOutletItem()
            item['Url'] = response.url
            item['Title'] = response.xpath("//div[@class='product__title']/h1/text()").get()
            item['Barcode'] = str(variant_data.get('barcode', '')) if selected_variant else str(variant_data.get('gtin', ''))
            item['BarcodeType'] = barcode_type(item['Barcode'])
            item['Availability'] = variant_data.get('available', False) if selected_variant else "InStock" in variant_data['offers']['availability']
            item['Price'] = response.xpath("//meta[@property='og:price:amount']/@content").get()
            item['hasVariations'] = bool(selected_variant)
            item['isPriceExcVAT'] = "Taxes included" not in response.xpath("//div[contains(@class,'product__tax')]/text()").get()
            item['Description'] = clean_text(response.xpath('(//div[contains(@class, "product__description")]//text())').getall())
            item['Brand'] = response.xpath("//p[contains(@class,'product__text')]/strong/text()").get()
            item['mpn'] = ""
            item['sku'] = variant_data.get('sku','')
            item['Size'] = ""
            item['Color'] = response.xpath("//*[@checked and contains(@name,'Colo')]/@value").get(default="")
            item['Offer'] = ""
            item['Image'] = "https:" + response.xpath("(//div[contains(@class,'product__media')]/img/@src)[1]").get()
            item['Images'] = ["https:" + img for img in response.xpath("(//div[contains(@class,'product__media')]/img/@src)[1]").extract()]
            if item['sku'] and item['sku'] not in self.seen_skus:
                self.seen_skus.add(item['sku'])
                yield item
       
        except:
            print("Exception in parse_details!!")    

    
