import os
import time
from curl_cffi import requests
from bs4 import BeautifulSoup

pages = [
    "https://baike.baidu.com/item/网络爬虫",
    "https://baike.baidu.com/item/人工智能",
    "https://baike.baidu.com/item/机器学习",
]

for url in pages:
    word = url.split("/")[-1]
    cache = f"cache_{word}.html"

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
            continue
        html = r.text
        with open(cache, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  已保存 {cache}")
        time.sleep(2)

    # ── 解析 ──
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1")
    print(f"  标题: {title.get_text(strip=True) if title else '没找到'}")

    print("  === 测试常见 class ===")
    for cls in [
        "lemma-summary", "J-summary", "summary", "summary-content",
        "basicInfo-item", "basic-info", "basic-info-item",
        "para", "para-title", "lemma-content",
    ]:
        found = soup.find(class_=cls)
        print(f"    {cls:30s} -> {'✅' if found else '❌'}")

    print("  === 最常见的 15 个 class ===")
    from collections import Counter
    all_classes = []
    for tag in soup.find_all(class_=True):
        all_classes.extend(tag.get("class", []))
    for cls, count in Counter(all_classes).most_common(15):
        print(f"    {cls:40s} 出现 {count} 次")

    print()