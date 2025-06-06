import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com"]

    def parse(self, response):
        # response.css() 使用CSS选择器来选取元素，返回一个选择器列表
        # .get() 获取第一个匹配元素的内容
        # .getall() 获取所有匹配元素的内容
        
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

        # --- 新增翻页功能 ---
        # 找到next按钮的链接
        next_page_url = response.css('li.next a::attr(href)').get()
        
        if next_page_url is not None:
            # response.urljoin() 会自动将相对URL (如 /page/2) 拼接成完整的URL
            full_next_page_url = response.urljoin(next_page_url)
            # yield 一个新的请求，并指定回调函数还是用 self.parse
            yield scrapy.Request(full_next_page_url, callback=self.parse)
        else:
            # 使用Scrapy的日志系统进行输出
            self.logger.info("已到达最后一页")
            
        # 更简洁的写法 (推荐)
        # Scrapy 提供了 response.follow() 专门处理这种情况
        # if next_page_url is not None:
        #     yield response.follow(next_page_url, callback=self.parse)

