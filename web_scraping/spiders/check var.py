import scrapy
from web_scraping.spiders.utils import sanitize_json,safe_load_json,barcode_type,clean_text
from web_scraping.items import EvanscyclesCrawlerItem

class Evanscycles_Crawler(scrapy.Spider):
    name = "check"
    start_urls = ["https://www.evanscycles.com/brand/specialized/tarmac-sl7-comp---105-di2-road-bike-931110#colcode=93111002"]
    seen_skus = set()
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
        selected_data = sanitize_json(response.xpath("//script[@id='structuredDataLdJson']/text()").get())
        selected_variant = sanitize_json(response.xpath("//span[@class='ProductDetailsVariants hidden']/@data-variants").get())
        try:
            data_list = safe_load_json(selected_data) or []
            variant_list = safe_load_json(selected_variant) or []

            variant_dict = {}
            for variant in variant_list:
                for size in variant.get('SizeVariants', []):
                    sku_variant = size.get('SizeVarId', '')
                    variant_dict[sku_variant] = {
                        'Size': size.get('SizeName', ''),
                        'Color': variant.get('ColourName', ''),
                        'Color_id':variant.get('ColVarId', ''),
                        'Image': variant.get('MainImageDetails', {}).get('ImgUrlXXLarge', ''),
                        'Images': [img.get('ImgUrlXXLarge', '') for img in variant.get('ProdImages', {}).get('AlternateImages', [])]
                    }
    
            for data in data_list:
                for offer in data.get('offers', []):
                    sku = offer.get('sku', '')
                    item = EvanscyclesCrawlerItem()
                    item['sku'] = sku
                    item['Brand'] = clean_text(data.get('brand', ''))
                    item['Price'] = float(offer.get('price', ''))
                    item['Availability'] = "InStock" in offer.get('availability', '')
                    item['Barcode'] = str(data.get('gtin13', '')) if data.get('gtin13','').isdigit() else ''
                    item['BarcodeType'] = barcode_type(item['Barcode'])
                    item['Description'] = clean_text(str(data.get('description', '')))
                    item['Title'] = clean_text(data.get('name', ''))
                    item['hasVariations'] = bool(len(data.get('offers', [])) > 1)
                    item['isPriceExcVAT'] = False
                    item['mpn'] = ""
                    item['Offer'] = ""
                    variant = variant_dict.get(sku)
                    item['Size'] = variant['Size']
                    item['Color'] = variant['Color']
                    item['Image'] = variant['Image']
                    item['Images'] = variant['Images']
                    if item['hasVariations'] == True:
                        item['Url'] = f"{response.url}#colcode={ variant['Color_id']}?ah={sku}"
                    else:
                        item['Url'] = f"{response.url}#colcode={ variant['Color_id']}"   

                    if item['sku'] and item['sku'] not in self.seen_skus:
                        self.seen_skus.add(item['sku'])
                        yield item

        except:
            print("Exception in parse details!!")
