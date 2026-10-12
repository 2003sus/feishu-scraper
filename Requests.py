import os
import time
from curl_cffi import requests
from bs4 import BeautifulSoup

# 你要爬的所有词条
pages = [
    "https://baike.baidu.com/item/网络爬虫",
    "https://baike.baidu.com/item/人工智能",
    "https://baike.baidu.com/item/机器学习",
]

for url in pages:
    # ── 拼缓存文件名 ──
    word = url.split("/")[-1]           # "网络爬虫"
    cache = f"cache_{word}.html"        # "cache_网络爬虫.html"

    # ── 有缓存就读，没有才请求 ──
    if os.path.exists(cache):
        print(f"[缓存] {word}")
        with open(cache, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        print(f"[请求] {word}")
        r = requests.get(url, impersonate="edge101")
        print(f"  状态码: {r.status_code}")

        if not r.ok:
            print(f"  被拦了，跳过 {word}")
            continue                     # 被拦就跳过，别继续

        html = r.text
        with open(cache, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  已保存 {cache}")

        time.sleep(2)                    # 每次真实请求后等 2 秒

    # ── 解析（现在只测标题）──
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1")
    print(f"  标题: {title.get_text(strip=True) if title else '没找到'}\n") 