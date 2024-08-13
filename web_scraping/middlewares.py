# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import requests
from random import randint
import os
from random import choice
from web_scraping.spiders.constants import UK_PROXIES 
from itemadapter import is_item, ItemAdapter
from scrapy.downloadermiddlewares.retry import RetryMiddleware


class WebScrapingSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class WebScrapingDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass



class CustomMiddleware:
    def process_request(self, request, spider):
        # Before Request
        #print("###  Request #\n\n\n")
        print(f"Processing request: {request.url}")
        return None  # Returning None means the request will be sent as usual

    def process_response(self, request, response, spider):
        # After Request
        #print("#### Response \n\n\n")
        print(f"Processing response: {response.url}")
        return response  # Returning the response means it will be processed by the spider
    

    def spider_opened(self, spider):
        print("Spider opened: %s" % spider.name)




class CustomRetryMiddleware(RetryMiddleware):
    def process_exception(self, request, exception, spider):
        print("RETRIESSSSSSSSSSSSS")
        return super().process_exception(request, exception, spider)




class RandomUserAgentMiddleware:
    USER_AGENTS_FILE = os.path.join(os.path.dirname(__file__), 'spiders', 'user_agents.txt')

    def get_user_agents(file_path):
        with open(file_path, 'r') as f:
            user_agents = [line.strip() for line in f.readlines() if line.strip()]
        return user_agents
    
    USER_AGENTS = get_user_agents(USER_AGENTS_FILE)

    def get_random_user_agent(self, USER_AGENTS):
        random_index=randint(0, len(USER_AGENTS)-1)
        return self.USER_AGENTS[random_index]

    def process_request(self, request,spider):
        random_user_agent=self.get_random_user_agent()  
        request.headers['User-Agent'] = random_user_agent

        print("************  new header attched ***************")
        print(request.headers['User-Agent'])



class MyProxyMiddleware:
   
    def __init__(self):
        self.proxies = UK_PROXIES

    def get_random_proxy(self):
        return choice(self.proxies)

    def process_request(self, request, spider):
        proxy = self.get_random_proxy()
        proxy_str = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
        request.meta['proxy'] = proxy_str

        #Additional headers
        request.headers['Accept-Language'] = 'en-US,en;q=0.9'
        request.headers['Accept-Encoding'] = 'gzip, deflate, br'
        # request.headers['Referer'] = 'http://example.com'
        # request.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        request.headers['Connection'] = 'keep-alive'
        # request.headers['Cache-Control'] = 'no-cache'
        # request.headers['Pragma'] = 'no-cache'
        # request.headers['DNT'] = '1'
        # request.headers['Upgrade-Insecure-Requests'] = '1'
        # request.headers['X-Requested-With'] = 'XMLHttpRequest'
        # request.headers['X-Forwarded-For'] = '123.123.123.123'
        
        # Print debug information
        print("************  new proxy attached ***************")
        print(request.meta['proxy'])
        print("************  headers attached ***************")
        print(request.headers)
       
