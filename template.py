from html import escape as _esc


def render_html(news_list, week_start, week_end, weekday):
    date_header = f"{week_start} — {week_end}  {weekday}"
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ margin: 0; padding: 0; background: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; }}
  .container {{ max-width: 640px; margin: 0 auto; padding: 20px; }}
  .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 32px 24px; border-radius: 12px 12px 0 0; text-align: center; }}
  .header h1 {{ color: #fff; font-size: 22px; margin: 0 0 8px 0; }}
  .header .date {{ color: rgba(255,255,255,0.85); font-size: 14px; }}
  .body {{ background: #fff; padding: 24px; border-radius: 0 0 12px 12px; }}
  .card {{ background: #f8f9fa; border-radius: 10px; padding: 20px 20px 16px 20px; margin-bottom: 16px; position: relative; }}
  .card:last-child {{ margin-bottom: 0; }}
  .card .badge {{ display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 50%; background: #667eea; color: #fff; font-size: 14px; font-weight: 700; margin-right: 10px; vertical-align: middle; }}
  .card .title {{ display: inline; font-size: 16px; font-weight: 700; color: #1a1a2e; line-height: 1.6; }}
  .card .summary {{ font-size: 14px; color: #444; margin: 12px 0 10px 0; line-height: 1.75; }}
  .card .meta {{ font-size: 12px; color: #999; }}
  .card .meta a {{ color: #667eea; text-decoration: none; }}
  .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #e8eaed; text-align: center; }}
  .footer p {{ font-size: 11px; color: #aaa; margin: 0; }}
  @media (max-width: 480px) {{
    .container {{ padding: 10px; }}
    .header {{ padding: 24px 16px; }}
    .body {{ padding: 16px; }}
    .card {{ padding: 16px 16px 14px 16px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📰 AI 要闻周报</h1>
    <div class="date">{_esc(date_header)}</div>
  </div>
  <div class="body">
"""
    for i, item in enumerate(news_list, 1):
        t = _esc(str(item.get("title", "")))
        s = _esc(str(item.get("summary", "")))
        u = _esc(str(item.get("url", "#")))
        src = _esc(str(item.get("source", "")))

        html += f"""    <div class="card">
      <span class="badge">{i}</span><span class="title">{t}</span>
      <p class="summary">{s}</p>
      <p class="meta">来源: {src} · <a href="{u}" target="_blank">阅读原文 →</a></p>
    </div>
"""

    html += """    <div class="footer">
      <p>由 AI News Agent 自动生成 · 来源: Tavily Search & X · 整理: DeepSeek</p>
    </div>
  </div>
</div>
</body>
</html>"""
    return html
