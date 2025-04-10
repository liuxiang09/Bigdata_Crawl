import os
import re
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
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# 设置日志级别
logging.basicConfig(level=logging.ERROR)
# 指定chromedriver的绝对路径
driver_path = r"D:\\chromedriver-win64\\chromedriver.exe"
# 设置Chrome驱动程序服务
service = Service(driver_path)
# 生成随机 User-Agent
user_agent = UserAgent().random
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')  # 忽略SSL证书错误
options.add_argument('--ignore-ssl-errors') # 忽略证书错误
options.add_argument('--allow-insecure-localhost')  # 允许不安全的本地连接
options.add_argument("--disable-proxy-certificate-handler")
options.add_argument("--disable-content-security-policy")
options.add_argument('--headless')  # 使用无头浏览器模式
options.add_argument(f'user-agent={random.choice(user_agent)}')  # 随机用户代理

# 初始化driver并设置 ChromeOptions
driver = webdriver.Chrome(service=service, options=options)


starturl = "https://spdsapp.qhrb.com.cn/spds16/match/inner/steadyprofit1.action"
MAX_THREADS = 10
lock = threading.Lock()

# 获取页面资源
def getpage(url):
    req = Request(url)
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 ' \
                 '(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    req.add_header('User-Agent', user_agent)
    try:
        response = urlopen(req, timeout=60)
    except:
        return "error"  # 已经结束了，后面不会运行
    else:
        page = response.read()
        return page


# 第一类子网页爬取
# 15 /html/body/form/div[2]/div[1]/div/div/table/tbody[2]/tr[1]/td[1]
# 16 /html/body/form/div[3]/div[1]/div/div/table/tbody[2]/tr[1]/td[1]
# 13 /html/body/form/div[4]/table/tbody/tr
def CrawlSourcePage(url, filedir, filename):
    #lock.acquire()
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

    Data1 = filedir + "/" + "基本数据" + "(" + filename + ")" + ".txt"
    Data2 = filedir + "/" + "多空交易数据" + "(" + filename + ")" + ".txt"
    Data3 = filedir + "/" + "日夜交易数据" + "(" + filename + ")" + ".txt"
    Data4 = filedir + "/" + "交易品种数据" + "(" + filename + ")" + ".txt"
    

    # 获取并写入基本数据
    if not os.path.exists(Data1):
        
        page = chrome.page_source
        # page = page.decode('utf-8', 'ignore')
        tree = etree.HTML(page)
        Nodes = tree.xpath("/html/body/form/div/div/div/div/table/tbody/tr|/html/body/form/div[4]/table/tbody/tr")
        print("第一类网页，一共有" , len(Nodes) , "条基本数据")
        # /html/body/form/div[3]/div[1]/div/div/table/tbody[2]/tr[1]/td[1]
        # /html/body/form/div[3]/div[1]/div/div/table/tbody[2]/tr[1]/td[1]
        f = open(Data1, 'w')
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

            #print(sourcetext1 + ": " + sourcetext2)
            #print(sourcetext3 + ": " + sourcetext4)
            # 写入文本文件 
            
            f.write(sourcetext1 + ": " + sourcetext2 + " ")
            f.write(sourcetext3 + ": " + sourcetext4 + "\n") 
        f.close()
    else:
        print("基本文件已存在")

    # 获取并写入多空交易数据
    if not os.path.exists(Data2):
        duo_kong_button = chrome.find_element(By.XPATH, "/html/body/form/div[2]/a[6]|/html/body/form/div[1]/a[6]")
        duo_kong_button.click()
        page = chrome.page_source
        tree = etree.HTML(page)
        Nodes = tree.xpath("/html/body/script[7]")
        print("第一类网页，一共有" , len(Nodes) , "条多空数据")
        for node in Nodes:
            duo_kong_data = node.xpath("./text()")[0]
            match = re.search(r"var\s+basicdata1Curves\s*=\s*'([^']+)';", duo_kong_data)
            if match:
                duo_kong_data = match.group(1)
            else:
                duo_kong_data = "N/A"
            # 写入文本文件
            f = open(Data2, 'w')
            f.write(duo_kong_data)
        f.close()
    else:
        print("多空文件已存在")

    # 获取并写入日夜交易数据
    if not os.path.exists(Data3):
        ri_ye_button = chrome.find_element(By.XPATH, "/html/body/form/div[2]/a[7]|/html/body/form/div[1]/a[7]")
        ri_ye_button.click()
        page = chrome.page_source
        tree = etree.HTML(page)
        Nodes = tree.xpath("/html/body/script[7]")
        print("第一类网页，一共有" , len(Nodes) , "条日夜数据")
        for node in Nodes:
            ri_ye_data = node.xpath("./text()")[0]
            match = re.search(r"var\s+basicdata1Curves\s*=\s*'([^']+)';", ri_ye_data)
            if match:
                ri_ye_data = match.group(1)
            else:
                ri_ye_data = "N/A"
            # 写入文本文件
            f = open(Data3, 'w')
            f.write(ri_ye_data)
        f.close()
    else:
        print("日夜文件已存在")

    # 获取并写入品种成交数据
    if not os.path.exists(Data4):
        pin_zhong_button = chrome.find_element(By.XPATH, "/html/body/form/div[2]/a[8]|/html/body/form/div[1]/a[8]")
        pin_zhong_button.click()
        page = chrome.page_source
        tree = etree.HTML(page)
        Nodes = tree.xpath("/html/body/script[7]")
        print("第一类网页，一共有" , len(Nodes) , "条品种数据")
        for node in Nodes:
            pin_zhong_button = node.xpath("./text()")[0]
            match = re.search(r"var\s+basicdata1Curves\s*=\s*'([^']+)';", pin_zhong_button)
            if match:
                pin_zhong_button = match.group(1)
            else:
                pin_zhong_button = "N/A"
            # 写入文本文件
            f = open(Data4, 'w')
            f.write(pin_zhong_button)
        f.close()
    else:
        print("品种文件已存在")

    #driver.close()
    chrome.close()
    #lock.release()


# 第二类子网页爬取
def CrawlSecond(url, filedir, filename):
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
    # 通过xpath得到新的url
    page = chrome.page_source
    tree = etree.HTML(page)
    Nodes = tree.xpath("/html/body//div/div/div//ul/li")
    # print("Node:", Nodes, "\n")
    urls = []
    for node in Nodes:
        urls.append(node.xpath("./a/@href")[0])
    # print("urls:", urls, "\n")
    BaseDataUrl = ""
    duo_kong_Url = ""
    ri_ye_Url = ""
    pin_zhong_Url = ""
    for Url in urls:
        if re.search(r'BasicData\.aspx\?id=\d+', Url):
            BaseDataUrl = str(Url)
            #print("BaseDataUrl:", type(BaseDataUrl), "\n")
        elif re.search(r'eom\.aspx\?id=\d+', Url):
            duo_kong_Url = str(Url)
            #print("duo_kong_Url:", duo_kong_Url, "\n")
        elif re.search(r'don\.aspx\?id=\d+', Url):
            ri_ye_Url = str(Url)
            #print("ri_ye_Url:", ri_ye_Url, "\n")
        elif re.search(r'BreedDeal\.aspx\?id=\d+', Url):
            pin_zhong_Url = str(Url)
            #print("pin_zhong_Url:", pin_zhong_Url, "\n")
        else:
            print("未找到匹配的URL")
    

    # 通过'/'符号切分URL(从右侧开始找到第一个'/'符号并切分)
    spliturl = url.rsplit('/', 1)[0]
    # print("spliturl:", type(spliturl), "\n")
    BaseDataUrl = spliturl + "/" + BaseDataUrl
    duo_kong_Url = spliturl + "/" + duo_kong_Url
    ri_ye_Url = spliturl + "/" + ri_ye_Url
    pin_zhong_Url = spliturl + "/" + pin_zhong_Url

    print("BaseDataUrl:", BaseDataUrl, "\n")
    print("duo_kong_Url:", duo_kong_Url, "\n")
    print("ri_ye_Url:", ri_ye_Url, "\n")
    print("pin_zhong_Url:", pin_zhong_Url, "\n")
    
    

    Data1 = filedir + "/" + "基本数据" + "(" + filename + ")" + ".txt"
    Data2 = filedir + "/" + "多空交易数据" + "(" + filename + ")" + ".txt"
    Data3 = filedir + "/" + "日夜交易数据" + "(" + filename + ")" + ".txt"
    Data4 = filedir + "/" + "交易品种数据" + "(" + filename + ")" + ".txt"

    # 获取第二类页面基本数据
    if not os.path.exists(Data1):
        chrome.get(BaseDataUrl)
        page = chrome.page_source
        tree = etree.HTML(page)
        Nodes = tree.xpath("/html/body/form/div/table/tbody/tr")
        print("第二类网页，一共有" , len(Nodes) , "条基本数据")
        f = open(Data1, 'w')
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

            # 写入文本文件 
            f.write(sourcetext1 + ": " + sourcetext2 + " ")
            f.write(sourcetext3 + ": " + sourcetext4 + "\n") 

        f.close()
    else:
        print("基本文件已存在")
        
    # 获取第二类页面多空交易数据
    # /html/head/script[9]
    if not os.path.exists(Data2):
        chrome.get(duo_kong_Url)
        page = chrome.page_source
        tree = etree.HTML(page)
        Nodes = tree.xpath("/html/head/script[9]")
        print("第二类网页，一共有" , len(Nodes) , "条多空数据")
        for node in Nodes:
            duo_kong_data = node.xpath("./text()")[0]
            match = re.findall(r'\[\'(.*?)\',(\d+\.?\d*)\]', duo_kong_data)
            # print("match:", match)
            if match:
                # 写入文本文件
                f = open(Data2, 'w')
                f.write(str(match))
            else:
                print("不存在多空交易数据")
            

        f.close()
    else:
        print("多空文件已存在")

    # 获取第二类页面日夜交易数据
    if not os.path.exists(Data3):
        chrome.get(ri_ye_Url)
        page = chrome.page_source
        tree = etree.HTML(page)
        Nodes = tree.xpath("/html/head/script[9]")
        print("第二类网页，一共有" , len(Nodes) , "条日夜数据")
        for node in Nodes:
            ri_ye_data = node.xpath("./text()")[0]
            match = re.findall(r'\[\'(.*?)\',(\d+\.?\d*)\]', ri_ye_data)
            # print("match:", match)
            if match:
                # 写入文本文件
                f = open(Data3, 'w')
                f.write(str(match))
            else:
                print("不存在日夜交易数据")
    else:    
        print("日夜文件已存在")

    # 获取第二类页面品种成交数据
    if not os.path.exists(Data4):
        chrome.get(pin_zhong_Url)
        page = chrome.page_source
        tree = etree.HTML(page)
        Nodes = tree.xpath("/html/head/script[9]")
        print("第二类网页，一共有" , len(Nodes) , "条品种数据")
        for node in Nodes:
            pin_zhong_data = node.xpath("./text()")[0]
            match = re.findall(r'\[\'(.*?)\',(\d+\.?\d*)\]', pin_zhong_data)
            # print("match:", match)
            if match:
                # 写入文本文件
                f = open(Data4, 'w')
                f.write(str(match))
            else:
                print("不存在品种交易数据")
    else:    
        print("品种文件已存在")

    #driver.close()
    chrome.close()


# 解析首页
def CrawIndexPage():
    # page = getpage(starturl)
    page = driver.page_source
    rank = driver.find_element(By.XPATH, "/html/body/form/nav/ul/input[1]")
    rank_value = rank.get_attribute("value")
    print(f"正在爬取第{rank_value}页")
    if page == "error":
        return
    # page = page.decode('utf-8', 'ignore')
    tree = etree.HTML(page)
    Nodes = tree.xpath("/html/body/form/div[3]/div/table/tbody/tr")
    
    print("一共有参赛者", len(Nodes), "名")
    
    for node in Nodes:
        # 获取所有的 href 属性
        
        urls = node.xpath("./td/a/@href")
        name = node.xpath("./td[2]/text()")[0].replace("/", "") \
            .replace("\\", "") \
            .replace(":", "") \
            .replace("*", "") \
            .replace("?", "") \
            .replace("\"", "") \
            .replace("<", "") \
            .replace(">", "") \
            .replace("|", "") \
            .replace(" ", "")
        
        
        print("name:" + name)
        # print("urls：" , urls)
        newdir = "C:/Users/LiuXiang/Desktop/大数据实践编程/data3/" + name
        os.makedirs(newdir, exist_ok=True)
        print("创建分类目录:" + newdir)
        # 创建线程池，最大数目为10
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            for url in urls:
                match = re.search(r'/spds(\d+)/|/S(\d+)/', url)
                if match:
                    session = match.group(1) or match.group(2)
                    if int(session) > 13:
                        executor.submit(CrawlSourcePage, url, newdir, session)
                        
                    elif int(session) <= 13:
                        executor.submit(CrawlSecond, url, newdir, session)
                else:
                    print("未找到匹配的届数信息")
                    
        # 在此处等待所有线程执行完成
        executor.shutdown(wait=True)

    

class myThread(threading.Thread):
    def __init__(self, url, newdir, name):
        threading.Thread.__init__(self)
        self.url = url
        self.newdir = newdir
        self.name = name

    def run(self):
        CrawlSourcePage(self.url, self.newdir, self.name)


def main():

    driver.get("https://spdsapp.qhrb.com.cn/spds16/match/inner/steadyprofit1!list.action")

    # for i in range (14):
    #     # 使用动态的XPath来查找翻页按钮并点击
    #     next_button = driver.find_element(By.XPATH, "/html/body/form/nav/ul/a[3]")
    #     next_button.click()

    for i in range(1):
        CrawIndexPage()
        # 使用动态的XPath来查找翻页按钮并点击
        next_button = driver.find_element(By.XPATH, "/html/body/form/nav/ul/a[3]")
        next_button.click()
    driver.close()


if __name__ == "__main__":
    main()
