import os
import re
import json
from urllib.request import Request, urlopen
from lxml import etree
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import logging
from fake_useragent import UserAgent
from concurrent.futures import ThreadPoolExecutor
import random
import datetime
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import csv
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# 设置日志级别和格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 指定chromedriver的绝对路径
driver_path = r"D:\\chrome-win64\\chrome.exe"
# 设置Chrome驱动程序服务
service = Service(driver_path)
# 生成随机 User-Agent
user_agent = UserAgent().random
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')  # 忽略SSL证书错误
options.add_argument('--ignore-ssl-errors')  # 忽略证书错误
options.add_argument('--allow-insecure-localhost')  # 允许不安全的本地连接
options.add_argument("--disable-proxy-certificate-handler")
options.add_argument("--disable-content-security-policy")
options.add_argument('--headless')  # 使用无头浏览器模式
options.add_argument(f'user-agent={random.choice(user_agent)}')  # 随机用户代理

# 创建结果目录
base_dir = "D:\LAST\大数据实践课设\ProjectSummary\Spider\Data_Summary"
os.makedirs(base_dir, exist_ok=True)
logger.info(f"创建主结果目录: {base_dir}")

# 初始化driver并设置 ChromeOptions
driver = webdriver.Chrome(service=service, options=options)

# 创建一个统计信息文件 (保留CSV格式的统计文件)
stats_file = os.path.join(base_dir, "scraping_stats.csv")
with open(stats_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['时间', '页码', '爬取参赛者数', '成功爬取数', '失败爬取数', '备注'])
    logger.info(f"创建统计信息文件: {stats_file}")

starturl = "https://spdsapp.qhrb.com.cn/spds16/match/inner/steadyprofit1.action"
MAX_THREADS = 6
lock = threading.Lock()


# 获取页面资源
def getpage(url):
    logger.info(f"尝试获取页面: {url}")
    req = Request(url)
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0'
    req.add_header('User-Agent', user_agent)
    try:
        response = urlopen(req, timeout=60)
        logger.info(f"成功获取页面: {url}")
    except Exception as e:
        logger.error(f"获取页面失败: {url}, 错误: {str(e)}")
        return "error"  # 已经结束了，后面不会运行
    else:
        page = response.read()
        return page


# 保存数据到JSON文件
def save_to_json(data, filepath):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"成功保存JSON文件: {filepath}")
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败: {filepath}, 错误: {str(e)}")
        return False


def crawl_new_sessions(driver, base_dir, stats_file):
    """
    专门爬 14 届及以后新网站 (例如第16届)。
    """
    new_url = "https://spdspc.qhrb.com.cn/#/"
    logger.info(f"[NEW] 打开新网站首页: {new_url}")
    driver.get(new_url)
    time.sleep(2)
    logger.info(f"[NEW] 进入长期稳定盈利页面")
    next_button = driver.find_element(By.XPATH, "/html/body/div/div/div[4]/div[3]/div[18]")
    next_button.click()
    time.sleep(2)
    # 如果你还想预先翻 14 页之类，就可以在这里做
    # 例如你原来在 main() 里写的先翻14页
    for i in range(0):
        try:
            next_button = driver.find_element(By.XPATH, "/html/body/div/div/div[5]/div[3]/div[1]/a[2]")
            next_button.click()
            time.sleep(2)
            logger.info(f"[NEW] 预翻页 {i+1}/14")
        except Exception as e:
            logger.error(f"[NEW] 预翻页失败: {str(e)}")
            break

    # 然后爬 N 页
    pages_to_crawl = 300
    for i in range(pages_to_crawl):
        logger.info(f"[NEW] 正在爬新网站第 {i+1}/{pages_to_crawl} 页...")
        page_result = CrawIndexPage()
        if not page_result:
            logger.warning("[NEW] 本页爬取返回 False，可能出现异常，停止翻页")
            break

        # 下一页
        try:
            next_button = driver.find_element(By.XPATH, "/html/body/div/div/div[5]/div[3]/div[1]/a[2]")
            next_button.click()
            time.sleep(2)
        except Exception as e:
            logger.error(f"[NEW] 下一页失败: {str(e)}")
            break

    logger.info("[NEW] 新网站爬取完毕")

def click_and_parse_score(row_index, col_index, total_participants, newdir, participant_results):
    try:
        row_xpath = f"/html/body/div/div/div[5]/div[3]/table/tbody/tr[{row_index}]"
        row = driver.find_element(By.XPATH, row_xpath)
        tds = row.find_elements(By.TAG_NAME, "td")

        if len(tds) <= col_index:
            logger.warning(f"第{row_index}行 第{col_index}列 不存在")
            return False

        p_elements = tds[col_index].find_elements(By.TAG_NAME, "p")
        if not p_elements:
            logger.info(f"第{row_index}行 第{col_index}列 无 <p> 元素，跳过")
            return False

        score_text = p_elements[0].text.strip()
        if not score_text or not score_text.replace('.', '', 1).isdigit():
            logger.info(f"第{row_index}行 第{col_index}列 分数非法: '{score_text}'")
            return False

        score = float(score_text)
        if score == 0:
            logger.info(f"第{row_index}行 第{col_index}列 分数为 0，跳过")
            return False

        logger.info(f"第{row_index}行 第{col_index+1}届 点击得分: {score}")


        old_tabs = driver.window_handles

        # 点击之前确保点击目标
        driver.execute_script("arguments[0].scrollIntoView(true);", p_elements[0])
        p_elements[0].click()

        # 等待新标签页打开
        WebDriverWait(driver, 8).until(lambda d: len(d.window_handles) > len(old_tabs))

        # 切换到新窗口
        new_tabs = driver.window_handles
        new_tab = [tab for tab in new_tabs if tab not in old_tabs][0]
        driver.switch_to.window(new_tab)

        # 打印当前URL
        logger.info(f"已跳转至详情页: {driver.current_url}")

        if col_index + 1 <= 13:
            result = CrawlSecond(driver.current_url, newdir, f"第{col_index+1}届")
        else:
            result = CrawlSourcePage(driver.current_url, newdir, f"第{col_index + 1}届")
        # 关闭子页面并回到原窗口
        driver.close()
        driver.switch_to.window(old_tabs[0])

        if result:
            participant_results.append(f"成功: 第{col_index+1}届")
            logger.info(f"成功爬取: 第{col_index+1}届")
            return True
        else:
            participant_results.append(f"失败: 第{col_index+1}届")
            logger.warning(f"爬取失败: 第{col_index+1}届")
            return False

    except Exception as e:
        logger.error(f"第{row_index}行 第{col_index}列 处理异常: {type(e).__name__} - {str(e)}")
        participant_results.append(f"异常: 第{col_index+1}届 - {type(e).__name__}: {str(e)}")
        return False


def CrawIndexPage():
    try:
        # 获取页码
        try:
            element = driver.find_element(By.XPATH, "/html/body/div/div/div[5]/div[3]/div[1]/span[2]")
            text = element.text
            parts = text.split(" ")[-1]
            rank_value, total_pages = map(int, parts.split("/"))
            logger.info(f"正在爬取第{rank_value}页")
        except:
            rank_value = "未知页码"
            logger.warning("无法获取页码信息")

        # 获取所有参赛行
        rows = driver.find_elements(By.XPATH, "/html/body/div/div/div[5]/div[3]/table/tbody/tr")
        total_participants = len(rows)
        logger.info(f"一共找到参赛者 {total_participants} 名")

        success_count = 0
        fail_count = 0

        for row_index in range(1, total_participants + 1):
            try:
                row_xpath = f"/html/body/div/div/div[5]/div[3]/table/tbody/tr[{row_index}]"
                row = driver.find_element(By.XPATH, row_xpath)
                tds = row.find_elements(By.TAG_NAME, "td")

                name_element = tds[1].find_element(By.TAG_NAME, "a")
                name = name_element.text.strip()
                logger.info(f"开始处理参赛者: {name}")

                name = re.sub(r'[\\/:*?"<>| ]+', "", name)
                newdir = os.path.join(base_dir, name)
                os.makedirs(newdir, exist_ok=True)

                participant_results = []

                for col_index in range(5, 16):  # 第6列到第19列
                    success = click_and_parse_score(
                        row_index, col_index, total_participants, newdir, participant_results
                    )
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1

                # 保存每位选手结果
                save_to_json({
                    "结果列表": participant_results,
                    "统计": {
                        "成功数": sum(r.startswith("成功") for r in participant_results),
                        "失败数": sum(not r.startswith("成功") for r in participant_results)
                    }
                }, os.path.join(newdir, "爬取结果.json"))

            except Exception as e:
                logger.error(f"处理第{row_index}行时异常: {str(e)}")

        # 写入整体统计
        import csv
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(stats_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                current_time, rank_value, total_participants,
                success_count, fail_count,
                f"成功率: {success_count / (success_count + fail_count) * 100:.2f}%" if (success_count + fail_count) > 0 else "0%"
            ])

        logger.info(f"页面 {rank_value} 统计完成: 成功 {success_count}, 失败 {fail_count}")
        return True

    except Exception as e:
        logger.error(f"爬取首页时发生错误: {str(e)}")
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(stats_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([current_time, "未知页码", 0, 0, 0, f"爬取页面错误: {str(e)}"])
        return False



# 第一类子网页爬取
def CrawlSourcePage(url, filedir, filename):
    logger.info(f"开始爬取第一类子网页: {url}, 文件目录: {filedir}, 文件名: {filename}")
    try:
        # 设置日志级别
        logging.basicConfig(level=logging.ERROR)
        # 配置 Chrome 选项
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--ignore-certificate-errors')  # 忽略SSL证书错误
        chrome_options.add_argument('--allow-insecure-localhost')  # 允许不安全的本地连接
        chrome_options.add_argument('--no-sandbox')  # 解决DevToolsActivePort文件不存在的报错
        chrome_options.add_argument('--headless')  # 无头模式
        # 指定chromedriver的绝对路径
        driver_path = r"D:\\chromedriver-win64\\chromedriver.exe"
        # 设置Chrome驱动程序服务
        service = Service(driver_path)
        # 启动 Chrome 浏览器
        chrome = webdriver.Chrome(service=service, options=chrome_options)
        chrome.get(url)
        logger.info(f"成功加载页面: {url}")

        # 修改文件名格式：数字(届数)在前，字段名在后
        Data1 = os.path.join(filedir, f"{filename}_基本数据.json")
        Data2 = os.path.join(filedir, f"{filename}_多空交易数据.json")
        Data3 = os.path.join(filedir, f"{filename}_日夜交易数据.json")
        Data4 = os.path.join(filedir, f"{filename}_交易品种数据.json")

        # 获取并写入基本数据
        if not os.path.exists(Data1):
            logger.info(f"开始爬取基本数据: {url}")
            page = chrome.page_source
            tree = etree.HTML(page)
            Nodes = tree.xpath("/html/body/form/div/div/div/div/table/tbody/tr|/html/body/form/div[4]/table/tbody/tr")
            logger.info(f"第一类网页，一共找到 {len(Nodes)} 条基本数据")

            data_dict = {}

            for node in Nodes:
                sourcetext1 = node.xpath("./td[1]/text()")
                sourcetext2 = node.xpath("./td[2]/text()")
                sourcetext3 = node.xpath("./td[3]/text()")
                sourcetext4 = node.xpath("./td[4]/text()")

                # 判空和处理
                sourcetext1 = sourcetext1[0].strip() if sourcetext1 else "N/A"
                sourcetext2 = sourcetext2[0].strip() if sourcetext2 else "N/A"
                sourcetext3 = sourcetext3[0].strip() if sourcetext3 else "N/A"
                sourcetext4 = sourcetext4[0].strip() if sourcetext4 else "N/A"

                # 添加到字典
                if sourcetext1 != "N/A":
                    data_dict[sourcetext1] = sourcetext2
                if sourcetext3 != "N/A":
                    data_dict[sourcetext3] = sourcetext4

            # 保存为JSON
            save_to_json(data_dict, Data1)
        else:
            logger.info(f"基本数据文件已存在: {Data1}")

        # 获取并写入多空交易数据
        if not os.path.exists(Data2):
            logger.info(f"开始爬取多空交易数据: {url}")
            try:
                duo_kong_button = chrome.find_element(By.XPATH,
                                                      "/html/body/form/div[2]/a[6]|/html/body/form/div[1]/a[6]")
                duo_kong_button.click()
                logger.info("成功点击多空交易按钮")
                page = chrome.page_source
                tree = etree.HTML(page)
                Nodes = tree.xpath("/html/body/script[7]")
                logger.info(f"第一类网页，一共找到 {len(Nodes)} 条多空数据")

                for node in Nodes:
                    duo_kong_data = node.xpath("./text()")[0]
                    match = re.search(r"var\s+basicdata1Curves\s*=\s*'([^']+)';", duo_kong_data)
                    if match:
                        duo_kong_data = match.group(1)
                        # 尝试解析数据为JSON格式
                        try:
                            data_points = duo_kong_data.split(',')
                            data_dict = {}

                            for i in range(0, len(data_points), 2):
                                if i + 1 < len(data_points):
                                    data_dict[data_points[i]] = data_points[i + 1]

                            save_to_json(data_dict, Data2)
                        except Exception as e:
                            logger.error(f"解析多空交易数据失败: {str(e)}")
                            save_to_json({"raw_data": duo_kong_data}, Data2)
                    else:
                        logger.warning("未找到多空交易数据")
                        save_to_json({"error": "N/A"}, Data2)
            except NoSuchElementException:
                logger.warning("未找到多空交易按钮")
                save_to_json({"error": "无法获取多空交易数据"}, Data2)
        else:
            logger.info(f"多空交易数据文件已存在: {Data2}")

        # 获取并写入日夜交易数据
        if not os.path.exists(Data3):
            logger.info(f"开始爬取日夜交易数据: {url}")
            try:
                ri_ye_button = chrome.find_element(By.XPATH, "/html/body/form/div[2]/a[7]|/html/body/form/div[1]/a[7]")
                ri_ye_button.click()
                logger.info("成功点击日夜交易按钮")
                page = chrome.page_source
                tree = etree.HTML(page)
                Nodes = tree.xpath("/html/body/script[7]")
                logger.info(f"第一类网页，一共找到 {len(Nodes)} 条日夜数据")

                for node in Nodes:
                    ri_ye_data = node.xpath("./text()")[0]
                    match = re.search(r"var\s+basicdata1Curves\s*=\s*'([^']+)';", ri_ye_data)
                    if match:
                        ri_ye_data = match.group(1)
                        # 尝试解析数据为JSON格式
                        try:
                            data_points = ri_ye_data.split(',')
                            data_dict = {}

                            for i in range(0, len(data_points), 2):
                                if i + 1 < len(data_points):
                                    data_dict[data_points[i]] = data_points[i + 1]

                            save_to_json(data_dict, Data3)
                        except Exception as e:
                            logger.error(f"解析日夜交易数据失败: {str(e)}")
                            save_to_json({"raw_data": ri_ye_data}, Data3)
                    else:
                        logger.warning("未找到日夜交易数据")
                        save_to_json({"error": "N/A"}, Data3)
            except NoSuchElementException:
                logger.warning("未找到日夜交易按钮")
                save_to_json({"error": "无法获取日夜交易数据"}, Data3)
        else:
            logger.info(f"日夜交易数据文件已存在: {Data3}")

        # 获取并写入品种成交数据
        if not os.path.exists(Data4):
            logger.info(f"开始爬取品种成交数据: {url}")
            try:
                pin_zhong_button = chrome.find_element(By.XPATH,
                                                       "/html/body/form/div[2]/a[8]|/html/body/form/div[1]/a[8]")
                pin_zhong_button.click()
                logger.info("成功点击品种成交按钮")
                page = chrome.page_source
                tree = etree.HTML(page)
                Nodes = tree.xpath("/html/body/script[7]")
                logger.info(f"第一类网页，一共找到 {len(Nodes)} 条品种数据")

                for node in Nodes:
                    pin_zhong_button = node.xpath("./text()")[0]
                    match = re.search(r"var\s+basicdata1Curves\s*=\s*'([^']+)';", pin_zhong_button)
                    if match:
                        pin_zhong_data = match.group(1)
                        # 尝试解析数据为JSON格式
                        try:
                            data_points = pin_zhong_data.split(',')
                            data_dict = {}

                            for i in range(0, len(data_points), 2):
                                if i + 1 < len(data_points):
                                    data_dict[data_points[i]] = data_points[i + 1]

                            save_to_json(data_dict, Data4)
                        except Exception as e:
                            logger.error(f"解析品种成交数据失败: {str(e)}")
                            save_to_json({"raw_data": pin_zhong_data}, Data4)
                    else:
                        logger.warning("未找到品种成交数据")
                        save_to_json({"error": "N/A"}, Data4)
            except NoSuchElementException:
                logger.warning("未找到品种成交按钮")
                save_to_json({"error": "无法获取品种成交数据"}, Data4)
        else:
            logger.info(f"品种成交数据文件已存在: {Data4}")

        chrome.close()
        logger.info(f"成功完成第一类子网页爬取: {url}")
        return True
    except Exception as e:
        logger.error(f"爬取第一类子网页失败: {url}, 错误: {str(e)}")
        try:
            chrome.close()
        except:
            pass
        return False


# 第二类子网页爬取
def CrawlSecond(url, filedir, filename):
    logger.info(f"开始爬取第二类子网页: {url}, 文件目录: {filedir}, 文件名: {filename}")
    try:
        # 设置日志级别
        logging.basicConfig(level=logging.ERROR)
        # 配置 Chrome 选项
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--ignore-certificate-errors')  # 忽略SSL证书错误
        chrome_options.add_argument('--allow-insecure-localhost')  # 允许不安全的本地连接
        chrome_options.add_argument('--no-sandbox')  # 解决DevToolsActivePort文件不存在的报错
        chrome_options.add_argument('--headless')  # 无头模式
        # 指定chromedriver的绝对路径
        driver_path = r"D:\\chromedriver-win64\\chromedriver.exe"
        # 设置Chrome驱动程序服务
        service = Service(driver_path)
        # 启动 Chrome 浏览器
        chrome = webdriver.Chrome(service=service, options=chrome_options)
        chrome.get(url)
        logger.info(f"成功加载页面: {url}")

        # 通过xpath得到新的url
        page = chrome.page_source
        tree = etree.HTML(page)
        Nodes = tree.xpath("/html/body//div/div/div//ul/li")
        logger.info(f"找到 {len(Nodes)} 个子页面链接")

        urls = []
        for node in Nodes:
            urls.append(node.xpath("./a/@href")[0])

        BaseDataUrl = ""
        duo_kong_Url = ""
        ri_ye_Url = ""
        pin_zhong_Url = ""
        for Url in urls:
            if re.search(r'BasicData\.aspx\?id=\d+', Url):
                BaseDataUrl = str(Url)
            elif re.search(r'eom\.aspx\?id=\d+', Url):
                duo_kong_Url = str(Url)
            elif re.search(r'don\.aspx\?id=\d+', Url):
                ri_ye_Url = str(Url)
            elif re.search(r'BreedDeal\.aspx\?id=\d+', Url):
                pin_zhong_Url = str(Url)

        # 通过'/'符号切分URL(从右侧开始找到第一个'/'符号并切分)
        spliturl = url.rsplit('/', 1)[0]
        BaseDataUrl = spliturl + "/" + BaseDataUrl if BaseDataUrl else ""
        duo_kong_Url = spliturl + "/" + duo_kong_Url if duo_kong_Url else ""
        ri_ye_Url = spliturl + "/" + ri_ye_Url if ri_ye_Url else ""
        pin_zhong_Url = spliturl + "/" + pin_zhong_Url if pin_zhong_Url else ""

        logger.info(f"基本数据URL: {BaseDataUrl}")
        logger.info(f"多空交易URL: {duo_kong_Url}")
        logger.info(f"日夜交易URL: {ri_ye_Url}")
        logger.info(f"品种成交URL: {pin_zhong_Url}")

        # 修改文件名格式：数字(届数)在前，字段名在后
        Data1 = os.path.join(filedir, f"{filename}_基本数据.json")
        Data2 = os.path.join(filedir, f"{filename}_多空交易数据.json")
        Data3 = os.path.join(filedir, f"{filename}_日夜交易数据.json")
        Data4 = os.path.join(filedir, f"{filename}_交易品种数据.json")

        # 获取第二类页面基本数据
        if not os.path.exists(Data1) and BaseDataUrl:
            logger.info(f"开始爬取第二类页面基本数据: {BaseDataUrl}")
            chrome.get(BaseDataUrl)
            page = chrome.page_source
            tree = etree.HTML(page)
            Nodes = tree.xpath("/html/body/form/div/table/tbody/tr")
            logger.info(f"第二类网页，一共找到 {len(Nodes)} 条基本数据")

            data_dict = {}

            for node in Nodes:
                sourcetext1 = node.xpath("./td[1]/text()")
                sourcetext2 = node.xpath("./td[2]/text()")
                sourcetext3 = node.xpath("./td[3]/text()")
                sourcetext4 = node.xpath("./td[4]/text()")

                # 判空以及处理空格、换行符
                sourcetext1 = sourcetext1[0].strip() if sourcetext1 else "N/A"
                sourcetext2 = sourcetext2[0].strip() if sourcetext2 else "N/A"
                sourcetext3 = sourcetext3[0].strip() if sourcetext3 else "N/A"
                sourcetext4 = sourcetext4[0].strip() if sourcetext4 else "N/A"

                # 添加到字典
                if sourcetext1 != "N/A":
                    data_dict[sourcetext1] = sourcetext2
                if sourcetext3 != "N/A":
                    data_dict[sourcetext3] = sourcetext4

            # 保存为JSON
            save_to_json(data_dict, Data1)
        else:
            logger.info(f"基本数据文件已存在或URL为空: {Data1}")

        # 获取第二类页面多空交易数据
        if not os.path.exists(Data2) and duo_kong_Url:
            logger.info(f"开始爬取第二类页面多空交易数据: {duo_kong_Url}")
            chrome.get(duo_kong_Url)
            page = chrome.page_source
            tree = etree.HTML(page)
            Nodes = tree.xpath("/html/head/script[9]")
            logger.info(f"第二类网页，一共找到 {len(Nodes)} 条多空数据")

            for node in Nodes:
                duo_kong_data = node.xpath("./text()")[0]
                match = re.findall(r'\[\'(.*?)\',(\d+\.?\d*)\]', duo_kong_data)
                if match:
                    # 转换为JSON格式
                    data_dict = {}
                    for item in match:
                        data_dict[item[0]] = item[1]

                    save_to_json(data_dict, Data2)
                else:
                    logger.warning("未找到多空交易数据")
                    save_to_json({"error": "不存在多空交易数据"}, Data2)
        else:
            logger.info(f"多空交易数据文件已存在或URL为空: {Data2}")

        # 获取第二类页面日夜交易数据
        if not os.path.exists(Data3) and ri_ye_Url:
            logger.info(f"开始爬取第二类页面日夜交易数据: {ri_ye_Url}")
            chrome.get(ri_ye_Url)
            page = chrome.page_source
            tree = etree.HTML(page)
            Nodes = tree.xpath("/html/head/script[9]")
            logger.info(f"第二类网页，一共找到 {len(Nodes)} 条日夜数据")

            for node in Nodes:
                ri_ye_data = node.xpath("./text()")[0]
                match = re.findall(r'\[\'(.*?)\',(\d+\.?\d*)\]', ri_ye_data)
                if match:
                    # 转换为JSON格式
                    data_dict = {}
                    for item in match:
                        data_dict[item[0]] = item[1]

                    save_to_json(data_dict, Data3)
                else:
                    logger.warning("未找到日夜交易数据")
                    save_to_json({"error": "不存在日夜交易数据"}, Data3)
        else:
            logger.info(f"日夜交易数据文件已存在或URL为空: {Data3}")

        # 获取第二类页面品种成交数据
        if not os.path.exists(Data4) and pin_zhong_Url:
            logger.info(f"开始爬取第二类页面品种成交数据: {pin_zhong_Url}")
            chrome.get(pin_zhong_Url)
            page = chrome.page_source
            tree = etree.HTML(page)
            Nodes = tree.xpath("/html/head/script[9]")
            logger.info(f"第二类网页，一共找到 {len(Nodes)} 条品种数据")

            for node in Nodes:
                pin_zhong_data = node.xpath("./text()")[0]
                match = re.findall(r'\[\'(.*?)\',(\d+\.?\d*)\]', pin_zhong_data)
                if match:
                    # 转换为JSON格式
                    data_dict = {}
                    for item in match:
                        data_dict[item[0]] = item[1]

                    save_to_json(data_dict, Data4)
                else:
                    logger.warning("未找到品种成交数据")
                    save_to_json({"error": "不存在品种交易数据"}, Data4)
        else:
            logger.info(f"品种成交数据文件已存在或URL为空: {Data4}")

        chrome.close()
        logger.info(f"成功完成第二类子网页爬取: {url}")
        return True
    except Exception as e:
        logger.error(f"爬取第二类子网页失败: {url}, 错误: {str(e)}")
        try:
            chrome.close()
        except:
            pass
        return False




class myThread(threading.Thread):
    def __init__(self, url, newdir, name):
        threading.Thread.__init__(self)
        self.url = url
        self.newdir = newdir
        self.name = name

    def run(self):
        logger.info(f"线程开始: {self.name}, URL: {self.url}")
        result = CrawlSourcePage(self.url, self.newdir, self.name)
        logger.info(f"线程结束: {self.name}, 结果: {'成功' if result else '失败'}")

def main():
    start_time = datetime.datetime.now()
    logger.info(f"爬虫开始运行: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 创建一个总结果文件 (JSON格式)
    summary_file = os.path.join(base_dir, "爬取总结.json")

    # 初始化统计数据
    summary_data = {
        "开始时间": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "爬取统计": {
            "爬取页数": 0,
            "总参赛者数": 0,
            "成功爬取数": 0,
            "失败爬取数": 0,
            "成功率": "0%"
        }
    }

    try:

        crawl_new_sessions(driver, base_dir, stats_file)

        # ============= 这里统计一下总共爬了几页、成功/失败等等 =============
        # 你可以参考你原先的做法，去统计 stats_file (CSV) 里记录的总数。
        # 例如:
        total_pages = 0
        total_participants = 0
        total_success = 0
        total_fail = 0

        with open(stats_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            for row in rows[1:]:  # 跳过标题行
                # row: 时间, 页码, 爬取参赛者数, 成功爬取数, 失败爬取数, 备注
                if len(row) >= 5:
                    total_pages += 1  # 或者你可以用 row[1] 中的页码做计算
                    total_participants += int(row[2]) if row[2].isdigit() else 0
                    total_success     += int(row[3]) if row[3].isdigit() else 0
                    total_fail        += int(row[4]) if row[4].isdigit() else 0

        success_rate = (total_success / (total_success + total_fail)) * 100 if (total_success + total_fail) > 0 else 0

        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds() / 60.0
        summary_data["结束时间"] = end_time.strftime('%Y-%m-%d %H:%M:%S')
        summary_data["总耗时(分钟)"] = f"{duration:.2f}"
        summary_data["爬取统计"] = {
            "爬取页数": total_pages,
            "总参赛者数": total_participants,
            "成功爬取数": total_success,
            "失败爬取数": total_fail,
            "成功率": f"{success_rate:.2f}%"
        }

        # 保存总结文件
        save_to_json(summary_data, summary_file)
        logger.info("全部爬取完毕！")

    except Exception as e:
        logger.error(f"爬虫运行出错: {str(e)}")
        # 出错也写一下总结
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds() / 60.0
        summary_data["结束时间"] = end_time.strftime('%Y-%m-%d %H:%M:%S')
        summary_data["总耗时(分钟)"] = f"{duration:.2f}"
        summary_data["爬取统计"]["错误信息"] = str(e)
        save_to_json(summary_data, summary_file)
    finally:
        driver.close()
        logger.info("已关闭浏览器")



if __name__ == "__main__":
    main()