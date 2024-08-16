import scrapy
import json
from web_scraping.spiders.utils import sanitize_json, safe_load_json, barcode_type, clean_text

class NikeSpider(scrapy.Spider):
    name = "check"
    start_urls = ["https://www.nike.com"]
    seen_skus = set()
    color_id_instock = set()
    color_id_outOfStock = set()
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
    def parse(self,response):
        categories= response.xpath("//p[contains(text(),'All Shoes') or contains(text(),'All Clothing') or contains(text(),'All Accessories')]/parent::a/@href").extract()
        yield from response.follow_all(categories, callback=self.parse_categories)

    def parse_categories(self, response):
        page_count = 0
        url = self.build_url(page_count)
        yield scrapy.Request(url, callback=self.pagination, meta={"page_count": page_count})

    def build_url(self, page_count):
        return f"https://api.nike.com/cic/browse/v2?queryid=products&anonymousId=B5E086C91EFFE15A9B1F4CC636F67E85&country=us&endpoint=%2Fproduct_feed%2Frollup_threads%2Fv2%3Ffilter%3Dmarketplace(US)%26filter%3Dlanguage(en)%26filter%3DemployeePrice(true)%26filter%3DattributeIds(7baf216c-acc6-4452-9e07-39c2ca77ba32%2Ca00f0bb2-648b-4853-9559-4cd943b7d6c6)%26anchor%3D{page_count}%26consumerChannelId%3Dd9a5bc42-4b9c-4976-858a-f159cf99c647%26count%3D24&language=en&localizedRangeStr=%7BlowestPrice%7D%20%E2%80%94%20%7BhighestPrice%7D"

    def pagination(self, response):
        yield from self.fetch_products(response)
        data = json.loads(response.body)
        total_pages = data["data"]["products"]["pages"]["totalPages"]
        current_page = response.meta.get('page_count', 0) // 24
        if current_page < total_pages - 1:
            next_page = (current_page + 1) * 24
            url = self.build_url(next_page)
            yield scrapy.Request(url, callback=self.pagination, meta={"page_count": next_page})

    def fetch_products(self, response):
        data = response.json()
        products = data["data"]["products"]["products"]
        country_lang = "us/en"
        for product in products:
            for colorway in product["colorways"]:
                pdp_url = colorway["pdpUrl"].replace("{countryLang}", country_lang)
                full_url = f"https://www.nike.com/{pdp_url}"
                if full_url not in self.seen_skus:
                    self.seen_skus.add(full_url)
                    self.color_id_instock.add(full_url.split('/')[-1])
                    yield scrapy.Request(full_url, callback=self.fetch_variants)


    def fetch_variants(self, response):
        yield from self.all_urls(response)
        script_tag = response.xpath("//script[@type='application/json']/text()").get()
        if script_tag:
            data = json.loads(script_tag)
            colors = data["props"]["pageProps"]["colorwayImages"]
            for color in colors:
                color_id = color['styleColor']
                if color_id not in self.color_id_instock:
                    self.color_id_outOfStock.add(color_id)
                    url_id = response.url.split('/')[-1]
                    url = response.url.replace(url_id, str(color_id))
                    if url not in self.seen_skus:
                        self.seen_skus.add(url)
                        yield scrapy.Request(url, callback=self.all_urls)
   
    def all_urls(self, response):
        url = response.url
        script_tag = sanitize_json(response.xpath("//script[@type='application/ld+json']/text()").get())
        script_tag2 = sanitize_json(response.xpath("//script[@type='application/json']/text()").get())

        data = safe_load_json(script_tag) or {}
        data2 = safe_load_json(script_tag2) or {}

        brand_name = data.get("brand", {}).get("name", "")
        offers = data.get("offers", {}).get("offers", [])

        colorway_images = data2.get('props', {}).get('pageProps', {}).get('colorwayImages', [])
        style_colors = {item.get('styleColor', ''): item.get('colorDescription', '') for item in colorway_images}
        style_images = {item.get('styleColor', ''): item.get('squarishImg', '') for item in colorway_images}
        alt_texts = {item.get('styleColor', ''): item.get('altText', '') for item in colorway_images}

        sizes = {}
        sku_ids = {}
        gtins = {}

        product_id = data2.get('props', {}).get('pageProps', {}).get('selectedProduct', {}).get('merchProductId', '')
        for group in data2.get('props', {}).get('pageProps', {}).get('productGroups', []):
            for product_key, product_value in group.get('products', {}).items():
                style_color = product_value.get('styleColor', '')
                if style_color not in sizes:
                    sizes[style_color] = []
                    sku_ids[style_color] = []
                    gtins[style_color] = []
                sizes[style_color].extend([size.get('label', '') for size in product_value.get('sizes', [])])
                sku_ids[style_color].extend([size.get('merchSkuId', '') for size in product_value.get('sizes', [])])
                gtins[style_color].extend([gtin.get('gtin', '') for size in product_value.get('sizes', []) for gtin in size.get('gtins', [])])

        for style_color, color_description in style_colors.items():
            variant_data = {
                "url": response.url,
                "style_color": style_color,
                "sizes": sizes.get(style_color, []),
                "sku_ids": sku_ids.get(style_color, []),
                "gtins": gtins.get(style_color, []),
                "title": f"{alt_texts.get(style_color, '')} - {color_description}",
                "brand": brand_name,
                "color": response.xpath("//li[@data-testid='product-description-color-description']/text()[last()]").get(),
                "price": response.xpath("(//span[@data-testid='currentPrice-container']/text())[1]").get(),
                "offers": response.xpath("(//span[@data-testid='OfferPercentage']/text())[1]").get(),
                "image": response.xpath("//div[contains(@data-testid,'ThumbnailListContainer')]//label/img/@src").get(),
                "description": response.xpath("//p[contains(@data-testid,'product-description')]/text()").extract(),
                "images": response.xpath("//div[contains(@data-testid,'ThumbnailListContainer')]//label/img/@src").extract()
            }

            sku_api = f"https://api.nike.com/cic/grand/v1/graphql/getfulfillmentofferings/v5?variables=%7B%22countryCode%22%3A%22US%22%2C%22currency%22%3A%22USD%22%2C%22locale%22%3A%22en-US%22%2C%22locationId%22%3A%22%22%2C%22locationType%22%3A%22STORE_VIEWS%22%2C%22offeringTypes%22%3A%5B%22SHIP%22%5D%2C%22postalCode%22%3A%22%22%2C%22productId%22%3A%22{product_id}%22%7D"
            yield scrapy.Request(sku_api, callback=self.fetch_details, meta={"variant_data": variant_data, "url": url, "sizes": sizes, "sku_ids": sku_ids, "gtins": gtins})
    
    def fetch_details(self, response):
        variant_data = response.meta.get('variant_data', {})
        sizes = response.meta.get('sizes', {})
        sku_ids = response.meta.get('sku_ids', {})
        gtins = response.meta.get('gtins', {})

        data = safe_load_json(response.body) or {}  
        color_id = variant_data.get('style_color', '')

        if data is None or not data.get('data', {}).get('fulfillmentOfferings', {}):
            in_stock_sku_ids = ()
            out_of_stock_sku_ids =variant_data.get('sku_ids', '')
            all_sku_ids = out_of_stock_sku_ids
        else:
            fulfillment = data.get('data', {}).get('fulfillmentOfferings', {})
            in_stock_sku_ids = {item.get('skuId', '') for item in fulfillment.get('items', [])}
            warnings = fulfillment.get('warnings', [])
            if warnings is None:
                warnings = []
                all_sku_ids = in_stock_sku_ids
            else: 
                out_of_stock_sku_ids = {warning.get('skuId', '') for warning in fulfillment.get('warnings', [])}
                all_sku_ids = in_stock_sku_ids.union(out_of_stock_sku_ids)

        for sku in all_sku_ids:
            size_for_sku = next(
                (size for color, sizes_list in sizes.items()
                for size, skus in zip(sizes_list, sku_ids.get(color, []))
                if sku in skus), ''
            )

            availability = sku in in_stock_sku_ids
            url = response.meta.get('url', '')
            has_variations = len(all_sku_ids) > 1
            if has_variations:
                url = f"{response.meta.get('url', '')}?ah={sku}"

            if sku not in self.seen_skus:
                self.seen_skus.add(sku)
                yield {
                    "url": url,
                    "Title": clean_text(f"{variant_data.get('title', '')} - {size_for_sku}"),
                    "Barcode": next((gtin for color, gtins_list in gtins.items()
                                    for gtin, skus in zip(gtins_list, sku_ids.get(color, []))
                                    if sku in skus), ''),
                    "Barcode_type": barcode_type(next((gtin for color, gtins_list in gtins.items()
                                                    for gtin, skus in zip(gtins_list, sku_ids.get(color, []))
                                                    if sku in skus), '')) if sku else '',
                    "Availability": availability,
                    "Price": float(clean_text(variant_data.get('price', '0'))),
                    "hasVariations": has_variations,
                    "isPriceExcVAT": False,
                    "Description": clean_text(str(variant_data.get('description', ''))),
                    "Brand": clean_text(str(variant_data.get('brand', ''))),
                    "Mpn": "",
                    "Sku": sku,
                    "Size": size_for_sku,
                    "Color": clean_text(str(variant_data.get('color', ''))),
                    "Offer": clean_text(str(variant_data.get('offers', ''))),
                    "Image": variant_data.get('image', ''),
                    "Images": variant_data.get('images', [])
                }