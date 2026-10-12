import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

os.makedirs("output/images", exist_ok=True)
os.makedirs("output/sheets", exist_ok=True)
os.makedirs("output/videos", exist_ok=True)

driver = webdriver.Chrome()
driver.get("https://your-domain.larkoffice.com/docx/YOUR_DOC_ID")
time.sleep(5)
driver.find_element(By.TAG_NAME, "body").click()
time.sleep(1)

# ── 存储 ──
all_lines = []
seen_lines = set()
img_urls = set()
sheet_keys = set()
video_urls = set()
sheet_count = 0

last_text = 0
last_img = 0
stuck = 0
step = 0

while True:
    step += 1

    # ── 1. 抓文字 ──
    for line in driver.find_elements(By.CSS_SELECTOR, 'div.ace-line'):
        text = line.text.strip()
        if text and text not in seen_lines:
            seen_lines.add(text)
            all_lines.append(text)

    # ── 2. 抓图片（关键修正：img.docx-image）──
    for img in driver.find_elements(By.CSS_SELECTOR, 'img.docx-image'):
        try:
            src = img.get_attribute("src")
            if src and src.startswith("http"):
                img_urls.add(src)
        except Exception:
            continue

    # ── 3. 抓表格（截图）──
    for s in driver.find_elements(By.CSS_SELECTOR, '.docx-sheet-block'):
        try:
            loc = s.location
            key = f"{loc['x']}_{loc['y']}"
            if key not in sheet_keys:
                sheet_keys.add(key)
                sheet_count += 1
                s.screenshot(f"output/sheets/sheet_{sheet_count}.png")
                print(f"  表格 sheet_{sheet_count}.png")
        except Exception:
            continue

    # ── 4. 抓视频 ──
    for v in driver.find_elements(By.CSS_SELECTOR, 'video'):
        try:
            src = v.get_attribute("src")
            if src:
                video_urls.add(src)
            for source in v.find_elements(By.CSS_SELECTOR, 'source'):
                s2 = source.get_attribute("src")
                if s2:
                    video_urls.add(s2)
        except Exception:
            continue

    print(f"[{step}] 文字 {len(all_lines)} | 图片 {len(img_urls)} | 表格 {sheet_count} | 视频 {len(video_urls)}")

    # ── 滚动 ──
    driver.find_element(By.TAG_NAME, "body").send_keys("\ue00f")
    time.sleep(1.2)

    # ── 退出条件 ──
    if len(all_lines) == last_text and len(img_urls) == last_img:
        stuck += 1
        if stuck >= 8:
            print("内容不再增长，停止")
            break
    else:
        stuck = 0
    last_text = len(all_lines)
    last_img = len(img_urls)

# ── 拿 Selenium 的 Cookie（下载图片/视频用）──
selenium_cookies = driver.get_cookies()
cookies = {c['name']: c['value'] for c in selenium_cookies}
print(f"\n拿到 {len(cookies)} 个 Cookie")

# ── 下载图片 ──
print(f"\n下载 {len(img_urls)} 张图片...")
img_ok = 0
for i, url in enumerate(img_urls):
    try:
        r = requests.get(url, cookies=cookies, timeout=15)
        if r.ok:
            ext = "png"
            if ".jpg" in url or ".jpeg" in url:
                ext = "jpg"
            elif ".gif" in url:
                ext = "gif"
            elif ".webp" in url:
                ext = "webp"
            with open(f"output/images/img_{i+1}.{ext}", "wb") as f:
                f.write(r.content)
            img_ok += 1
            print(f"  img_{i+1}.{ext} ✅")
        else:
            print(f"  img_{i+1} 失败: 状态码 {r.status_code}")
    except Exception as e:
        print(f"  img_{i+1} 失败: {e}")

# ── 打印视频 URL ──
print(f"\n视频 URL:")
for i, url in enumerate(video_urls):
    print(f"  {i+1}. {url}")

# ── 保存文字 ──
with open("output/content.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(all_lines))

print(f"\n{'='*40}")
print(f"文字: {len(all_lines)} 行")
print(f"图片: {img_ok} 张")
print(f"表格: {sheet_count} 张")
print(f"视频: {len(video_urls)} 个（URL 已打印）")
print(f"滚了 {step} 次")
print(f"{'='*40}")

input("按回车关闭...")
driver.quit()