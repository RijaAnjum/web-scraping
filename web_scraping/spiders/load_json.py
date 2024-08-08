import scrapy
import json
class check(scrapy.Spider):
    name = "check"
    start_urls = ["https://www.evanscycles.com/brand/hjc/atara-mt-gl-road-helmet-932079#colcode=93207916"]
    
    custom_settings = {
        'FEEDS': {
            'check.json': {
                'format': 'json',
                'overwrite': True,
                'indent': 4,
            },
        },
        'FEED_EXPORT_ENCODING': 'utf-8',
    }

    def parse(self, response):
        script_tag = response.xpath("//span[@class='ProductDetailsVariants hidden']/@data-variants").get()
        if script_tag:
            variants = json.loads(script_tag)
            yield  {"variants" :variants }

