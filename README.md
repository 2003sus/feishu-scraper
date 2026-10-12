# Web Scraper 项目

用 Python 抓取网页内容（文字、图片、表格、视频）的练习项目。

## 项目结构
requests/
├── README.md ← 本文件
├── feishu_test.py ← 飞书文档抓取脚本（主脚本）
├── wet_scraper.py ← 调 wet-mcp 的试验脚本
├── test_mcp.py ← 测 wet-mcp 连接
├── list_tools.py ← 列出 wet-mcp 的工具
├── Requests.py ← 猫眼影院列表抓取
├── cache_*.html ← 本地缓存的页面（避免重复请求）
└── output/ ← 抓取结果
├── content.txt ← 文字
├── images/ ← 图片
├── sheets/ ← 表格截图
└── videos/ ← 视频

text

## 环境要求

- Python 3.11+
- Google Chrome
- 依赖库：

```bash
pip install selenium requests beautifulsoup4 curl_cffi
