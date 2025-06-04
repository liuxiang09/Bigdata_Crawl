import urllib.parse
import requests # 暂时保留requests，以防后续需要处理API请求或其他静态页面
from bs4 import BeautifulSoup
from splinter import Browser
import urllib
import logging
import time
import json
import os 
from fake_useragent import UserAgent
import random


class BilibiliCrawler:
    BASE_URL = "https://www.bilibili.com"

    
    def __init__(self, browser_name='chrome', driver_executable_path=None):
        """
        初始化 BilibiliCrawler，并启动 Splinter 浏览器。
        可选参数 browser_name: 'chrome', 'firefox' 等。
        可选参数 driver_executable_path: 浏览器驱动的完整路径，如果不在 PATH 中。
        """
        self.ua = UserAgent()
        random_user_agent = self.ua.random # 生成随机UserAgent
        self.HEADERS = {
            "User-Agent": random_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive"
        }
        self.browser = None
        try:
            if driver_executable_path:
                self.browser = Browser(browser_name, executable_path=driver_executable_path)
            else:
                self.browser = Browser(browser_name)
            print(f"成功启动 {browser_name} 浏览器。")
        except Exception as e:
            print(f"启动 {browser_name} 浏览器失败: {e}")


    def fetch_page(self, url, wait_time=5):
        """
        使用 Splinter 访问 URL 并获取完整的页面 HTML 内容。
        wait_time: 等待页面加载的秒数。
        """
        if not self.browser:
            print("浏览器未成功启动，无法获取页面。")
            return None
        try:
            self.browser.visit(url)
            # self.browser.driver.implicitly_wait(wait_time) # 隐式等待元素加载
            is_present = self.browser.is_element_present_by_css(".video-card", wait_time=20)
            if not is_present:
                print(f"警告: 在 {wait_time} 秒内未找到 CSS 选择器")
            self._scroll_to_end()
            # --- 调试：将获取到的HTML内容保存到文件 ---
            # with open("bilibili_page_content.html", "w", encoding="utf-8") as f:
            #     f.write(self.browser.html)
            # print("页面HTML内容已保存到 bilibili_page_content.html，请检查该文件。")
            # -----------------------------------------------
            return self.browser.html
        
        except Exception as e:
            print(f"使用 Splinter 请求 {url} 失败: {e}")
            return None
        

    def _scroll_to_end(self, scroll_attempts=20):
        """
        模拟滚动到页面底部，加载所有动态内容。
        scroll_attempts: 最大滚动尝试次数，防止无限循环。
        scroll_pause_time: 每次滚动后等待的时间，让新内容加载。
        """
        last_height = self.browser.execute_script("return document.body.scrollHeight")
        no_change_count = 0

        for i in range(scroll_attempts):
            print(f"正在进行第 {i+1} 次滚动")
            # 滚动到页面底部
            self.browser.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2,3))
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                no_change_count += 1
                print(f"页面高度未变化，计数: {no_change_count}")
                if no_change_count >= 3: # 连续3次高度未变化，认为已到达底部
                    print("连续多次页面高度未变化，认为已加载所有内容，停止滚动。")
                    break
            else:
                no_change_count = 0  # 高度变化，重置计数

            last_height = new_height
        print(f"滚动完成，开始提取视频信息。")

    def close_browser(self):
        """
        关闭 Splinter 浏览器。
        """
        if self.browser:
            self.browser.quit()
            print("浏览器已关闭。")

    def parse_video_info(self, html_content):
        """
        解析页面内容，提取视频信息
        """
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "lxml")
        video_list = []

        video_items = soup.find_all("div", class_="video-card")

        if video_items:
            for item in video_items:
                try:
                    # 获取视频链接，封面链接，视频标题，视频作者，播放量，弹幕量
                    video_content = item.find("div", class_="video-card__content")
                    video_info = item.find("div", class_="video-card__info")
                    video = video_content.find("a").get('href')
                    cover = video_content.find("img").get('data-src')
                    title = video_info.find("p").get('title')
                    up_name = video_info.find("span", class_="up-name").span.text.strip()
                    views_and_barrage = video_info.find("p", class_="video-stat")
                    views = views_and_barrage.find("span", class_="play-text").text.strip()
                    barrage = views_and_barrage.find("span", class_="like-text").text.strip()
                    # 使用 https:// 拼接链接
                    if video:
                        video = urllib.parse.urljoin("https:", video)
                    if cover:
                        cover = urllib.parse.urljoin("https:", cover)
                    # 添加到列表中
                    video_list.append({
                        "video": video,
                        "cover": cover,
                        "title": title,
                        "up_name": up_name,
                        "views": views,
                        "barrage": barrage,
                    })
                except Exception as e:
                    print(f"解析单个视频信息时出错: {e}. 跳过此项。")
                    continue
        else:
            print("未找到视频列表项，video-items列表为空。")

        if not video_list:
            print("解析完成后视频列表为空，请检查解析逻辑。")

        return video_list

class JsonSaver:
    def __init__(self, output_dir="."):
        """
        初始化 JsonSaver。
        output_dir: 文件保存地址。
        """
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def save_to_json(self, data, filename='output.json'):
        """
        将字典或列表数据保存为 JSON 文件。
        data: 要保存的数据（通常是列表或字典）。
        filename: 保存的文件名。
        """
        file_path = os.path.join(self.output_dir, filename)
        try:
            with open(file_path, "w", encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                print(f"数据已成功保存到文件: {file_path}")
                return True
        except IOError as e:
            print(f"写入文件失败: {e}")
            return False
def main():
    # crawler = BilibiliCrawler(browser_name='chrome', driver_executable_path='D:/path/to/your/chromedriver.exe')
    crawler = BilibiliCrawler() # 默认使用chrome，并且假设chromedriver在PATH中
    saver = JsonSaver(output_dir='./bilibili/') # 保存类
    if not crawler.browser:
        print("无法继续，浏览器启动失败。")
        return
    try:
        target_url = f"{crawler.BASE_URL}/v/popular/all/"  # 热门视频页面
        print(f"正在使用 Splinter 爬取: {target_url}")
        html_content = crawler.fetch_page(target_url)
        if html_content:
            videos = crawler.parse_video_info(html_content)
            if videos:
                print("已成功解析以下视频信息:")
                for idx, video in enumerate(videos):
                    print(f"序号: {idx+1}, 标题: {video['title']}, 封面: {video['cover']}, 链接: {video['video']}, 播放量: {video['views']}, UP主: {video['up_name']}")
                saver.save_to_json(data=videos, filename="popular_videos.json")
            else:
                print("未解析到任何视频信息，请检查解析逻辑或页面结构是否正确。")
    except Exception as e:
        print(e)
    finally:
        crawler.close_browser() # 确保浏览器最终被关闭


if __name__ == "__main__":
    main()
