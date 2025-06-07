import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class QuotesCrawlSpider(CrawlSpider):
    name = "quotes_crawl"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com"]
    
    # 定义爬取规则
    rules = (
        # 规则1: 提取并跟踪分页链接
        Rule(
            # LinkExtractor用于提取链接，restrict_css参数指定只从特定CSS选择器中提取链接
            LinkExtractor(restrict_css='li.next a'),
            # follow=True表示继续在提取到的页面上应用规则
            # callback='parse_item'表示对提取到的页面调用parse_item方法处理
            follow=True,
            callback='parse_item'
        ),
    )
    
    # 处理起始URL的方法，用于处理第一页数据
    def parse_start_url(self, response):
        # 直接调用parse_item方法处理第一页数据
        return self.parse_item(response)
    
    # CrawlSpider中不要重写parse方法，它被用于实现规则处理
    # 而是定义一个新的回调函数
    def parse_item(self, response):
        # 找到所有 class="quote" 的 div 标签
        all_quotes = response.css('div.quote')
        
        # 遍历每一个名言的 div
        for quote in all_quotes:
            # 在每个 div 中，继续使用CSS选择器找到内容和作者
            text = quote.css('span.text::text').get()
            author = quote.css('small.author::text').get()
            tags = quote.css('div.tags a.tag::text').getall()
            
            # yield 一个字典，Scrapy会自动收集这些数据
            yield {
                'text': text,
                'author': author,
                'tags': tags,
            }
            
        # 不需要手动处理翻页，因为Rule已经处理了
        self.logger.info(f"已处理页面: {response.url}") 