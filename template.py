from html import escape as _esc


def render_html(headline, important, research, industry, date_str, weekday):
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
  .section {{ margin-bottom: 24px; }}
  .section:last-child {{ margin-bottom: 0; }}
  .section-title {{ font-size: 18px; font-weight: 700; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 2px solid #e8eaed; }}
  .card {{ background: #f8f9fa; border-radius: 8px; padding: 16px; margin-bottom: 12px; border-left: 4px solid #667eea; }}
  .card.headline-card {{ border-left-color: #e8590c; background: #fff9f0; }}
  .card:last-child {{ margin-bottom: 0; }}
  .card .title {{ font-size: 15px; font-weight: 600; color: #1a1a2e; margin: 0 0 6px 0; line-height: 1.5; }}
  .card .summary {{ font-size: 13px; color: #555; margin: 0 0 8px 0; line-height: 1.6; }}
  .card .meta {{ font-size: 11px; color: #999; }}
  .card .meta a {{ color: #667eea; text-decoration: none; }}
  .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #e8eaed; text-align: center; }}
  .footer p {{ font-size: 11px; color: #aaa; margin: 0; }}
  @media (max-width: 480px) {{
    .container {{ padding: 10px; }}
    .header {{ padding: 24px 16px; }}
    .body {{ padding: 16px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📰 AI 要闻日报</h1>
    <div class="date">{_esc(date_str)} {_esc(weekday)}</div>
  </div>
  <div class="body">
"""
    if headline:
        html += _section("🔥 头条", headline, is_headline=True)
    if important:
        html += _section("📌 重要动态", important)
    if research:
        html += _section("🔬 研究前沿", research)
    if industry:
        html += _section("💡 行业观察", industry)

    html += """    <div class="footer">
      <p>由 AI News Agent 自动生成 · 新闻来源: Tavily Search · 整理: DeepSeek</p>
    </div>
  </div>
</div>
</body>
</html>"""
    return html


def _section(title, items, is_headline=False):
    css_class = "card headline-card" if is_headline else "card"
    out = f'    <div class="section">\n      <div class="section-title">{_esc(title)}</div>\n'
    for item in items:
        t = _esc(str(item.get("title", "")))
        s = _esc(str(item.get("summary", "")))
        u = _esc(str(item.get("url", "#")))
        src = _esc(str(item.get("source", "")))
        out += f'      <div class="{css_class}">\n'
        out += f'        <p class="title">{t}</p>\n'
        out += f'        <p class="summary">{s}</p>\n'
        out += f'        <p class="meta">来源: {src} · <a href="{u}" target="_blank">阅读原文 →</a></p>\n'
        out += '      </div>\n'
    out += '    </div>\n'
    return out
