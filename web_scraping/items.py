# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class BeautyOutletItem(scrapy.Item):
    Url = scrapy.Field()
    Brand = scrapy.Field()
    Price = scrapy.Field()
    sku = scrapy.Field()
    Availability = scrapy.Field()
    Barcode = scrapy.Field()
    BarcodeType=scrapy.Field()
    Description = scrapy.Field()
    Title = scrapy.Field()
    hasVariations = scrapy.Field()
    isPriceExcVAT = scrapy.Field()  
    mpn = scrapy.Field()
    Offer = scrapy.Field()
    Size = scrapy.Field()
    Color = scrapy.Field()
    Image = scrapy.Field()
    Images = scrapy.Field()



class EvanscyclesCrawlerItem(scrapy.Item):
    Url= scrapy.Field()
    Brand= scrapy.Field()
    Price= scrapy.Field()
    sku= scrapy.Field()
    Availability= scrapy.Field()
    Barcode= scrapy.Field()
    BarcodeType=scrapy.Field()
    Description= scrapy.Field()
    Title= scrapy.Field()
    hasVariations= scrapy.Field()
    isPriceExcVAT= scrapy.Field()
    mpn= scrapy.Field()
    Offer= scrapy.Field()
    Size= scrapy.Field()
    Color= scrapy.Field()
    Image = scrapy.Field()
    Images= scrapy.Field()


class SainsburysCrawlerItem(scrapy.Item):
    Url= scrapy.Field()
    Brand= scrapy.Field()
    Price= scrapy.Field()
    sku= scrapy.Field()
    Availability= scrapy.Field()
    Barcode= scrapy.Field()
    BarcodeType=scrapy.Field()
    Description= scrapy.Field()
    Title= scrapy.Field()
    hasVariations= scrapy.Field()
    isPriceExcVAT= scrapy.Field()
    mpn= scrapy.Field()
    Offer= scrapy.Field()
    Size= scrapy.Field()
    Color= scrapy.Field()
    Image = scrapy.Field()
    Images= scrapy.Field()    