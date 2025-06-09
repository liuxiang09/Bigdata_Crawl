import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import time
import random


class IndexSpider(scrapy.Spider):
    name = "index"
    allowed_domains = ["www.bilibili.com"]
    start_urls = ["https://www.bilibili.com"]
    max_refresh_times = 5

    # 添加自定义设置
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,  # 降低并发
        'DOWNLOAD_DELAY': 2,  # 基础下载延迟
        'RANDOMIZE_DOWNLOAD_DELAY': True,  # 随机化延迟
        # 'SELENIUM_DRIVER_ARGUMENTS': [
        #     '--headless',
        #     '--disable-gpu',
        #     '--no-sandbox',
        #     '--disable-dev-shm-usage',
        #     f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        # ],
    }
    custom_cookies = [
                {
                    "domain": ".bilibili.com",
                    "hostOnly": False,
                    "httpOnly": True,
                    "name": "SESSDATA",
                    "path": "/",
                    "secure": True,
                    "value": "5293d25b%2C1764909930%2C4cb2e%2A61CjBD5u0FJ2lUSrtF0MaAHxnMQI_wFm5FWnrb1Qb-Yz7HxGxNFre0vNUEdFmtrlG3F-ESVllVZEkxOVVSQUR5OWtkWkVfMEZjTV9wMWgyQUtNU1BOb2Z2T0o1NEZ5cTl2bUVnTnNTV0lSQ0daUGl4R2g1TV9maUVLOF9kS0loS1FKRHdZVE9mSDZ3IIEC",
                },
                {
                    "domain": ".bilibili.com",
                    "hostOnly": False,
                    "httpOnly": False,
                    "name": "bili_jct",
                    "path": "/",
                    "secure": False,
                    "value": "a4a51c870475d313181a3ba88a85bf98",
                },
    ]
    async def start(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse,
                wait_time=10,
                wait_until=EC.presence_of_element_located((By.CLASS_NAME, 'feed-card')),
                cookies = self.custom_cookies,
            )
            
    def parse(self, response):
        current_refresh = response.meta.get('refresh_count', 1)
        print(f"开始解析页面{current_refresh} ----->")
        
        bili_avatar = response.css('div.bili-avatar')
        if bili_avatar:
            print("登录成功！！")

        feed_cards = response.css('div.feed-card')
        if feed_cards:
            for feed_card in feed_cards:
                yield {
                    'title': feed_card.css('h3.bili-video-card__info--tit a::text').get(),
                    'link': feed_card.css('a.bili-video-card__image--link::attr(href)').get(),
                    'upname': feed_card.css('span.bili-video-card__info--author::text').get(),
                    'cover': 'https:' + (feed_card.css('picture[class="v-img bili-video-card__cover"] img::attr(src)').get() or ''),
                    'duration': feed_card.xpath('//*[@id="i_cecream"]/div[2]/main/div[2]/div/div[1]/div[2]/div/div/a/div/div[2]/div/span/text()').get(),
                    'views': feed_card.xpath('//*[@id="i_cecream"]/div[2]/main/div[2]/div/div[1]/div[2]/div/div/a/div/div[2]/div/div/span[1]/span/text()').get(),
                    'barrage': feed_card.xpath('//*[@id="i_cecream"]/div[2]/main/div[2]/div/div[1]/div[2]/div/div/a/div/div[2]/div/div/span[2]/span/text()').get(),
                }

        if current_refresh >= self.max_refresh_times:
            print(f"已达到最大刷新次数 {self.max_refresh_times}")
            return
        
        # 添加随机延迟
        delay = random.uniform(0.5, 1.5)  # 随机延迟
        print(f"等待 {delay:.2f} 秒后刷新...")
        time.sleep(delay)

        driver = response.request.meta['driver']
        # 模拟真实用户行为
        try:
            # 随机滚动页面
            scroll_height = random.randint(300, 700)
            driver.execute_script(f"window.scrollTo(0, {scroll_height});")
            time.sleep(random.uniform(0.3, 0.7))  # 短暂停顿
            old_content = driver.page_source
            fresh_button = driver.find_element(By.CSS_SELECTOR, 'div.feed-roll-btn')
            
            # 模拟真实点击
            driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });""", fresh_button)
            time.sleep(random.uniform(0.3, 0.7))  # 短暂停顿
            fresh_button.click()

            WebDriverWait(driver, 10).until(
                lambda d: d.page_source != old_content
            )
            
            # 点击后再次随机滚动
            scroll_height = random.randint(100, 500)
            driver.execute_script(f"window.scrollTo(0, {scroll_height});")
            
        except TimeoutException:
            print("等待页面更新超时")
            return
        except Exception as e:
            print(f"发生错误: {e}")
            return
        # 递归调用parse继续抓取
        new_response = response.replace(
            body=driver.page_source.encode('utf-8'),
        )
        new_response.meta['refresh_count'] = current_refresh + 1
        yield from self.parse(new_response)
