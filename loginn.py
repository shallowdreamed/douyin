import json
import time
import re
import traceback
import random
import brotli
import pandas as pd
import pickle  # 确保导入pickle模块



from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import traceback


from seleniumwire import webdriver  # 使用 seleniumwire 拦截网络请求
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from datetime import datetime  # 导入datetime模块


from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置ChromeDriver的路径
##CHROM+6EDRIVER_PATH = 'C:/install/chromedriver-win64/chromedriver.exe'  # 替换为您的chromedriver路径
# 配置目标用户的抖音主页URL


service = Service('C:/chromedriver-win64/chromedriver.exe')
# 配置Selenium选项
chrome_options = Options()

#chrome_options.add_argument('--headless')  # 无头模式
chrome_options.page_load_strategy = 'eager'
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 防止被检测为自动化脚本
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-infobars')
chrome_options.add_argument('--disable-extensions')  # 禁用扩展
chrome_options.add_argument('--disable-gpu')  # 禁用 GPU 加速
# 禁用 WebGL
chrome_options.add_argument('--disable-webgl')
chrome_options.add_argument('--disable-gpu')
# 添加建议的 flag
chrome_options.add_argument('--enable-unsafe-swiftshader')
# 设置用户数据目录（保存登录状态）
chrome_options.add_argument(r'user-data-dir=C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default')
driver = None







# -------------------------------------------------------------
# 主函数
# -------------------------------------------------------------
# 主函数
# -------------------------------------------------------------
def main():
    
    global driver
    try:
        # 打开抖音首页以设置域
        driver = webdriver.Chrome(service=service,options=chrome_options)
        driver.get('https://www.douyin.com/')
        #print("Navigated to Douyin homepage.")
        #time.sleep(3)  # 等待页面加载

        # 添加以下代码以等待手动登录
        input("请在浏览器中完成登录操作后，按 Enter 键继续...")

        # 可选：保存登录后的 Cookies 以便未来使用
        # save_cookies(driver, 'cookies.pkl')

        # 验证是否已登录

    except Exception as e:
        print(f"An error occurred in main: {e}")
        traceback.print_exc()
    finally:
        # 关闭 WebDriver
        driver.quit()
        print("WebDriver closed.")


# -------------------------------------------------------------
# 入口点
# -------------------------------------------------------------
if __name__ == "__main__":
    main()

