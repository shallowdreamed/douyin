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


service = Service('C:/install/chromedriver/chromedriver.exe')
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







# -------------------------- 输入输出 ---------------------------
input_csv = 'user_profiles.csv'  # CSV 文件名，需包含“用户主页”列
authors_output_csv = 'douyin_authors_with_videostest.csv'  # 输出文件名



# 读取输入 CSV 文件
df_users = pd.read_csv(input_csv)

# 检查是否包含“用户主页”列
if '用户主页' not in df_users.columns:
    print(f"输入的 CSV 文件 '{input_csv}' 中不包含 '用户主页' 列。请检查文件格式。")
    driver.quit()
    exit()


# 用于存储所有用户（作者信息 + 视频数据）
authors_data = []

processed_requests = set()  # 用于存储已处理的请求 URL，防止重复处理

# 用于识别抖音请求中用户信息和视频数据的关键字
PROFILE_URL_KEYWORD = '/aweme/v1/web/user/profile/other'
POST_URL_KEYWORD = '/aweme/v1/web/aweme/post'

# -------------------------------------------------------------
# 函数：加载Cookies（暂时不使用，保留以备将来使用）
# -------------------------------------------------------------
def load_cookies_from_file(driver, cookies_file='cookies.json'):
    try:
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        if not cookies:
            print("Cookies 文件为空。")
            return
        for cookie in cookies:
            # 跳过没有 name 或 value 的 Cookies
            if not cookie.get('name') or not cookie.get('value'):
                print(f"Skipping cookie with missing name or value: {cookie}")
                continue
            # Selenium 需要的 cookie 字段：name, value, domain, path, expiry, etc.
            # 确保 cookie 字段格式正确
            cookie_dict = {
                'name': cookie.get('name'),
                'value': cookie.get('value'),
                'domain': cookie.get('domain'),
                'path': cookie.get('path', '/'),
            }
            # 使用 'expirationDate' 作为 'expiry'
            if 'expirationDate' in cookie:
                cookie_dict['expiry'] = int(cookie['expirationDate'])
            # 删除不支持的字段（如果有）
            # Selenium 不需要 'sameSite', 'secure', 'httpOnly', etc.
            # 这些字段可以保留，但 Selenium 会忽略它们
            try:
                driver.add_cookie(cookie_dict)
                print(f"已添加 Cookie: {cookie_dict['name']}")
            except Exception as e:
                print(f"添加 Cookie {cookie_dict['name']} 失败: {e}")
        print("Cookies 成功从文件加载。")
        
        # 打印当前 Cookies
        print("当前浏览器中的 Cookies:")
        for c in driver.get_cookies():
            print(c)
        
    except json.JSONDecodeError as e:
        print(f"解析 JSON 时出错: {e}")
    except FileNotFoundError:
        print(f"找不到 Cookies 文件: {cookies_file}")
    except Exception as e:
        print(f"加载 Cookies 时出错: {e}")

# -------------------------------------------------------------
# 函数：保存Cookies
# -------------------------------------------------------------
def save_cookies(driver, cookies_file='cookies.pkl'):
    try:
        cookies = driver.get_cookies()
        with open(cookies_file, 'wb') as f:
            pickle.dump(cookies, f)
        print("Cookies saved successfully.")
    except Exception as e:
        print(f"Failed to save cookies: {e}")

# -------------------------------------------------------------
# 函数：解析作者信息
# -------------------------------------------------------------
def parse_author_data(response, author, current_url):
    """
    解析作者信息，填充到 author 字典中
    """
    try:
        raw_data = response.body
        content_encoding = response.headers.get('Content-Encoding', '').lower()

        # 根据响应头解压
        if content_encoding == 'br':
            raw_data = brotli.decompress(raw_data)
            print("Decompressed Brotli data.")
        elif content_encoding == 'gzip':
            import gzip
            import io
            with gzip.GzipFile(fileobj=io.BytesIO(raw_data)) as gz:
                raw_data = gz.read()
            print("Decompressed gzip data.")
        elif content_encoding == 'deflate':
            import zlib
            raw_data = zlib.decompress(raw_data)
            print("Decompressed deflate data.")

        # 解码
        raw_text = raw_data.decode('utf-8', errors='ignore')
        data = json.loads(raw_text)

        # 提取作者资料
        profile = data.get('user', {})

        # 设置作者的 URL
        author['url'] = current_url

        # 按照 JavaScript 脚本映射字段
        author['uid'] = profile.get('unique_id') if profile.get('unique_id') else profile.get('short_id', '')
        author['nickname'] = profile.get('nickname', '')
        author['favoratedCount'] = profile.get('total_favorited', 0)
        author['followerCount'] = profile.get('followers_count', 0)
        author['followingCount'] = profile.get('following_count', 0)
        author['favoritingCount'] = profile.get('favoriting_count', 0)
        
        gender = profile.get('gender', 0)
        author['gender'] = "男" if gender == 1 else ("女" if gender == 2 else "")

        # 年龄解析
        user_age = profile.get('user_age', 0)
        author['age'] = user_age if isinstance(user_age, int) and user_age > 0 else None

        # IP属地
        ip_location = profile.get('ip_location')
        author['ipLocation'] = ip_location.replace('IP属地：', '') if ip_location else None

        # 省份和城市
        author['province'] = profile.get('province', '')
        author['city'] = profile.get('city', '')

        # 发布视频数
        author['postCount'] = profile.get('aweme_count', 0)

        # 更多字段映射
        author['hasShop'] = profile.get('with_fusion_shop_entry', False)
        author['hasLiveCommerce'] = profile.get('live_commerce', False)
        author['signature'] = profile.get('signature','')
        author['withCommerceEnterpriseTabEntry'] = profile.get('with_commerce_enterprise_tab_entry', False)
        author['withCommerceEntry'] = profile.get('with_commerce_entry', False)
        author['withNewGoods'] = profile.get('with_new_goods', False)
        author['youtubeChannelId'] = profile.get('youtube_channel_id', '')
        author['youtubeChannelTitle'] = profile.get('youtube_channel_title', '')
        author['showFavoriteList'] = profile.get('show_favorite_list', False)
        author['showSubscription'] = profile.get('show_subscription', False)
        author['isActivityUser'] = profile.get('is_activity_user', False)
        author['isBan'] = profile.get('is_ban', False)
        author['isBlock'] = profile.get('is_block', False)
        author['isBlocked'] = profile.get('is_blocked', False)
        author['isEffectArtist'] = profile.get('is_effect_artist', False)
        author['isGovMediaVip'] = profile.get('is_gov_media_vip', False)
        author['isMixUser'] = profile.get('is_mix_user', False)
        author['isNotShow'] = profile.get('is_not_show', False)
        author['isSeriesUser'] = profile.get('is_series_user', False)
        author['isSharingProfileUser'] = profile.get('is_sharing_profile_user', False)
        author['isStar'] = profile.get('is_star', False)
        author['isoCountryCode'] = profile.get('iso_country_code', '')
        author['customVerify'] = profile.get('custom_verify', '')
        author['hasMcn'] = ('mcn' in profile.get('account_info_url', '')) if profile.get('account_info_url') else False

        # 群聊数量解析
        author['groupChatCount'] = 0
        card_entries = profile.get('card_entries', [])
        if isinstance(card_entries, list):
            group_chat_entry = next(
                (entry for entry in card_entries if entry.get('sub_title') and '群聊' in entry['sub_title']),
                None
            )
            if group_chat_entry:
                match = re.search(r'(\d+)个群聊', group_chat_entry['sub_title'])
                if match:
                    author['groupChatCount'] = int(match.group(1))

        # 添加创建时间
        # 将创建时间转换为日期时间格式
        author['create_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 当前时间的日期时间字符串

        print(f"Author data for UID {author.get('uid','未知')} extracted.")

    except Exception as e:
        print(f"Error parsing author data: {e}")
        traceback.print_exc()

# -------------------------------------------------------------
# 函数：解析视频数据
# -------------------------------------------------------------
def parse_post_data(response, author, start_idx=1, max_videos=50):
    """
    解析视频列表，并将前 `max_videos` 条目以动态字段添加到 author 字典中
    :param response: 网络响应对象
    :param author: 作者信息字典
    :param start_idx: 视频字段的起始索引
    :param max_videos: 最大视频数量
    :return: 解析的视频数量
    """
    videos_parsed = 0
    try:
        raw_data = response.body
        content_encoding = response.headers.get('Content-Encoding', '').lower()

        if content_encoding == 'br':
            raw_data = brotli.decompress(raw_data)
            print("Decompressed Brotli data.")
        elif content_encoding == 'gzip':
            import gzip
            import io
            with gzip.GzipFile(fileobj=io.BytesIO(raw_data)) as gz:
                raw_data = gz.read()
            print("Decompressed gzip data.")
        elif content_encoding == 'deflate':
            import zlib
            raw_data = zlib.decompress(raw_data)
            print("Decompressed deflate data.")

        # 解码
        raw_text = raw_data.decode('utf-8', errors='ignore')
        data = json.loads(raw_text)

        aweme_list = data.get('aweme_list', [])
        for aweme in aweme_list:

            post_title = aweme.get('desc', '').replace('\n', ' ').strip()
            # 提取标签（Tags）
            tags = []
            text_extra = aweme.get('text_extra', [])
            if isinstance(text_extra, list):
                for item in text_extra:
                    if item.get('hashtag_name'):
                        tags.append(item['hashtag_name'])
                    elif item.get('user_id'):  # 处理用户标签，如 @用户名
                        tags.append(f"@{item['user_id']}")
            tag_str = '#'.join(tags) if tags else ""  # 标签用#连接

            # 提取分类（Video Tags）
            video_tags = []
            video_tag_list = aweme.get('video_tag', [])
            if isinstance(video_tag_list, list):
                for tag in video_tag_list:
                    if tag.get('tag_name'):
                        video_tags.append(tag['tag_name'])
            video_tag_str = '->'.join(video_tags) if video_tags else ""  # 分类用->连接       

            # 将时间戳转换为日期时间格式
            timestamp = aweme.get('create_time', 0)
            try:
                post_datetime = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')  # 转换为日期时间字符串
            except Exception:
                post_datetime = None
            like_count = aweme.get('statistics', {}).get('digg_count', 0)
            share_count = aweme.get('statistics', {}).get('share_count', 0)
            comment_count = aweme.get('statistics', {}).get('comment_count', 0)
            collect_count = aweme.get('statistics', {}).get('collect_count', 0)
            duration = aweme.get('duration', 0) / 1000  # 转换为秒

            # 动态字段名：v1_title, v1_create_datetime, ...
            idx = start_idx + videos_parsed
            if idx > max_videos:
                break  # 限制最大视频数量
            author[f'v{idx}_title'] = post_title
            author[f'v{idx}_tag'] = tag_str  # 标签字段
            author[f'v{idx}_video_tag'] = video_tag_str  # 分类字段
            author[f'v{idx}_create_datetime'] = post_datetime  # 日期时间字符串
            author[f'v{idx}_like_count'] = like_count
            author[f'v{idx}_share_count'] = share_count
            author[f'v{idx}_comment_count'] = comment_count
            author[f'v{idx}_collect_count'] = collect_count
            author[f'v{idx}_duration'] = duration
            videos_parsed += 1

        print(f"Parsed {videos_parsed} posts starting from index {start_idx} for UID {author.get('uid','未知')}.")


        return videos_parsed

    except Exception as e:
        print(f"Error parsing post data: {e}")
        traceback.print_exc()
        return videos_parsed

# -------------------------------------------------------------
# 函数：键盘滚动页面
# -------------------------------------------------------------

def click_and_scroll(driver, num_scrolls=3, pause_time=0.7):
    """
    确保点击页面使其获取焦点，并执行键盘下拉滚动。
    :param driver: Selenium WebDriver 对象
    :param num_scrolls: 滚动次数
    :param pause_time: 每次滚动后的暂停时间（秒）
    """
    try:
        # 获取页面的 body 元素
        body = driver.find_element(By.TAG_NAME, 'body')
        body_width = body.size['width']
        body_width = body.size['height']
        

        # 创建 ActionChains 对象
        actions = ActionChains(driver)



        # 创建 ActionChains 对象，用于模拟键盘操作
        for i in range(num_scrolls):
            # 确保每次滚动前都获取焦点
            # 将鼠标移动到页面中心
            actions.move_to_element_with_offset(body, body_width-25, body_width/2)
            actions.click()  # 在右侧位置点击
            actions.perform()

            # 模拟按下 "Page Down" 键进行滚动
            body.send_keys(Keys.PAGE_DOWN)  # 直接使用 send_keys 来模拟滚动
            print(f"Performed scroll {i+1}/{num_scrolls} down")
            time.sleep(pause_time)  # 暂停，模拟延时

        print("Keyboard scroll completed.")
    except Exception as e:
        print(f"Error while performing keyboard scroll: {e}")


def restart_driver():
    driver.quit()  # 退出当前WebDriver
    driver = webdriver.Chrome(options=chrome_options)  # 重新启动WebDrive



# -------------------------------------------------------------
# 函数：处理单个用户主页
# -------------------------------------------------------------
def process_user_profile(user_url):
    """
    处理单个用户主页，抓取作者信息和视频数据
    """
    author = {}
    
    try:


        driver.get(user_url)
        print(f"Navigating to {user_url}")

        # 等待页面加载
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        print("Page loaded.")


        random_sleep = random.uniform(0.7 , 2)
        print(f"Sleeping for {random_sleep:.2f} seconds...")
        time.sleep(random_sleep)

        # 进行键盘滚动加载
        click_and_scroll(driver)

        current_idx = 1
        time.sleep(3)

        # 捕获并解析网络请求
        for request in driver.requests:
            if request.response:
                if PROFILE_URL_KEYWORD in request.url:
                    #print(f"Processing profile request: {request.url}")
                    parse_author_data(request.response, author, current_url=user_url)
    
        # 捕获并解析网络请求
        for request in driver.requests:
            if request.response :
                if POST_URL_KEYWORD in request.url:
                    #print(f"Processing post request: {request.url}")
                    videos_parsed = parse_post_data(request.response, author, start_idx=current_idx, max_videos=50)
                    current_idx += videos_parsed       

        print(f"Processed user {author.get('uid', '未知')}")

        return author  # 返回作者数据


    except TimeoutException:
        print(f"Timeout while loading {user_url}")
    except WebDriverException as e:
        print(f"WebDriverException while processing {user_url}: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"An error occurred while processing {user_url}: {e}")
        traceback.print_exc()




# 设置输出文件路径
output_file = 'user_processing_times.txt'



# -------------------------------------------------------------
# 主函数
# -------------------------------------------------------------
# 主函数
# -------------------------------------------------------------
def main():
    
    global driver
    try:
        # 打开抖音首页以设置域
        #driver.get('https://www.douyin.com/')
        #print("Navigated to Douyin homepage.")
        #time.sleep(3)  # 等待页面加载

        # 添加以下代码以等待手动登录
        ##input("请在浏览器中完成登录操作后，按 Enter 键继续...")

        # 可选：保存登录后的 Cookies 以便未来使用
        # save_cookies(driver, 'cookies.pkl')

        # 验证是否已登录
        

        # 记录循环开始时间
        start_time = time.time()



        # 遍历所有用户主页链接
        for index, row in df_users.iterrows():
            
            driver = webdriver.Chrome(service=service,options=chrome_options)
            user_url = row['用户主页']
            print(f"\nProcessing user {index + 1}/{len(df_users)}: {user_url}")

            author = process_user_profile(user_url)
            driver.quit()
            
    
            # 将每个作者数据单独写入文件
            if author:  # 如果解析到了作者数据
                df_author = pd.DataFrame([author])  # 将单个作者数据转换为 DataFrame
                df_author.to_csv(authors_output_csv, mode='a', header=not pd.io.common.file_exists(authors_output_csv), index=False, encoding='utf-8-sig')  # 追加写入
                print(f"Author {author.get('uid', '未知')} data saved to '{authors_output_csv}'.")

            # 防止过于频繁的请求
            random_sleep = random.uniform(0.2, 0.7)
            print(f"Sleeping for {random_sleep:.2f} seconds before next user...")
            time.sleep(random_sleep)
        
        # 记录循环结束时间
        end_time = time.time()

        # 计算总时间
        total_time = end_time - start_time

        # 将执行时间写入文件
        with open(output_file, 'w') as file:
             file.write(f"The loop took {total_time:.4f} seconds to execute.\n")

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

