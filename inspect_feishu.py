import time, os, io
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image

URL = "https://your-domain.larkoffice.com/docx/YOUR_DOC_ID"
LOG = "inspect_log.txt"
logf = open(LOG, "w", encoding="utf-8")
def log(*a):
    s = " ".join(str(x) for x in a); print(s); logf.write(s + "\n"); logf.flush()

opts = webdriver.ChromeOptions()
opts.add_argument("--start-maximized")
driver = webdriver.Chrome(options=opts)
driver.get(URL)
time.sleep(8)
os.makedirs("tbl_test", exist_ok=True)

def find_table(rid, down=True):
    for _ in range(160):
        for tb in driver.find_elements(By.CSS_SELECTOR, ".docx-table-block"):
            if tb.get_attribute("data-record-id") == rid:
                return tb
        driver.execute_script("""
          const els=[...document.querySelectorAll('*')].filter(el=>{const oy=getComputedStyle(el).overflowY;return (oy==='auto'||oy==='scroll')&&el.scrollHeight>el.clientHeight+50;});
          els.sort((a,b)=>b.scrollHeight-a.scrollHeight);
          const e=els[0];
          if(e) e.scrollTop = arguments[0] ? Math.min(e.scrollTop+400, e.scrollHeight) : Math.max(0, e.scrollTop-400);
        """, down)
        time.sleep(0.3)
    return None

def scroller_rect():
    return driver.execute_script("""
      const sc=[...document.querySelectorAll('*')].filter(e=>{const oy=getComputedStyle(e).overflowY;return (oy==='auto'||oy==='scroll')&&e.scrollHeight>e.clientHeight+50;}).sort((a,b)=>b.scrollHeight-a.scrollHeight)[0];
      const r=sc.getBoundingClientRect();
      return {x:r.left, y:r.top, w:r.width, h:r.height, ch:sc.clientHeight};
    """)

def table_geo(rid):
    return driver.execute_script("""
      const el=document.querySelector('.docx-table-block[data-record-id="%s"]');
      if(!el) return null;
      const sc=[...document.querySelectorAll('*')].filter(e=>{const oy=getComputedStyle(e).overflowY;return (oy==='auto'||oy==='scroll')&&e.scrollHeight>e.clientHeight+50;}).sort((a,b)=>b.scrollHeight-a.scrollHeight)[0];
      const er=el.getBoundingClientRect(); const sr=sc.getBoundingClientRect();
      return {top: er.top - sr.top, left: er.left - sr.left, h: er.height, w: er.width, ch: sc.clientHeight};
    """ % rid)

def capture_table(rid):
    el = find_table(rid, down=True)
    if el is None:
        log("NOT FOUND", rid); return None, None, None
    rect = scroller_rect()
    H = rect["h"]
    step = int(H * 0.6)
    # align table top to scroller top
    driver.execute_script("""
      const el=document.querySelector('.docx-table-block[data-record-id="%s"]');
      const sc=[...document.querySelectorAll('*')].filter(e=>{const oy=getComputedStyle(e).overflowY;return (oy==='auto'||oy==='scroll')&&e.scrollHeight>e.clientHeight+50;}).sort((a,b)=>b.scrollHeight-a.scrollHeight)[0];
      const er=el.getBoundingClientRect(); const sr=sc.getBoundingClientRect();
      sc.scrollTop += (er.top - sr.top);
    """ % rid)
    time.sleep(1.3)

    box = (int(rect["x"]), int(rect["y"]), int(rect["x"]+rect["w"]), int(rect["y"]+rect["h"]))
    crops = []
    first_geo = None
    for i in range(80):
        geo = table_geo(rid)
        if geo is None:
            break
        if first_geo is None:
            first_geo = geo
        png = driver.get_screenshot_as_png()
        full = Image.open(io.BytesIO(png)).convert("RGB")
        crops.append(full.crop(box))
        if geo["top"] + geo["h"] <= geo["ch"] + 4:
            log(f"bottom at slice {i} top={geo['top']:.0f} h={geo['h']:.0f} ch={geo['ch']:.0f}")
            break
        driver.execute_script("""
          const sc=[...document.querySelectorAll('*')].filter(e=>{const oy=getComputedStyle(e).overflowY;return (oy==='auto'||oy==='scroll')&&e.scrollHeight>e.clientHeight+50;}).sort((a,b)=>b.scrollHeight-a.scrollHeight)[0];
          sc.scrollTop += arguments[0];
        """, step)
        time.sleep(0.55)
    return crops, step, first_geo

def stitch_stride(crops, step, first_geo, name):
    if not crops: return
    cropH = crops[0].height
    W = crops[0].width
    totalH = (len(crops)-1)*step + cropH
    canvas = Image.new("RGB", (W, totalH), "white")
    for i, c in enumerate(crops):
        canvas.paste(c, (0, i*step))
    # tight-crop to the table region using first_geo (table top ~0 after align)
    top0 = max(0, int(first_geo["top"]))
    th = int(first_geo["h"])
    left0 = max(0, int(first_geo["left"]))
    w0 = int(first_geo["w"])
    y1 = min(canvas.height, top0 + th + 4)
    x1 = min(canvas.width, left0 + w0 + 4)
    tight = canvas.crop((left0, top0, x1, y1))
    out = os.path.join("tbl_test", name)
    tight.save(out)
    log("stitched ->", out, "full", canvas.size, "tight", tight.size, "(table h=%d)" % th)

crops, step, fg = capture_table("YOUR_RECORD_ID")
log("crops:", len(crops), "step:", step, "first_geo:", fg)
stitch_stride(crops, step, fg, "t_faq_stride.png")

log("\nDONE")
logf.close()
driver.quit()








