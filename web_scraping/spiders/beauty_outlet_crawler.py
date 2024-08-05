import scrapy
import json
import re
from web_scraping.items import BeautyOutletItem

class BeautyOutletSpider(scrapy.Spider):
    name = "beauty_outlet_crawler"
    start_urls = ["https://www.beautyoutlet.co.uk"]
    
    def parse(self, response):
        major_categories = response.xpath("(//a[contains(@id,'shop-all')])[position()<8]/@href").extract()
        yield from response.follow_all(major_categories, callback=self.parse_sub_categories) 

    def parse_sub_categories(self, response):
        sub_categories = list(set(response.xpath('//span[@class="icon-wrap"]/preceding::h3/a/@href').extract()))
        yield from self.parse_pagination(response)
        yield from response.follow_all(sub_categories or '', callback=self.parse_sub_categories) 

    def parse_pagination(self, response):
        yield from self.parse_product(response)
        next_page = response.xpath('//a[@aria-label="Next page"]/@href').get()
        yield response.follow(next_page or '', callback=self.parse_pagination) 

    def parse_product(self, response):
        products = response.xpath('//h3[@class="card__heading h5"]/a/@href').extract()
        yield from response.follow_all(products, callback=self.parse_variants)

    def parse_variants(self, response):
        script_tag = response.xpath("//script[contains(text(), 'var meta = ')]/text()").get()
        if script_tag:
            pattern = re.compile(r'var meta = ({.*?});', re.DOTALL)
            match = pattern.search(script_tag)
            if match:
                meta_json = match.group(1)
                meta_data = json.loads(meta_json)
                
                for variant in meta_data.get('product', {}).get('variants', []):
                    variant_id = variant.get('id')
                    url = f"{response.url}?variant={variant_id}"
                    
                    base_data = {
                        "url": url,
                        #"description": self.clean_text(response.xpath('(//div[contains(@class, "product__description")]//text())[2]').getall()),
                        "description": self.clean_text(response.xpath('(//div[contains(@class, "product__description")]//text())').getall()),
                        "brand": response.xpath("//p[contains(@class,'product__text')]/strong/text()").get(),
                        "hasVariations": bool(response.xpath('(//label[starts-with(@for,"template")]/text())[3]').get()),
                        "isPriceExcVAT": "Taxes included" not in response.xpath("//div[contains(@class,'product__tax')]/text()").get(),
                        "images": ["https:" + img for img in response.xpath("//div[contains(@class,'product__media')]/img/@src").extract()],
                        "Title": variant.get('name', ''),
                        #"Price": float(variant.get('price', 0)),
                        "Mpn": int(variant.get('id', '')),
                        "Sku": ', '.join([s.strip() for s in variant.get('sku', '').split(',') if s.strip()]),
                        "Color": variant.get('public_title', '')
                    }
                    
                    yield scrapy.Request(url, callback=self.product_information, meta={'base_data': base_data})
    
    def product_information(self, response):
        selected_variant = response.xpath("//script[@type='application/json' and @data-selected-variant]/text()").get()
        single_variant = response.xpath("(//script[@type='application/ld+json']/text())[2]").get()
        
        variant_data = json.loads(selected_variant) if selected_variant else json.loads(single_variant)

        item = BeautyOutletItem()
        item['Url']= response.meta['base_data']['url']
        item['Title']= response.meta['base_data']['Title']
        item['Barcode']= variant_data.get('barcode', '')
        item['Availability']= variant_data.get('available', False) if selected_variant else "InStock" in variant_data['offers']['availability']
        #item['Price']= response.meta['base_data']['Price']
        item['Price']= float(variant_data['offers']['price'])
        item['hasVariations']= response.meta['base_data']['hasVariations']
        item['isPriceExcVAT']= response.meta['base_data']['isPriceExcVAT']
        item['Description']= response.meta['base_data']['description']
        item['Brand']= response.meta['base_data']['brand']
        item['Mpn']= response.meta['base_data']['Mpn']
        item['Sku']= response.meta['base_data']['Sku']
        item['Size']= ""
        item['Color']= response.meta['base_data']['Color']
        item['Offer']= ""
        item['Image']= variant_data.get('featured_image', {}).get('src', '') if selected_variant else variant_data.get('image')
        item['Images']= response.meta['base_data']['images']

        yield item

    def clean_text(self, text):
        if isinstance(text, list):
            text = ' '.join(text)
        text = text.replace('&nbsp;"', '')
        text = text.strip('/"').strip()
        text = text.replace('\\"', '')
        return text
    

