import json
import requests
from time import sleep

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import setting

session = None


def set_session():
    url = f"https://qiita.com/login"

    # ローカル上でのChrome Driverを指定
    # driver_path = "./chromedriver.exe"

    # Heroku上のChrome Driverを指定(※デプロイするときはコメントを外す)
    driver_path = '/app/.chromedriver/bin/chromedriver'

    # Headless Chromeをあらゆる環境で起動させるオプション
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--user-agent=hogehoge')
    options.add_argument('--proxy-server="direct://"')
    options.add_argument('--proxy-bypass-list=*')
    options.add_argument('--headless')

    driver = webdriver.Chrome(executable_path=driver_path, options=options)
    driver.get(url)

    identity = driver.find_element_by_name("identity")
    password = driver.find_element_by_name("password")
    identity.send_keys(setting.QIITA_USER_NAME)
    password.send_keys(setting.QIITA_PASSWORD)
    sleep(0.2)

    login_btn = driver.find_element_by_name("commit")
    sleep(0.2)
    login_btn.click()

    s = requests.session()

    # セッションの受け渡し
    for cookie in driver.get_cookies():
        s.cookies.set(cookie["name"], cookie["value"])

    driver.close()

    global session
    session = s
    print("FINISH")


def get_article_list(scope):
    html = session.get("https://qiita.com/?scope={}".format(scope))
    soup = BeautifulSoup(html.text, "html.parser")
    items = soup.find(attrs={"data-hyperapp-app": "Trend"})
    items_json = json.loads(items.get("data-hyperapp-props"))

    return items_json["trend"]["edges"]


def get_trend_info(scope="daily", max_amount=5):
    article_list = get_article_list(scope)
    article_url_temp = "https://qiita.com/{user_name}/items/{article_id}"

    article_info = {
        "title": [],
        "likes_count": [],
        "url": []
    }

    for article in article_list[:max_amount]:
        article = article["node"]
        title = article["title"]  # 記事タイトル
        like_count = article["likesCount"]  # LGTMの数
        user_name = article["author"]["urlName"]  # ユーザー名
        article_id = article["uuid"]  # 記事ID
        article_url = article_url_temp.format(
            user_name=user_name,
            article_id=article_id
        )

        # リストに格納
        article_info["title"].append(title)
        article_info["likes_count"].append(like_count)
        article_info["url"].append(article_url)

    return article_info
