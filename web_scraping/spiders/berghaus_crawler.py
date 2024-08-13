import scrapy
import json
from web_scraping.spiders.utils import barcode_type, clean_text

class BerghausSpider(scrapy.Spider):
    name = "berghaus_crawler"
    custom_settings = {
        'FEEDS': {
            'berghaus_crawler.json': {
                'format': 'json',
                'overwrite': True,
                'indent':4,
            },
        },
        'FEED_EXPORT_ENCODING': 'utf-8', 
    }
    start_urls = ["https://www.berghaus.com/women-s-bramblfell-interactive-gore-tex-waterproof-jacket-blue/14540875.html"]

    def parse(self, response):
        categories = list(set(response.xpath("//a[@data-context='Shop All' and (@data-override-value='Men-ShopAll' or @data-override-value='Women-ShopAll')]/@href").extract()))
        yield from response.follow_all(categories, callback=self.pagination)

    def pagination(self, response):
        yield from self.parse_product(response)
        next_page = response.xpath("//button[@data-direction='next']").get()
        if next_page:
            next_url = response.xpath("(//a[contains(@class,'PageSelectorActive')]/following::a[contains(@aria-label,'Go to page')]/@href)[1]").get()
            yield scrapy.Request(next_url, callback=self.pagination)

    def parse_product(self, response):
        products = list(set(response.xpath("//a[@class='athenaProductBlock_linkImage']/@href").extract()))
        yield from response.follow_all(products, callback=self.parse_variants)
    
    def parse_variants(self, response):
        script_tag = response.xpath("//script[@type='application/ld+json' and @id='productSchema']/text()").get()
        if not script_tag: return
        data = json.loads(script_tag)     
        for data in data['hasVariant']:
            url=data['offers']['url']
            variants = bool(len(data) > 1)
            yield scrapy.Request(url,callback=self.parse_details, meta={'variant': data,'hasVariations':variants})

    def parse_details(self,response):
        data = response.meta['variant']
        yield {
                "url": response.url,
                "Title": response.xpath("//h1[@class='productName_title']/text()").get(),
                "Barcode" : "",
                "Availability" :bool("InStock" in data['offers']['availability']),
                "Price" : float(data['offers']['price']),
                "hasVariations" :response.meta['hasVariations'],
                "isPriceExcVAT" :False,
                "Description" : self.clean_text(response.xpath("(//div[@id='product-description-content-2']//following::p/text())[1]").get()) ,
                "Brand" : str(response.xpath("//div[@class='productAddToWishlist']/@data-product-brand").get()),
                "Mpn" : str(data['mpn']),
                #"Sku" : response.xpath("//div[@class='externalSku']/@data-external-sku").get(),
                "Sku" : str(data['sku']),
                "Size" : clean_text(str(response.xpath("(//button[@data-selected]/text())[1]").get())),
                "Color": clean_text(str(response.xpath("(//span[contains(@class,'colorSwatch-selected')]/span/text())[1]").get(default=""))),
                "Offer": "SALE" if response.xpath("//span/@data-pap-banner-text[1]").get().strip() == "SALE" else "",
                "Image" : response.xpath("(//ul[@aria-label='Product Images']/li//img/@src)[1]").get(),
                "Images": response.xpath("//ul[@aria-label='Product Images']/li//img/@src").extract() 
                }
  
           