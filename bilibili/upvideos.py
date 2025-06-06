from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import time
import json
import os 
from fake_useragent import UserAgent
import random
from popular import JsonSaver
from urllib.parse import urljoin


# OUTPUT_DIR = "./bilibili/" # 假设这个变量已经存在
# COOKIES_DIR = "./bilibili/cookies.json" # 假设这个变量已经存在

# 全局常量 (可以根据您的实际项目结构进行调整)
BILIBILI_URL = "https://bilibili.com" # 主站URL，用于设置Cookies
COOKIES_FILE_PATH = os.path.join("./bilibili/", "cookies.json") # 您的Cookies文件路径
OUTPUT_DIR = "./bilibili/" # 输出目录
BASE_URL = "https://space.bilibili.com" # UP主空间的基准URL
UP_ID = "386869863" # UP主ID


class UpCrawler:
    
    def __init__(self, browser_name='chrome', driver_executable_path=None, cookies=None):
        
        self.ua = UserAgent(browsers=['chrome', 'firefox'], os=['windows', 'macos', 'linux']) # 限制浏览器和操作系统，倾向于桌面
        random_user_agent = self.ua.random 
        
        self.driver = None # 替换 self.browser 为 self.driver
        try:
            if browser_name == 'chrome':
                chrome_options = ChromeOptions()
                chrome_options.add_argument("--window-size=1920,1080") # 设置固定窗口大小
                chrome_options.add_argument(f"user-agent={random_user_agent}") # 设置随机 User-Agent
                # chrome_options.add_argument("--headless") # 如果需要无头模式
                # chrome_options.add_argument("--disable-gpu") # 无头模式下可能需要
                
                if driver_executable_path:
                    service = ChromeService(executable_path=driver_executable_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    self.driver = webdriver.Chrome(options=chrome_options)
            elif browser_name == 'firefox':
                firefox_options = FirefoxOptions()
                firefox_options.set_preference("general.useragent.override", random_user_agent)
                
                if driver_executable_path:
                    service = FirefoxService(executable_path=driver_executable_path)
                    self.driver = webdriver.Firefox(service=service, options=firefox_options)
                else:
                    self.driver = webdriver.Firefox(options=firefox_options)
            else:
                raise ValueError(f"不支持的浏览器类型: {browser_name}")

            print(f"成功启动 {browser_name} 浏览器，使用 User-Agent: {random_user_agent}")
        except Exception as e:
            print(f"启动 {browser_name} 浏览器失败: {e}")

        # --- 添加 Cookies ---
        if self.driver and cookies:
            print("正在添加 Cookies...")
            # 首先访问一下用于设置 Cookie 的基础域名，通常是主域名
            self.driver.get(BILIBILI_URL) # 访问主站URL
            time.sleep(2) # 等待页面加载，确保Cookie可以被设置

            for cookie in cookies:
                try:
                    # 格式化 Cookie 以符合 Selenium add_cookie 方法的要求
                    selenium_cookie = {
                        'name': cookie.get('name'),
                        'value': cookie.get('value'),
                        'domain': cookie.get('domain'),
                        'path': cookie.get('path', '/') # 默认路径为 '/'
                    }
                    
                    if 'secure' in cookie:
                        selenium_cookie['secure'] = cookie['secure']
                    if 'httpOnly' in cookie:
                        selenium_cookie['httpOnly'] = cookie['httpOnly']
                    if 'expirationDate' in cookie:
                        selenium_cookie['expiry'] = int(cookie['expirationDate']) # Selenium 期望 'expiry' (整数时间戳)
                    if 'sameSite' in cookie and cookie['sameSite'] in ['Lax', 'Strict', 'None']:
                        selenium_cookie['sameSite'] = cookie['sameSite']

                    if not selenium_cookie.get('name') or \
                       not selenium_cookie.get('value') or \
                       not selenium_cookie.get('domain'):
                        print(f"跳过 Cookie，因为缺少必要字段或值为 None/空: {cookie}")
                        continue
                    
                    print(f"尝试添加 Cookie: {selenium_cookie['name']}")
                    self.driver.add_cookie(selenium_cookie) # 使用 self.driver.add_cookie

                except Exception as cookie_e:
                    print(f"添加 Cookie 失败 ({cookie.get('name', '未知')}): {cookie_e}. 原始Cookie: {cookie}")
            print("Cookies 添加完成。")

            # 调试：打印所有当前浏览器会话中的 Cookies
            print("\n--- 浏览器会话中已设置的 Cookies ---")
            for c in self.driver.get_cookies(): # 使用 self.driver.get_cookies()
                print(f"  Name: {c.get('name')}, Value: {c.get('value')[:10]}..., Domain: {c.get('domain')}, Path: {c.get('path')}, Secure: {c.get('secure')}")
            print("------------------------------------\n")


    def fetch_page(self, url, wait_time=10): # 增加默认等待时间到10秒
        """
        使用 Selenium 访问 URL 并获取完整的页面 HTML 内容。
        wait_time: 等待页面加载的秒数。
        """
        if not self.driver:
            print("浏览器未成功启动，无法获取页面。")
            return None
        try:
            self.driver.get(url) # 使用 self.driver.get()
            self.driver.implicitly_wait(wait_time) # 隐式等待元素加载
            
            # --- 调试：将获取到的HTML内容保存到文件 ---
            # with open("bilibili_page_content_initial.html", "w", encoding="utf-8") as f:
            #     f.write(self.driver.page_source) # 使用 self.driver.page_source
            # print("页面HTML内容 (初始加载) 已保存到 bilibili_page_content_initial.html。")
            # -----------------------------------------------

            return self.driver.page_source # 返回页面的完整HTML
        
        except Exception as e:
            print(f"使用 Selenium 请求 {url} 失败: {e}")
            return None
        

    def _scroll_to_end(self, scroll_attempts=50, scroll_pause_time=1.5):
            """
            模拟滚动到页面底部，加载所有动态内容。
            scroll_attempts: 最大滚动尝试次数，防止无限循环。
            scroll_pause_time: 每次滚动后等待的时间，让新内容加载。
            """
            last_height = self.driver.execute_script("return document.body.scrollHeight") # 使用 self.driver
            no_change_count = 0

            for i in range(scroll_attempts):
                print(f"正在进行第 {i+1} 次滚动")
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # 使用 self.driver
                time.sleep(random.uniform(scroll_pause_time - 0.5, scroll_pause_time + 0.5)) # 增加随机性
                new_height = self.driver.execute_script("return document.body.scrollHeight") # 使用 self.driver
                if new_height == last_height:
                    no_change_count += 1
                    print(f"页面高度未变化，连续 {no_change_count} 次。")
                    if no_change_count >= 3: # 连续3次高度未变化，认为已到达底部
                        print("连续多次页面高度未变化，认为已加载所有内容，停止滚动。")
                        break
                else:
                    no_change_count = 0  # 高度变化，重置计数

                last_height = new_height
            print(f"滚动完成，开始提取视频信息。")


    def close_browser(self):
        """
        关闭 Selenium WebDriver 浏览器。
        """
        if self.driver:
            self.driver.quit() # 使用 self.driver.quit()
            print("浏览器已关闭。")


    def parse_video_info(self, html_content):
        if not html_content:
            return []
        soup = BeautifulSoup(html_content, "lxml")
        video_list = []

        # 方法一：直接根据类名查找（两个class都要匹配）
        up = soup.find("div", class_="nickname").get_text(strip=True)
        video_cards_by_class = soup.find_all("div", class_="upload-video-card grid-mode")
        for card in video_cards_by_class:
            try:
                link = card.find("a", class_="bili-cover-card").get('href')
                cover = card.find("img").get('src')
                title = card.find("div", class_="bili-video-card__title").find("a").get_text(strip=True)
                date = card.find("div", class_="bili-video-card__subtitle").find("span").get_text(strip=True)
                stats_items = card.find_all("div", class_="bili-cover-card__stat")
                views, barrage, duration = None, None, None
                for idx, item in enumerate(stats_items):
                    if idx == 0:
                        views = item.find("span").get_text(strip=True)
                    elif idx == 1:
                        barrage = item.find("span").get_text(strip=True)
                    elif idx == 2:
                        duration = item.find("span").get_text(strip=True)
            except Exception as e:
                print(f"解析视频信息时发生异常: {e}")
                link = cover = title = date = views = barrage = duration = None

            # 方法二：用xpath查找（需要lxml的etree支持）
            # from lxml import etree
            # html_tree = etree.HTML(html_content)
            # video_cards_by_xpath = html_tree.xpath("//div[contains(@class, 'upload-video-card') and contains(@class, 'grid-mode')]")
            # 拼接 https:// 前缀
            if link and not link.startswith("http"):
                link = urljoin("https:", link)
            if cover and not cover.startswith("http"):
                # os.path.join 更适合用于文件路径拼接，URL 拼接推荐使用 urllib.parse.urljoin
                cover = urljoin("https:", cover)
            # 组装成字典
            video_info = {
                "link": link,
                "cover": cover,
                "title": title,
                "date": date,
                "views": views,
                "barrage": barrage,
                "duration": duration,
                "up": up
            }
            video_list.append(video_info)
            
        if not video_list:
            print("解析完成后视频列表为空，请再次检查解析逻辑。")

        return video_list


def main():
    print("程序启动")
    
    my_bilibili_cookies = None
    # 尝试从 JSON 文件中加载 Cookies
    if os.path.exists(COOKIES_FILE_PATH):
        try:
            with open(COOKIES_FILE_PATH, "r", encoding="utf-8") as f:
                my_bilibili_cookies = json.load(f)
            print(f"成功从 {COOKIES_FILE_PATH} 加载 Cookies。")
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载 Cookies 文件失败: {e}")
            my_bilibili_cookies = None
    else:
        print(f"Cookies 文件不存在: {COOKIES_FILE_PATH}。将以游客身份继续。")

    # 根据需要指定 chromedriver.exe 的路径
    # driver_path = "D:/path/to/your/chromedriver.exe" 
    crawler = UpCrawler(browser_name='chrome', driver_executable_path=None, cookies=my_bilibili_cookies) 
    saver = JsonSaver(output_dir=OUTPUT_DIR) 

    if not crawler.driver: # 检查 self.driver 而不是 self.browser
        print("无法继续，浏览器启动失败。")
        return
    try:
        # 构建 UP 主所有视频页面的 URL
        target_url = f"{BASE_URL}/{UP_ID}/upload/video"  # UP主空间的所有视频页面

        print(f"正在使用 Selenium 爬取: {target_url}")
        html_content = crawler.fetch_page(target_url) # 获取初始页面HTML
        
        if html_content:
            for i in range(1, 100):
                print(f"正在爬取第 {i} 页......")
                crawler._scroll_to_end(scroll_attempts=50, scroll_pause_time=1.5) # 调用滚动方法
                
                # 滚动完成后，重新获取最新的HTML内容
                html_content_after_scroll = crawler.driver.page_source # 使用 self.driver.page_source
                
                # --- 调试：将滚动后的HTML内容保存到文件 ---
                # with open(os.path.join(OUTPUT_DIR, "bilibili_page_content_after_scroll.html"), "w", encoding="utf-8") as f:
                #     f.write(html_content_after_scroll)
                # print("页面HTML内容 (滚动后) 已保存到 bilibili_page_content_after_scroll.html，请检查该文件。")
                # -----------------------------------------------

                videos = crawler.parse_video_info(html_content_after_scroll)
                if videos:
                    print("已成功解析以下视频信息:")
                    for idx, video in enumerate(videos):
                        print(f"序号: {idx+1}, 标题: {video.get('title', '未知标题')}, 链接: {video.get('link', '未知链接')}, 播放量: {video.get('views', '未知播放量')}, UP主: {video.get('up', '未知UP主')}, 封面图片: {video.get('cover', '未知图片链接')}")
                    saver.save_to_json(data=videos, filename=f"{UP_ID}.json", append=False if i==1 else True) # 保存文件名更新为 up_all_videos.json
                else:
                    print("未解析到任何视频信息，请检查解析逻辑或页面结构是否正确。")

                # 查找“下一页”按钮，如果存在则点击，否则跳出循环
                try:
                    # 尝试查找“下一页”按钮
                    next_btn = crawler.driver.find_element(By.XPATH, "//*[@id='app']/main/div[1]/div[2]/div/div[3]/div/div[1]/button[11]")
                    # 检查按钮是否可点击（有些情况下按钮存在但已禁用）
                    if "disabled" in next_btn.get_attribute("class") or not next_btn.is_enabled():
                        print("未找到可用的下一页按钮，已到达最后一页。")
                        break
                    else:
                        print("找到下一页按钮，准备点击进入下一页。")
                        next_btn.click()
                        # 等待页面加载
                        time.sleep(random.uniform(2, 3))
                except NoSuchElementException:
                    print(f"未找到下一页按钮，结束循环。错误信息: {e}")
                    break
        else:
            print("未获取到任何页面html，请检查是否正确获取page_source。")
    except Exception as e:
        print(f"爬取过程中发生错误: {e}")
    finally:
        crawler.close_browser() # 确保浏览器最终被关闭


if __name__ == "__main__":
    main()
