# -*- coding: utf-8 -*-
"""
飞书公开文档抓取器（虚拟滚动 + blob 图片 + 视频 + 表格截图）
- 文字: div.ace-line（边滚边抓，去重，保序）
- 图片: img.docx-image 的 src 是 blob: URL，用 JS fetch -> base64 在滚动中抓取
- 视频: <video> 的 currentSrc 是可直接下载的 drive-stream URL，滚动中收集，末尾带 cookie 下载
- 表格: .docx-table-block 在滚动中出现时立即截图，按文本签名去重
输出: output3/
"""
import time
import os
import base64
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

URL = "https://your-domain.larkoffice.com/docx/YOUR_DOC_ID"

OUT = "output3"
IMG_DIR = os.path.join(OUT, "images")
TBL_DIR = os.path.join(OUT, "tables")
VID_DIR = os.path.join(OUT, "videos")
for d in (IMG_DIR, TBL_DIR, VID_DIR):
    os.makedirs(d, exist_ok=True)

# ───────────── 启动浏览器 ─────────────
opts = webdriver.ChromeOptions()
opts.add_argument("--start-maximized")
opts.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(options=opts)
driver.get(URL)
time.sleep(8)

TITLE = driver.title
print("标题:", TITLE)
print("初始URL:", driver.current_url)

# ───────────── 状态 ─────────────
text_lines = []          # 有序唯一文本
text_seen = set()
img_done = set()         # 已成功保存的 blob url
img_count = 0
img_fail = 0
table_sigs = set()
table_count = 0
video_urls = []          # 有序唯一
video_seen = set()

# ───────────── JS: 找最高的滚动容器并滚动 ─────────────
SCROLL_JS = """
const els = [...document.querySelectorAll('*')].filter(el => {
  const oy = getComputedStyle(el).overflowY;
  return (oy === 'auto' || oy === 'scroll') && el.scrollHeight > el.clientHeight + 50;
});
els.sort((a,b) => b.scrollHeight - a.scrollHeight);
const e = els[0];
if (!e) return null;
const step = arguments[0] || 450;
e.scrollTop = Math.min(e.scrollTop + step, e.scrollHeight);
return {top: e.scrollTop, sh: e.scrollHeight, ch: e.clientHeight,
        atBottom: (e.scrollTop + e.clientHeight) >= (e.scrollHeight - 8)};
"""

# ───────────── JS: 抓取图片 blob -> base64（异步）─────────────
FETCH_IMG_JS = """
const cb = arguments[arguments.length - 1];
const img = arguments[0];
const url = img.currentSrc || img.src;
if (!url) { cb(null); return; }
fetch(url).then(r => r.blob()).then(b => {
  const fr = new FileReader();
  fr.onloadend = () => cb(fr.result);
  fr.onerror = () => cb(null);
  fr.readAsDataURL(b);
}).catch(() => cb(null));
"""

def save_data_url(data_url):
    """data:image/png;base64,XXXX -> 返回 (bytes, ext) 或 None"""
    if not data_url or "," not in data_url:
        return None
    header, b64 = data_url.split(",", 1)
    mime = header.split(";")[0].split(":")[-1].strip()   # image/png
    ext = mime.split("/")[-1] if "/" in mime else "png"
    if ext == "jpeg":
        ext = "jpg"
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return None
    return raw, ext

def capture_frame():
    """抓取当前视口内的 文字/图片/表格/视频"""
    global img_count, img_fail, table_count

    # ── 1. 文字 ──
    for ln in driver.find_elements(By.CSS_SELECTOR, "div.ace-line"):
        try:
            t = (ln.text or "").strip()
        except Exception:
            continue
        if t and t not in text_seen:
            text_seen.add(t)
            text_lines.append(t)

    # ── 2. 图片（blob -> base64，滚动中抓取）──
    for im in driver.find_elements(By.CSS_SELECTOR, "img.docx-image"):
        try:
            src = im.get_attribute("currentSrc") or im.get_attribute("src")
        except Exception:
            continue
        if not src or not src.startswith("blob:"):
            continue
        if src in img_done:
            continue
        try:
            data_url = driver.execute_async_script(FETCH_IMG_JS, im)
        except Exception:
            data_url = None
        res = save_data_url(data_url) if data_url else None
        if res:
            raw, ext = res
            img_count += 1
            fn = os.path.join(IMG_DIR, "img_%03d.%s" % (img_count, ext))
            with open(fn, "wb") as f:
                f.write(raw)
            img_done.add(src)
        else:
            img_fail += 1

    # ── 3. 表格（滚动中出现即截图，按文本签名去重）──
    for tb in driver.find_elements(By.CSS_SELECTOR, ".docx-table-block"):
        try:
            sig = (tb.text or "").strip()[:300]
            if not sig or sig in table_sigs:
                continue
            table_sigs.add(sig)
            table_count += 1
            fn = os.path.join(TBL_DIR, "table_%02d.png" % table_count)
            tb.screenshot(fn)
        except Exception:
            continue

    # ── 4. 视频（收集可下载 URL）──
    for v in driver.find_elements(By.CSS_SELECTOR, "video"):
        try:
            src = v.get_attribute("currentSrc") or v.get_attribute("src")
        except Exception:
            continue
        if src and src.startswith("http") and src not in video_seen:
            video_seen.add(src)
            video_urls.append(src)


# ───────────── 主滚动循环 ─────────────
print("\n开始滚动抓取...")
step = 0
bottom_hits = 0
max_steps = 500
while step < max_steps:
    step += 1
    capture_frame()
    info = driver.execute_script(SCROLL_JS, 450)
    time.sleep(0.5)

    if step % 10 == 0:
        tail = (" | top %d/%d" % (int(info["top"]), int(info["sh"]))) if info else ""
        print("[%3d] 文字 %d | 图 %d | 表 %d | 视频 %d%s"
              % (step, len(text_lines), img_count, table_count, len(video_urls), tail))

    if info and info.get("atBottom"):
        bottom_hits += 1
    else:
        bottom_hits = 0
    if bottom_hits >= 5:
        print("已到底部，停止滚动")
        break

# 最后再抓几帧，确保底部内容加载
for _ in range(3):
    capture_frame()
    time.sleep(0.8)

print("\n" + "=" * 50)
print("文字行: %d" % len(text_lines))
print("图片:   %d 张（失败 %d）" % (img_count, img_fail))
print("表格:   %d 张" % table_count)
print("视频:   %d 个" % len(video_urls))
print("滚动步数: %d" % step)
print("=" * 50)

# ───────────── 保存文字 ─────────────
with open(os.path.join(OUT, "content.txt"), "w", encoding="utf-8") as f:
    f.write("# %s\n\n" % TITLE)
    f.write("\n".join(text_lines))
print("文字已保存 -> %s/content.txt" % OUT)

# ───────────── 下载视频（带 cookie + referer）─────────────
cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
print("\n拿到 %d 个 cookie，开始下载视频..." % len(cookies))
sess = requests.Session()
sess.headers.update({
    "User-Agent": driver.execute_script("return navigator.userAgent"),
    "Referer": URL + "/",
})
for c in driver.get_cookies():
    sess.cookies.set(c["name"], c["value"], domain=c.get("domain", "").lstrip("."))

vid_ok = 0
for i, vurl in enumerate(video_urls, 1):
    try:
        r = sess.get(vurl, stream=True, timeout=180)
        if r.ok and int(r.headers.get("Content-Length", "1")) > 0:
            fn = os.path.join(VID_DIR, "video_%02d.mp4" % i)
            with open(fn, "wb") as f:
                for chunk in r.iter_content(1 << 16):
                    f.write(chunk)
            sz = os.path.getsize(fn)
            print("  video_%02d.mp4  %.1f MB  OK" % (i, sz / 1024 / 1024))
            vid_ok += 1
        else:
            print("  video_%02d 失败: HTTP %s" % (i, r.status_code))
    except Exception as e:
        print("  video_%02d 失败: %s" % (i, e))

print("\n视频下载完成: %d/%d" % (vid_ok, len(video_urls)))

with open(os.path.join(OUT, "video_urls.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(video_urls))

print("\n全部完成。输出目录:", OUT)
driver.quit()

