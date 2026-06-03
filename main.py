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


def get_yesterday():
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday_cn = weekdays[yesterday.weekday()]
    date_cn = f"{yesterday.year}年{yesterday.month}月{yesterday.day}日"
    return date_str, weekday_cn, date_cn


def search_news(api_key, query, include_domains, max_results=5):
    client = TavilyClient(api_key=api_key)
    try:
        result = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=include_domains,
        )
        return result.get("results", [])
    except Exception as e:
        logger.warning(f"Tavily 搜索失败 [{query[:40]}...]: {e}")
        return []


def organize_news(api_key, results, date_str):
    if not results:
        return None

    snippets = []
    for i, r in enumerate(results):
        title = r.get("title", "无标题")
        content = r.get("content", "")[:300]
        url = r.get("url", "")
        snippets.append(
            f"[{i + 1}] 标题: {title}\n    摘要: {content}\n    链接: {url}"
        )

    search_text = "\n\n".join(snippets)

    system_prompt = (
        "你是一名专业的AI新闻编辑。请根据以下搜索结果，整理出昨日AI领域要闻。\n\n"
        "要求：\n"
        "1. 过滤营销软文、低质重复内容，只保留有实质信息的新闻\n"
        "2. 英文内容翻译为中文，标题和摘要都用中文输出\n"
        "3. 按重要性排序，严格共8条\n"
        "4. 分类: 头条(headline)1条 + 重要动态(important)3条 + 研究前沿(research)2条 + 行业观察(industry)2条\n"
        "5. 每条摘要1-2句话，不超过80字\n"
        "6. url必须保留原文链接，不可编造\n\n"
        "以JSON格式输出，严格遵循以下结构，不要输出任何额外内容：\n"
        '{"headline":[{"title":"...","summary":"...","url":"...","source":"..."}],'
        '"important":[{"title":"...","summary":"...","url":"...","source":"..."},...],'
        '"research":[{"title":"...","summary":"...","url":"...","source":"..."},...],'
        '"industry":[{"title":"...","summary":"...","url":"...","source":"..."}]}'
    )

    user_prompt = f"今天是{date_str}。请整理昨日AI新闻：\n\n{search_text}"

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
    msg["Subject"] = f"AI 要闻日报 | {date_str}"
    msg["From"] = smtp_user
    msg["To"] = to_email

    plain = f"AI 要闻日报 | {date_str}\n\n请使用支持 HTML 的邮件客户端查看。"
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

    date_str, weekday, date_cn = get_yesterday()
    logger.info(f"目标日期: {date_str} {weekday}")

    logger.info("开始搜索 AI 新闻...")
    en_query = f"latest AI artificial intelligence news breakthroughs {date_str}"
    cn_query = f"人工智能 最新新闻 突破 {date_cn}"

    en_results = search_news(config["TAVILY_API_KEY"], en_query, EN_INCLUDE_DOMAINS)
    cn_results = search_news(config["TAVILY_API_KEY"], cn_query, CN_INCLUDE_DOMAINS)

    all_results = en_results + cn_results
    logger.info(f"搜索完成: 英文 {len(en_results)} 条 + 中文 {len(cn_results)} 条 = 合计 {len(all_results)} 条")

    if not all_results:
        logger.error("未获取到任何搜索结果，终止流程")
        return

    logger.info("DeepSeek 整理中...")
    organized = organize_news(config["DEEPSEEK_API_KEY"], all_results, date_str)

    if not organized:
        logger.error("DeepSeek 整理失败，终止发送")
        return

    html = render_html(
        organized.get("headline", []),
        organized.get("important", []),
        organized.get("research", []),
        organized.get("industry", []),
        date_str,
        weekday,
    )

    logger.info("发送邮件...")
    send_email(
        config["SMTP_USER"],
        config["SMTP_PASSWORD"],
        config["TO_EMAIL"],
        html,
        date_str,
    )

    logger.info("=== AI News Agent 完成 ===")


if __name__ == "__main__":
    main()
