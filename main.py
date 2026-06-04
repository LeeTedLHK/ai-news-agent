import os
import json
import logging
from datetime import datetime, timedelta

from tavily import TavilyClient
from openai import OpenAI

from template import render_html

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EN_INCLUDE_DOMAINS = [
    "arxiv.org", "techcrunch.com", "theverge.com", "venturebeat.com",
    "arstechnica.com", "zdnet.com", "nature.com", "wired.com",
]
CN_INCLUDE_DOMAINS = [
    "36kr.com", "jiqizhixin.com", "qbitai.com", "thepaper.cn",
]

HISTORY_FILE = "news_history.json"
MAX_HISTORY_URLS = 40


def load_env():
    keys = ["TAVILY_API_KEY", "DEEPSEEK_API_KEY", "SMTP_USER", "SMTP_PASSWORD", "TO_EMAIL"]
    config = {}
    missing = []
    for k in keys:
        v = os.environ.get(k, "").strip()
        if not v:
            missing.append(k)
        config[k] = v
    if missing:
        raise ValueError(f"以下环境变量未设置: {', '.join(missing)}")
    return config


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("sent_urls", []))
        except Exception as e:
            logger.warning(f"加载历史记录失败: {e}")
    return set()


def save_history(sent_urls):
    urls = list(sent_urls)[-MAX_HISTORY_URLS:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"sent_urls": urls, "last_updated": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)


def dedup_results(results, sent_urls):
    fresh = [r for r in results if r.get("url", "") not in sent_urls]
    logger.info(f"URL去重: {len(results)} → {len(fresh)} 条")
    return fresh


def mark_as_sent(news_items, sent_urls):
    for item in news_items:
        url = item.get("url", "")
        if url:
            sent_urls.add(url)


def filter_by_date(results, cutoff_date):
    if not results:
        return []
    filtered = []
    skipped = 0
    for r in results:
        pub = r.get("published_date", "")
        if pub and pub < cutoff_date:
            skipped += 1
            continue
        filtered.append(r)
    if skipped:
        logger.info(f"时间过滤(发布日期 <= {cutoff_date}): 剔除 {skipped} 条")
    return filtered


def get_week_range():
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    week_start = week_ago.strftime("%Y-%m-%d")
    week_end = today.strftime("%Y-%m-%d")
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday_cn = weekdays[today.weekday()]
    range_cn = f"{week_ago.year}年{week_ago.month}月{week_ago.day}日 — {today.year}年{today.month}月{today.day}日"
    return week_start, week_end, weekday_cn, range_cn


def search_news(api_key, query, include_domains, max_results=10, days=7):
    client = TavilyClient(api_key=api_key)
    try:
        result = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=include_domains,
            days=days,
        )
        return result.get("results", [])
    except Exception as e:
        logger.warning(f"Tavily 搜索失败 [{query[:40]}...]: {e}")
        return []


def organize_news(api_key, results, date_range):
    if not results:
        return None

    snippets = []
    for i, r in enumerate(results):
        title = r.get("title", "无标题")
        content = r.get("content", "")[:500]
        url = r.get("url", "")
        snippets.append(
            f"[{i + 1}] 标题: {title}\n    摘要: {content}\n    链接: {url}"
        )

    search_text = "\n\n".join(snippets)

    system_prompt = (
        "你是一名专业的AI新闻编辑。请根据以下搜索结果，整理出近一周AI领域最重要的5条要闻。\n\n"
        "要求：\n"
        "1. 过滤营销软文、低质重复内容，只保留有实质信息的新闻\n"
        "2. 英文内容必须翻译为中文，标题和摘要都用中文输出\n"
        "3. 按重要性排序，严格共5条，挑选最有价值、最具影响力的新闻\n"
        "4. 每条摘要200-300字，需包含：新闻背景、核心内容、行业影响分析\n"
        "5. url必须保留原文链接，不可编造\n\n"
        "以JSON格式输出，严格遵循以下结构，不要输出任何额外内容：\n"
        '{"news":[{"title":"中文标题","summary":"200-300字的详细中文摘要，涵盖新闻背景、核心内容及行业影响分析","url":"原文链接","source":"来源"},...共5条]}'
    )

    user_prompt = f"请整理最近一周({date_range})的AI要闻，挑选最重要的5条：\n\n{search_text}"

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        logger.info(f"DeepSeek 输出长度: {len(content)} 字符")
        return json.loads(content)
    except Exception as e:
        logger.error(f"DeepSeek 整理失败: {e}")
        return None


def send_email(smtp_user, smtp_password, to_email, html, date_str):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AI 要闻周报 | {date_str}"
    msg["From"] = smtp_user
    msg["To"] = to_email

    plain = f"AI 要闻周报 | {date_str}\n\n请使用支持 HTML 的邮件客户端查看。"
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        logger.info(f"邮件已发送至 {to_email}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False


def main():
    logger.info("=== AI News Agent 启动 ===")

    config = load_env()
    logger.info("环境变量加载成功")

    week_start, week_end, weekday, date_range = get_week_range()
    logger.info(f"时间范围: {week_start} — {week_end} {weekday}")

    sent_urls = load_history()
    logger.info(f"历史已发送URL: {len(sent_urls)} 条")

    en_query = f"latest AI artificial intelligence news breakthroughs {week_start} {week_end}"
    cn_query = f"人工智能 重大新闻 突破 {date_range}"
    logger.info(f"EN查询: {en_query}")
    logger.info(f"CN查询: {cn_query}")

    en_results = search_news(config["TAVILY_API_KEY"], en_query, EN_INCLUDE_DOMAINS)
    cn_results = search_news(config["TAVILY_API_KEY"], cn_query, CN_INCLUDE_DOMAINS)

    all_results = en_results + cn_results
    logger.info(f"搜索完成: 英文 {len(en_results)} 条 + 中文 {len(cn_results)} 条 = 合计 {len(all_results)} 条")

    all_results = dedup_results(all_results, sent_urls)
    all_results = filter_by_date(all_results, week_start)

    if not all_results:
        logger.error("过滤后无可用结果，终止流程")
        return

    logger.info("DeepSeek 整理中...")
    organized = organize_news(config["DEEPSEEK_API_KEY"], all_results, date_range)

    if not organized:
        logger.error("DeepSeek 整理失败，终止发送")
        return

    news_items = organized.get("news", [])
    mark_as_sent(news_items, sent_urls)
    save_history(sent_urls)
    logger.info(f"历史URL更新: {len(sent_urls)} 条")

    html = render_html(news_items, week_start, week_end, weekday)

    logger.info("发送邮件...")
    send_email(
        config["SMTP_USER"],
        config["SMTP_PASSWORD"],
        config["TO_EMAIL"],
        html,
        week_end,
    )

    logger.info("=== AI News Agent 完成 ===")


if __name__ == "__main__":
    main()
