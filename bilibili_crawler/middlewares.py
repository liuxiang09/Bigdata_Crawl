# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy_selenium.http import SeleniumRequest

class SeleniumMiddleware:
    """Scrapy middleware handling the requests using selenium"""

    def __init__(self, driver_name, command_executor, driver_arguments):
    # def __init__(self, driver_name, driver_executable_path,
    #     browser_executable_path, command_executor, driver_arguments):
        """Initialize the selenium webdriver

        Parameters
        ----------
        driver_name: str
            The selenium ``WebDriver`` to use
        driver_executable_path: str
            The path of the executable binary of the driver
        driver_arguments: list
            A list of arguments to initialize the driver
        browser_executable_path: str
            The path of the executable binary of the browser
        command_executor: str
            Selenium remote server endpoint
        """
        driver_name = driver_name.lower().capitalize()

        driver_options = getattr(webdriver, f"{driver_name}Options")()
        for argument in driver_arguments:
            driver_options.add_argument(argument)

        if command_executor:
            self.driver = webdriver.Remote(command_executor=command_executor,
                                           options=driver_options)
        else:
            driver_class = getattr(webdriver, driver_name)
            # 这一步会自动下载合适版本的chromedriver (要求selenium版本为4.6+)
            self.driver = driver_class(options=driver_options)

        # webdriver_base_path = f'selenium.webdriver.{driver_name}'

        # driver_klass_module = import_module(f'{webdriver_base_path}.webdriver')
        # driver_klass = getattr(driver_klass_module, 'WebDriver')

        # driver_options_module = import_module(f'{webdriver_base_path}.options')
        # driver_options_klass = getattr(driver_options_module, 'Options')

        # driver_options = driver_options_klass()

        # if browser_executable_path:
        #     driver_options.binary_location = browser_executable_path
        # for argument in driver_arguments:
        #     driver_options.add_argument(argument)

        # driver_kwargs = {
        #     'executable_path': driver_executable_path,
        #     f'{driver_name}_options': driver_options
        # }

        # # locally installed driver
        # if driver_executable_path is not None:
        #     driver_kwargs = {
        #         'executable_path': driver_executable_path,
        #         f'{driver_name}_options': driver_options
        #     }
        #     self.driver = driver_klass(**driver_kwargs)
        # # remote driver
        # elif command_executor is not None:
        #     from selenium import webdriver
        #     capabilities = driver_options.to_capabilities()
        #     self.driver = webdriver.Remote(command_executor=command_executor,
        #                                    desired_capabilities=capabilities)

    @classmethod
    def from_crawler(cls, crawler):
        """Initialize the middleware with the crawler settings"""

        driver_name = crawler.settings.get('SELENIUM_DRIVER_NAME')
        # driver_executable_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        # browser_executable_path = crawler.settings.get('SELENIUM_BROWSER_EXECUTABLE_PATH')
        command_executor = crawler.settings.get('SELENIUM_COMMAND_EXECUTOR')
        driver_arguments = crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS')

        if driver_name is None:
            raise NotConfigured('SELENIUM_DRIVER_NAME must be set')

        # if driver_executable_path is None and command_executor is None:
        #     raise NotConfigured('Either SELENIUM_DRIVER_EXECUTABLE_PATH '
        #                         'or SELENIUM_COMMAND_EXECUTOR must be set')

        middleware = cls(
            driver_name=driver_name,
            # driver_executable_path=driver_executable_path,
            # browser_executable_path=browser_executable_path,
            command_executor=command_executor,
            driver_arguments=driver_arguments
        )

        crawler.signals.connect(middleware.spider_closed, signals.spider_closed)

        return middleware

    def process_request(self, request, spider):
        """Process a request using the selenium driver if applicable"""

        if not isinstance(request, SeleniumRequest):
            return None

        self.driver.get(request.url)

        # for cookie_name, cookie_value in request.cookies.items():
        #     self.driver.add_cookie(
        #         {
        #             'name': cookie_name,
        #             'value': cookie_value
        #         }
        #     )
        # cookies为 list of dict
        for cookie in request.cookies:
            self.driver.add_cookie(cookie)

        # 验证登录状态
        self.driver.get(request.url)

        if request.wait_until:
            WebDriverWait(self.driver, request.wait_time).until(
                request.wait_until
            )

        if request.screenshot:
            request.meta['screenshot'] = self.driver.get_screenshot_as_png()

        if request.script:
            self.driver.execute_script(request.script)

        body = str.encode(self.driver.page_source)

        # Expose the driver via the "meta" attribute
        request.meta.update({'driver': self.driver})

        return HtmlResponse(
            self.driver.current_url,
            body=body,
            encoding='utf-8',
            request=request
        )

    def spider_closed(self):
        """Shutdown the driver when spider is closed"""

        self.driver.quit()


class BilibiliCrawlerSpiderMiddleware:
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

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class BilibiliCrawlerDownloaderMiddleware:
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

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
