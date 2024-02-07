import scrapy
import random
import requests
from urllib.parse import urlencode
import json


class ProductScraperSpider(scrapy.Spider):
    name = "product_scraper"
    allowed_domains = ["ao.com", 'proxy.scrapeops.io']
    start_urls = ["https://ao.com"]

    def parse(self, response):
        subcategories = response.xpath('//ul[contains(@class, "main-navigation__fourth-level")]/li[contains(@class, "main-navigation__fourth-level-nav-item")]/a[starts-with( @ href, "https://ao.com/l/")]/@href')
        subcategories_links = [item.get() for item in subcategories]

        for sub_link in subcategories_links:
            yield response.follow(sub_link, callback=self.parse_sub_page)

    def parse_sub_page(self, response):
        script_tag = response.xpath('//script[@id="lister-data"]/text()').get()
        if script_tag:
            data = json.loads(script_tag)
            for product in data.get('Products', []):
                product_url = product.get('FullProductUrl')
                if product_url:
                    yield response.follow(product_url, callback=self.parse_product_page)

        next_page_url = response.xpath('//link[@rel="next"]/@href').get()
        if next_page_url:
            yield response.follow(next_page_url, callback=self.parse_sub_page)

    def parse_product_page(self, response):
        check_availability = response.css('div.flex span.inStockText::text').get()
        if check_availability:

            # the product pages have different structure for price
            price = response.css('span.now.mb-1.text-display.leading-none.text-primary.mt-0::text').get()
            price_member = response.css('span.text-title-lg.leading-snug.text-cta-mainhover::text').get()
            if not price:
                price = response.css('span[itemprop="price"]::text').get()
                price_member = None
                if price:
                    price = price.strip()
                else:
                    price = response.css('.sticky-summary-price-container .now::text').get()
                    price_member = response.css('.sticky-summary-price-container .flex > .text-body-sm::text').get()

            title = response.css('h3.title.text-display-sm.text-title-lg::text').get()
            if not title:
                title = response.css('h1[itemprop="name"]::text').get()

            try:
                color = response.url.split('-')[-3]
            except IndexError:
                color = None

            yield {'url': response.url,
                   'title': title,
                   'price': price,
                   'price_member': price_member,
                   'color': color
                   }

