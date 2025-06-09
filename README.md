# 🎬 Bilibili Crawler

> 基于 Scrapy + Selenium 的 Bilibili 视频信息爬虫

---

## 🚀 项目简介

Bilibili Crawler 是一个开源的、可扩展的 B 站视频信息采集工具，旨在为数据分析、内容推荐、学术研究等场景提供高质量的数据支持。项目基于 Scrapy 框架，结合 Selenium 实现对动态内容的高效抓取，支持首页、热门、分区、UP主等多种采集模式。

---

## ✨ 主要特性

- 支持 B 站首页/热门视频信息采集
- 动态页面渲染，突破反爬机制
- 数据字段丰富（标题、链接、UP主、封面、时长、播放量、弹幕数等）
- 支持自定义 Cookie，模拟登录采集
- 自动去重与基础数据清洗
- 多种数据导出格式（JSON、CSV、数据库，未来可扩展）
- 代码结构清晰，易于二次开发
- 丰富的配置项，便于自定义采集策略

---

## 🛠️ 环境配置

### 1. 克隆项目
```bash
git clone https://github.com/yourname/bilibili_crawler.git
cd bilibili_crawler
```

### 2. 安装 Miniconda（推荐）

建议使用 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 管理 Python 环境，轻量且易于扩展。

- 访问 [Miniconda 官方下载页面](https://docs.conda.io/en/latest/miniconda.html)
- 选择与你操作系统对应的安装包下载安装
- 安装完成后，重启终端并确保 `conda` 命令可用

### 3. 创建并激活 conda 虚拟环境

```bash
conda create -n spider python=3.8 -y
conda activate spider
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

> 依赖主要包括：scrapy、scrapy-selenium、selenium、chromedriver-autoinstaller 等。

### 5. 配置 ChromeDriver

- 无需手动下载和配置 chromedriver，只需确保已安装 Selenium 4.6.0 及以上版本。
- Selenium 会自动检测本地 Chrome 浏览器版本，并自动下载、管理和调用合适版本的 chromedriver。
- 只需在 requirements.txt 或环境中安装最新版 selenium 即可。
- 如需手动指定 chromedriver 路径，依然可以通过 Selenium 的参数进行自定义。

### 6. 配置 Cookie（可选）

如需采集登录后内容，请在 `bilibili_crawler/spiders/index.py` 中配置你的 Cookie 信息。

---

## 🚦 使用方法

### 首页推荐视频采集

```bash
scrapy crawl index -o result.jsonl
```

- 默认采集 B 站首页推荐视频，结果输出为 JSON Lines 格式。
- 可通过修改 `index.py` 自定义采集目标、字段、导出格式等。
- 常用参数如 `max_refresh_times`（控制刷新次数）、`DOWNLOAD_DELAY`、`CONCURRENT_REQUESTS`、`SELENIUM_DRIVER_ARGUMENTS` 可在 `custom_settings` 中调整。
- 支持 JSON、CSV 等格式导出，未来可扩展数据库存储。
- 可结合 pandas、notebook 进行后续数据分析。

> 后续将支持分区、UP主、视频详情、弹幕、评论等多种采集功能，敬请期待！

---

## 🧩 可扩展性

- 支持采集分区、UP主、视频详情、弹幕、评论等（欢迎贡献！）
- 计划集成定时任务、Web UI、数据可视化等高级功能
- 代码结构模块化，便于插件式扩展

### 🤖 结合 Huggingface Transformers 的创新方向

- **视频标题/评论情感分析**
  - 利用 transformers 预训练模型（如 BERT、RoBERTa）对视频标题、评论、弹幕进行情感分类，自动识别热门视频的情绪倾向。
- **自动标签/话题生成**
  - 使用文本生成模型（如 T5、ChatGLM）为视频内容自动生成标签或摘要，提升内容检索和推荐能力。
- **弹幕/评论智能摘要**
  - 对大量弹幕或评论进行聚合和摘要，帮助用户快速了解视频观众的主要观点和讨论热点。
- **内容相似度与推荐**
  - 基于 transformers 的文本向量表示，计算视频之间的内容相似度，实现更智能的内容推荐或聚类分析。
- **多语言支持与翻译**
  - 利用 transformers 的多语言模型，实现弹幕、评论等内容的自动翻译，拓展国际化应用场景。
- **舆情监测与热点追踪**
  - 结合 transformers 的实体识别、事件抽取能力，自动监测 B 站热点事件、人物和话题。

> 欢迎社区贡献更多基于 transformers 的创新应用思路！

---

## 🤝 贡献指南

欢迎任何形式的贡献！

1. Fork 本仓库，创建新分支
2. 提交你的改动并发起 Pull Request
3. 建议在 PR 前先提 Issue 讨论
4. 遵循代码规范，保持注释清晰

---

## 📄 许可协议

本项目采用 MIT License，详情见 LICENSE 文件。

---

## 💡 致谢

感谢所有开源社区的贡献者！如果你喜欢本项目，欢迎 Star、Fork、提 Issue 或 PR。

---

> ⚠️ 本项目仅供学习与研究使用，请勿用于任何商业或非法用途，采集数据时请遵守目标网站的相关规定。
