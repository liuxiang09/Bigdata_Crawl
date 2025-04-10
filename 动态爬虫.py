from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time


# 指定chromedriver的绝对路径
driver_path = r"D:\chromedriver-win64\chromedriver.exe"
# 设置Chrome驱动程序服务
service = Service(driver_path)
# 生成随机 User-Agent
user_agent = UserAgent().random
options = webdriver.ChromeOptions()
options.add_argument(f'user-agent={user_agent}')
print(user_agent)
# 初始化driver并设置 ChromeOptions
driver = webdriver.Chrome(service=service, options=options)

# 请求页面，打开网页
# https://spdsapp.qhrb.com.cn/spds16/match/inner/steadyprofit1!list.action
driver.get("https://spdspc.qhrb.com.cn/")
# 停止5秒，等待页面加载完成
time.sleep(5) 

# next_button = driver.find_element(By.XPATH, "/html/body/form/nav/ul/a[3]")
# 获取网页源代码
page_source = driver.page_source
print(page_source)
# print(page_source)
# 通过特定的 XPath 来定位元素
#target_element = driver.find_element(By.XPATH, "/html/body/form/div[3]/div/table/tbody/tr[1]/td[1]")
#print(target_element.text)

# 使用动态的XPath来查找翻页按钮并点击
#next_button = driver.find_element(By.XPATH, "/html/body/form/nav/ul/a[3]")
#next_button.click()
input("请按回车键继续...")
# 关闭当前页面
driver.close()


