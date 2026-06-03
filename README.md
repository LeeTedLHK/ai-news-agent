# AI News Agent

每日自动搜索 AI 领域要闻，经 DeepSeek 整理后发送到 Gmail。

## 工作流程

```
每日 UTC 0:00 (北京时间 8:00) GitHub Actions 自动触发
  │
  ├─ 1. Tavily Search API   → 英文 + 中文并行搜索，过滤低质来源
  ├─ 2. DeepSeek Chat       → 去重、翻译、分类整理为 8 条结构化简报
  ├─ 3. HTML 邮件渲染        → 卡片式四段布局（头条 / 重要动态 / 研究前沿 / 行业观察）
  └─ 4. Gmail SMTP 发送      → 推送到指定邮箱
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

## 邮件示例

```
┌──────────────────────────────────────────┐
│  📰 AI 要闻日报 · 2026-06-03 星期三      │
│                                          │
│  🔥 头条                                  │
│  ┃ OpenAI 发布 GPT-5 正式版... [阅读原文]  │
│                                          │
│  📌 重要动态                               │
│  ┃ Meta 开源 Llama 4 ...        [链接]    │
│  ┃ Google DeepMind 新突破 ...    [链接]    │
│  ┃ Anthropic 发布 Claude 4 ...   [链接]    │
│                                          │
│  🔬 研究前沿                               │
│  ┃ Mixture-of-Experts 新架构 ... [链接]    │
│  ┃ 多模态对齐最新进展 ...         [链接]    │
│                                          │
│  💡 行业观察                               │
│  ┃ AI 芯片融资 50 亿美元 ...     [链接]    │
│  ┃ 欧盟 AI 法案正式生效 ...      [链接]    │
│                                          │
│  由 AI News Agent 自动生成                │
└──────────────────────────────────────────┘
```

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
├── .github/workflows/daily-news.yml   # GitHub Actions 定时触发
├── .env.example                       # 环境变量模板
├── .gitignore
├── requirements.txt                   # tavily-python, openai
├── main.py                            # 核心脚本
├── template.py                        # HTML 邮件模板
└── README.md
```
