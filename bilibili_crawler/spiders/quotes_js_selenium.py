import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class QuotesSpider(scrapy.Spider):
    name = 'quotes_js_seleinum'
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["http://quotes.toscrape.com/js/"]
    
    # 设置并发数
    custom_settings = {
        'CONCURRENT_REQUESTS': 4,  # 同时处理的请求数
        'SELENIUM_DRIVER_ARGUMENTS': ['--headless'],  # 无头模式运行
    }

    async def start(self):
        """
        起始请求，使用 SeleniumRequest
        """
        # 使用 SeleniumRequest 替代 scrapy.Request
        # wait_time: 等待页面加载的秒数
        # wait_until: 等待特定元素出现，这里是等待 class='quote' 的元素加载出来
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url, 
                callback=self.parse,
                wait_time=10,
                wait_until=EC.presence_of_element_located((By.CLASS_NAME, 'quote'))
            )

    def parse(self, response):
        """
        解析页面数据，并处理翻页
        """
        # 获取当前页码
        try:
            # 从URL中获取页码参数,如果没有则默认为第1页
            current_page = response.url.split('/')[-1] if 'page' in response.url else '1'
            self.logger.info(f"当前页码: {current_page}")
        except Exception as e:
            self.logger.error(f"获取页码出错: {e}")
            current_page = None

        # 解析数据
        quotes = response.css('div.quote')
        for quote in quotes:
            yield {
                'text': quote.css('span.text::text').get(),
                'author': quote.css('small.author::text').get(),
                'tags': quote.css('a.tag::text').getall(),
            }
            
        # --- 处理翻页 ---
        # SeleniumRequest 的 response 会在 meta 中包含 driver 对象
        driver = response.request.meta['driver']
        self.logger.info(f"查找下一页按钮")
        
        try:
            next_button_a = driver.find_element(By.CSS_SELECTOR, 'li.next a')
            # 获取当前页面的内容，用于后续比较
            old_content = driver.page_source
            
            # 点击下一页按钮
            next_button_a.click()
            self.logger.info(f"点击下一页按钮")
            
            # 等待新内容加载（等待页面内容发生变化）
            WebDriverWait(driver, 10).until(
                lambda d: d.page_source != old_content
            )
            
            # 创建一个新的 Response 对象，包含更新后的页面内容
            new_response = response.replace(
                body=driver.page_source.encode('utf-8')
            )
            
            # 使用新的 response 对象递归调用 parse
            yield from self.parse(new_response)
            
        except Exception as e:
            self.logger.info(f"已经是最后一页，找不到'Next'按钮或加载失败: {e}")
