import scrapy
from web_scraping.spiders.utils import sanitize_json,safe_load_json
from web_scraping.items import EvanscyclesCrawlerItem

class Evanscycles_Crawler(scrapy.Spider):
    name = "evanscycles_crawler"
    start_urls = ["https://www.evanscycles.com/"]

    def parse(self, response):
        major_categories = response.xpath("(//a[contains(@id,'lnkTopLevelMenu')]/@href)[position()<last()]").extract()
        yield from response.follow_all(major_categories or '', callback=self.parse_sub_categories)

    def parse_sub_categories(self, response):
        accessories = response.xpath("//h1[text()='ACCESSORIES']//following::a[text()='Shop All']/@href").get()
        yield response.follow(accessories or '', callback=self.parse_pagination)
        sub_categories = list(set(response.xpath("//div[@class='featCatInner']/a/@href").extract()))
        yield from response.follow_all(sub_categories or '', callback=self.parse_pagination)

    def parse_pagination(self, response):
        yield from self.parse_product(response)
        next_page = response.xpath("//a[@class='swipeNextClick NextLink ' and @rel='next']/@href").get()
        yield response.follow(next_page or '', callback=self.parse_pagination)

    def parse_product(self, response):
        products = response.xpath("//div[@class='s-producttext-top-wrapper']/a/@href").extract()
        yield from response.follow_all(products or '', callback=self.parse_details)

    def parse_details(self, response):
        script_tag = sanitize_json(response.xpath("//script[@id='structuredDataLdJson']/text()").get())
        script_tag2 = sanitize_json(response.xpath("//span[@class='ProductDetailsVariants hidden']/@data-variants").get())

        variants = safe_load_json(script_tag) or []
        variants2 = safe_load_json(script_tag2) or []

        item = EvanscyclesCrawlerItem()
        for variant2 in variants2:
            for size in variant2.get('SizeVariants', []):
                item['sku'] = size.get('SizeVarId', '')
                item['Size'] = size.get('SizeName', '')
                item['Color'] = variant2.get('ColourName', '')
                item['Image'] = variant2.get('MainImageDetails', {}).get('ImgUrlXXLarge', '')
                item['Images'] = [img.get('ImgUrlXXLarge', '') for img in variant2.get('ProdImages', {}).get('AlternateImages', [])]

        for variant in variants:
            for offer in variant.get('offers', []):
                sku2 = offer.get('sku', '')
                item['Url'] = f"{response.url}?ah={sku2}"
                item['Brand'] = variant.get('brand', '')
                item['Price'] = float(offer.get('price', ''))
                item['Availability'] = "InStock" in offer.get('availability', '')
                item['Barcode'] = str(variant.get('gtin13', ''))
                item['Description'] = str(variant.get('description', ''))
                item['Title'] = variant.get('name', '')
                item['hasVariations'] = len(variant.get('offers', [])) > 1
                item['isPriceExcVAT'] = ""
                item['mpn'] = ""
                item['Offer'] = ""
        yield item


