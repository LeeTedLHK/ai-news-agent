# AI News Agent

每周自动搜索近 7 天 AI 领域要闻及 X/Twitter 讨论，经 DeepSeek 翻译整理后发送到 Gmail。

## 工作流程

```
每日 UTC 0:00 (北京时间 8:00) GitHub Actions 自动触发
  │
  ├─ 1. GitHub Actions Cache   → 恢复已发送 URL 历史（最多 50 条），避免重复
  ├─ 2. Tavily Search API      → 英文 + 中文多关键词搜索（topic="news" + time_range="week"）
  ├─ 3. Tavily Social Media    → X/Twitter 搜索 AI 相关讨论（platform="x" + time_range="week"）
  ├─ 4. URL 去重 + 严格日期过滤 → 新闻与 X 分别去重、剔除无日期或超范围结果
  ├─ 5. DeepSeek deepseek-v4-flash → 新闻精选 3 条 + X 讨论精选 3 条，英文翻译为中文
  ├─ 6. HTML 邮件渲染           → 6 张编号卡片，新闻 3 张 + X 讨论 3 张
  └─ 7. Gmail SMTP 发送 → 推送到指定邮箱
  │
  └─ 8. GitHub Actions Cache   → 保存新 URL 至 history，供下次去重
```

## 快速开始

### 本地运行

```bash
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 API Key 和邮箱配置
python main.py
```

### GitHub Actions

1. Fork / 推送本项目到 GitHub
2. 在 Repo → Settings → Secrets and variables → Actions 添加以下 Secrets：

| Secret | 说明 |
|--------|------|
| `TAVILY_API_KEY` | [Tavily Search API Key](https://app.tavily.com) |
| `DEEPSEEK_API_KEY` | [DeepSeek API Key](https://platform.deepseek.com) |
| `SMTP_USER` | Gmail 地址 |
| `SMTP_PASSWORD` | Gmail 应用专用密码（16位） |
| `TO_EMAIL` | 接收要闻的邮箱 |

3. Actions 页面手动触发 "Run workflow" 测试，或等待每天 0:00 UTC 自动运行

### Gmail 应用密码获取

Google 账号 → 安全性 → 两步验证 → 应用专用密码 → 选择"邮件" + "其他设备" → 生成 16 位密码

## 邮件格式

```
┌──────────────────────────────────────────┐
│  📰 AI 要闻周报                           │
│  2026-05-28 — 2026-06-04  星期四          │
│                                          │
│  ── 📡 AI 新闻 ──                        │
│  ① 标题一                                 │
│  ┃ 200-300字详细摘要... [阅读原文]         │
│                                          │
│  ② 标题二                                 │
│  ┃ ...                                   │
│                                          │
│  ③ 标题三                                 │
│  ┃ ...                                   │
│                                          │
│  ── 𝕏 X 讨论 ──                          │
│  ④ 标题四                                 │
│  ┃ 150-250字摘要，含来源和观点分析...      │
│                                          │
│  ⑤ 标题五                                 │
│  ┃ ...                                   │
│                                          │
│  ⑥ 标题六                                 │
│  ┃ ...                                   │
│                                          │
│  由 AI News Agent 自动生成                │
└──────────────────────────────────────────┘
```

## 去重机制

每次运行通过 GitHub Actions Cache 保存 `news_history.json`（最近 40 条已发送 URL），下次运行时自动过滤重复新闻。Cache 有效期内不会丢失，确保周报间内容不重复。

## 日期过滤

采用两层防线确保新闻时效性（严格 7 天内）：

| 层级 | 机制 | 说明 |
|------|------|------|
| 服务端 | Tavily `topic="news"` + `time_range="week"` | 切换到新闻索引，API 层面精确过滤最近一周 |
| 客户端 | `filter_by_date()` 严格模式 | 丢弃无 `published_date` 的结果，剔除超出范围的结果 |

无发布日期的结果会被直接丢弃，确保不会出现 26 天前的旧闻混入周报。

## 搜索白名单

| 英文来源 | 中文来源 |
|----------|----------|
| arxiv.org | 36kr.com |
| techcrunch.com | jiqizhixin.com |
| theverge.com | qbitai.com |
| venturebeat.com | thepaper.cn |
| arstechnica.com | |
| zdnet.com | |
| nature.com | |
| wired.com | |

## 文件结构

```
├── .github/workflows/daily-news.yml   # GitHub Actions 定时触发 + Cache 去重
├── .env.example                       # 环境变量模板
├── .gitignore
├── requirements.txt                   # tavily-python, openai
├── main.py                            # 核心脚本（搜索 / 去重 / 整理 / 发送）
├── template.py                        # HTML 邮件模板
└── README.md
```
