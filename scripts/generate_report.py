#!/usr/bin/env python3
"""Generate a weekly AI cowork report and update this static archive site."""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import html
import json
import os
import re
import sys
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "sources.json"
FRAMEWORK = ROOT / "config" / "evaluation_framework.json"
REPORTS = ROOT / "reports"
REPORTS_JSON = ROOT / "reports.json"
INDEX = ROOT / "index.html"
GENERATED = ROOT / ".generated"


REPORT_STYLE = """
:root{--ink:#1d2f42;--muted:#667085;--gold:#b77900;--gold2:#f4b400;--bg:#fffaf0;--card:#ffffff;--line:#ead8a8;--soft:#fff4ce;--blue:#0b6f9f;--deep:#06456b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;line-height:1.78}a{color:#0563d8;text-decoration:none}a:hover{text-decoration:underline}
.hero{background:linear-gradient(135deg,#6f4a00 0%,#b77900 55%,#e2a90c 100%);color:#fff;padding:44px 28px 36px;position:relative;overflow:hidden}.hero:after{content:"";position:absolute;right:-80px;top:-110px;width:280px;height:280px;border-radius:50%;background:rgba(255,255,255,.13)}
.wrap{max-width:980px;margin:0 auto}.kicker{display:inline-block;padding:4px 14px;border:1px solid rgba(255,255,255,.38);border-radius:999px;font-size:13px;letter-spacing:.08em}.hero h1{margin:20px 0 6px;font-size:42px;line-height:1.18;letter-spacing:0}.meta{opacity:.9;font-size:16px}.nav{background:#fff7dc;border-bottom:1px solid var(--line);padding:20px 28px}.chips{display:flex;gap:12px;flex-wrap:wrap}.chip{background:#fff;border:1px solid #eed58a;border-radius:999px;padding:8px 14px;color:#7a4f00;font-weight:650}
main{padding:34px 28px 64px}.section-title{font-size:25px;margin:28px 0 18px;display:flex;align-items:center;gap:12px}.section-title:before{content:"";width:5px;height:28px;border-radius:4px;background:var(--gold2)}
.lead{background:#fff8df;border:1px solid #eed58a;border-left:5px solid var(--gold2);border-radius:8px;padding:24px 28px;margin-bottom:28px}.lead p{margin:0 0 14px}.lead p:last-child{margin:0}.tag{display:inline-block;background:#0b78aa;color:#fff;border-radius:7px;padding:3px 10px;font-size:13px;font-weight:700;margin-bottom:10px}.card{background:var(--card);border:1px solid #e6edf5;border-radius:8px;padding:26px 28px;margin:22px 0;box-shadow:0 1px 0 rgba(16,24,40,.03)}.card h2{font-size:24px;line-height:1.35;margin:4px 0 6px;color:var(--deep)}.source{font-size:15px;color:#667085;margin-bottom:18px}.card p{font-size:18px;margin:14px 0}.mini{font-weight:800;color:#075985;margin-top:22px;padding-left:12px;border-left:4px solid #65b9e8}.lens{background:#f8fbff;border:1px solid #d9e8f7;border-radius:8px;padding:16px 18px;margin:16px 0}.lens b{color:#075985}.take{background:#fff3bf;border-left:4px solid #f0a400;border-radius:0 8px 8px 0;padding:16px 18px;margin-top:20px;color:#6a3e00;font-size:17px}.take b{color:#b45309}.footer{color:#6b7280;font-size:14px;margin-top:38px;border-top:1px solid #ead8a8;padding-top:18px}
@media(max-width:680px){.hero h1{font-size:31px}.card,.lead{padding:20px}.card h2{font-size:21px}.card p{font-size:16px}.chips{gap:8px}.chip{font-size:14px}}
""".strip()


INDEX_STYLE = """
:root{--ink:#1d2f42;--muted:#667085;--gold:#b77900;--gold2:#f4b400;--bg:#fffaf0;--card:#fff;--line:#ead8a8;--soft:#fff7dc;--blue:#073f5f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif}a{text-decoration:none;color:inherit}.hero{background:linear-gradient(135deg,#654300,#b77900 55%,#e5ab12);color:#fff;padding:48px 28px}.wrap{max-width:980px;margin:0 auto}.eyebrow{display:inline-block;border:1px solid rgba(255,255,255,.38);border-radius:999px;padding:4px 14px;font-size:13px;letter-spacing:.08em}.hero h1{font-size:42px;line-height:1.16;margin:18px 0 8px;letter-spacing:0}.hero p{margin:0;color:rgba(255,255,255,.9);font-size:16px}main{padding:30px 28px 72px}.panel{background:#fff8df;border:1px solid #ecd28a;border-left:5px solid var(--gold2);border-radius:8px;padding:20px 22px;margin-bottom:24px;line-height:1.7}.panel b{color:#6f4a00}.toolbar{display:flex;gap:12px;align-items:center;justify-content:space-between;margin:24px 0 14px}.toolbar h2{margin:0;font-size:24px}.count{color:#7a4f00;background:var(--soft);border:1px solid var(--line);border-radius:999px;padding:5px 12px;font-weight:800}.list{display:grid;gap:14px}.row{display:grid;grid-template-columns:56px 1fr auto;gap:16px;align-items:center;background:var(--card);border:1px solid #e7edf4;border-radius:8px;padding:16px 18px;box-shadow:0 1px 0 rgba(16,24,40,.03)}.row:hover{border-color:#d6a31e;box-shadow:0 4px 18px rgba(115,79,0,.08)}.icon{width:46px;height:46px;border-radius:8px;background:#f4df9b;color:#7a4f00;display:grid;place-items:center;font-weight:900}.title{font-size:19px;font-weight:850;color:var(--blue);line-height:1.35}.meta{font-size:14px;color:#7a6a4a;margin-top:2px}.summary{font-size:14px;color:var(--muted);margin-top:5px;line-height:1.55}.open{color:#9a6700;font-weight:850;white-space:nowrap}.footer{margin-top:30px;color:#777;font-size:14px}@media(max-width:720px){.hero h1{font-size:32px}.row{grid-template-columns:42px 1fr}.icon{width:38px;height:38px}.open{grid-column:2}.summary{display:none}}
""".strip()


def e(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def period(config: dict, parsed: argparse.Namespace) -> tuple[dt.date, dt.date]:
    if parsed.start and parsed.end:
        return dt.date.fromisoformat(parsed.start), dt.date.fromisoformat(parsed.end)
    today = dt.datetime.now(ZoneInfo(config.get("timezone", "Asia/Shanghai"))).date()
    monday = today - dt.timedelta(days=today.weekday())
    return monday - dt.timedelta(days=7), monday - dt.timedelta(days=1)


def parse_source_date(value: str) -> dt.date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        pass
    try:
        return email.utils.parsedate_to_datetime(value).date()
    except Exception:
        return None


def fetch_bing_news(query: str, start: dt.date, end: dt.date, limit: int = 50) -> list[dict]:
    # Keep the search broad, then apply our own strict date gate below.
    params = urllib.parse.urlencode({"q": query, "format": "rss", "setlang": "zh-CN"})
    request = urllib.request.Request(
        f"https://www.bing.com/news/search?{params}",
        headers={"User-Agent": "Mozilla/5.0 cowork-report-bot"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        root = ET.fromstring(response.read())
    items: list[dict] = []
    for item in root.findall("./channel/item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = re.sub(r"<[^>]+>", "", item.findtext("description") or "").strip()
        raw_date = item.findtext("pubDate") or ""
        published_date = parse_source_date(raw_date)
        if not published_date or published_date < start or published_date > end:
            continue
        source = ""
        for child in item:
            if child.tag.lower().endswith("source"):
                source = (child.text or "").strip()
        if title and link:
            items.append({
                "title": title,
                "url": link,
                "source": source or urllib.parse.urlparse(link).netloc,
                "published": published_date.isoformat(),
                "summary": desc,
            })
    return items


def collect_sources(config: dict, start: dt.date, end: dt.date) -> list[dict]:
    seen: set[str] = set()
    sources: list[dict] = []
    for query in config["queries"]:
        try:
            for item in fetch_bing_news(query["query"], start, end):
                key = re.sub(r"\W+", "", (item["title"] + item["url"]).lower())
                if key in seen:
                    continue
                seen.add(key)
                item["query_group"] = query["name"]
                sources.append(item)
        except Exception as exc:
            print(f"warning: failed to fetch {query['name']}: {exc}", file=sys.stderr)
    return sources[:45]


def compact_text(value: str, max_chars: int = 1200) -> str:
    value = re.sub(r"<script[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style[\s\S]*?</style>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:max_chars]


def fetch_official_reference(source: dict) -> dict:
    url = source["url"]
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 cowork-report-bot"})
    with urllib.request.urlopen(request, timeout=18) as response:
        raw = response.read(900_000)
        charset = response.headers.get_content_charset() or "utf-8"
    text = raw.decode(charset, errors="replace")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    desc_match = re.search(
        r"<meta[^>]+(?:name|property)=[\"'](?:description|og:description)[\"'][^>]+content=[\"'](.*?)[\"']",
        text,
        flags=re.I | re.S,
    )
    title = compact_text(title_match.group(1), 180) if title_match else source.get("name", "")
    summary = compact_text(desc_match.group(1), 500) if desc_match else compact_text(text, 700)
    return {
        "name": source.get("name") or urllib.parse.urlparse(url).netloc,
        "url": url,
        "title": title,
        "summary": summary,
        "notes": source.get("notes", ""),
        "reference_only": True,
    }


def collect_official_references(config: dict) -> list[dict]:
    references: list[dict] = []
    for source in config.get("official_sources", [])[:16]:
        try:
            references.append(fetch_official_reference(source))
        except Exception as exc:
            references.append({
                "name": source.get("name"),
                "url": source.get("url"),
                "notes": source.get("notes", ""),
                "fetch_error": str(exc),
                "reference_only": True,
            })
    return references


def extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    left, right = text.find("{"), text.rfind("}")
    if left < 0 or right < 0:
        raise ValueError(f"No JSON object found: {text[:200]}")
    return text[left : right + 1]


def fixture_report(sources: list[dict], start: dt.date, end: dt.date) -> dict:
    picked = sources[:5] or [{"title": "AI cowork 流程测试", "url": "https://example.com", "source": "fixture", "published": end.isoformat(), "summary": "用于验证流程的测试来源。"}]
    items = []
    for source in picked:
        items.append(
            {
                "tag": source.get("query_group", "AI cowork"),
                "title": source["title"],
                "date": source.get("published") or end.isoformat(),
                "source": source.get("source") or "source",
                "url": source["url"],
                "fact": source.get("summary") or "该动态显示 AI 产品正在进入更具体的工作流场景。",
                "analysis_heading": "从功能发布到工作流占位",
                "analysis": "这类动态的重点不在于单点功能，而在于 AI 是否开始读取上下文、参与判断并推动下一步动作。对 cowork 产品而言，入口、数据和动作权限会共同决定产品能否长期留在用户流程里。",
                "implication": "后续 buddy 产品需要把数据连接、权限控制、执行边界和结果追溯放在同一套体验里，而不是只提供一个聊天窗口。",
                "commentary": "如果产品只强调生成能力，很快会被同质化；真正值得跟踪的是它是否绑定高频入口、是否拥有独特上下文、是否能在风险可控的情况下完成动作闭环。",
            }
        )
    return {
        "title": f"AI cowork 产品周报｜{start.isoformat()} 至 {end.isoformat()}",
        "date": end.isoformat(),
        "period": f"{start.isoformat()} 至 {end.isoformat()}",
        "summary": "本期关注 AI cowork 从助手功能走向真实工作流的产品竞争。",
        "lead": [
            "本期关注 AI cowork / buddy 产品从单点助手走向持续工作流的变化，重点看入口、上下文、跨应用执行和企业治理能力。",
            "公开信息会被整理为面向读者的产品周报：先讲清发生了什么，再判断它对 cowork 产品形态和竞争格局意味着什么。",
            "报告重点放在外部 AI cowork、企业 Agent、研发 Agent 和办公协作 Agent 的产品变化上，不把任何单一内部参照产品作为主线。",
        ],
        "items": items,
        "signals": [
            "cowork 产品竞争正在从模型能力转向工作流入口。",
            "能否接入持续上下文会决定助手是否有长期价值。",
            "可执行 Agent 必须具备预览、确认和审计机制。",
            "企业采购会关注模型选择权和数据治理能力。",
            "国内 buddy 产品应重点观察入口绑定和跨应用执行能力。",
        ],
    }


def call_deepseek(config: dict, sources: list[dict], official_references: list[dict], start: dt.date, end: dt.date, dry_run: bool) -> dict:
    if dry_run:
        return fixture_report(sources, start, end)
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GitHub Secret: DEEPSEEK_API_KEY")
    framework = json.loads(FRAMEWORK.read_text(encoding="utf-8")) if FRAMEWORK.exists() else {}
    official_references = official_references or []
    prompt = f"""
你是给公司同事阅读的 AI cowork / buddy 产品周报作者。你的任务不是复述新闻，而是把上一整周 AI cowork / AI buddy / AI 同事 / Agentic workspace 类产品的新动向，整理成可对外阅读的研究型周报。

观察周期：{start.isoformat()} 至 {end.isoformat()}

硬性时间范围：
- 只允许把观察周期内发布、更新或被权威报道的新信息写成“本周动向”。如果生成日是周一，观察周期就是上一个周一 00:00 到周日 23:59。
- 旧官网、旧评测、百科、论坛讨论、历史实测和长期背景只能用来理解产品，不得写成“本周发生”。
- 如果某条信息无法确认发布时间在观察周期内，或只有旧内容支撑，就不要进入产品动向卡片。

追踪范围：
- 重点是国内外主要 cowork / buddy / AI 同事 / Agentic workspace / 企业 Agent / 办公协作 Agent / 研发 Agent / 数据分析与金融工作流 Agent。太小、无公开可信来源、与“AI 持续帮人完成工作”无关的产品不用凑数。
- 必须主动检查代表性产品池：字节 Trae Work / Trae IDE / 飞书与豆包相关 AI 同事，阿里 Qoder / 通义 / 钉钉 AI，Kimi Work / Kimi Code / Kimi Claw / Moonshot，Arkclaw / OpenClaw / Manus，以及 OpenAI、Anthropic、Google、Microsoft、Cursor、Slack、Notion、Salesforce、Perplexity 等。
- 权重由“这一周谁有值得读者知道的新消息”决定，不按固定公司配额。没有可信新动向就不写，也不要在正文解释为什么没写。

来源规则：
- 优先使用官方公告、官网新闻、产品页、changelog、帮助文档，其次使用权威媒体、研究论文、融资新闻稿。
- official_reference_sources 只用于核对产品定位、能力边界和术语；除非它自身有观察周期内明确日期，否则不能单独成为“本周新动向”。
- 不要只凭一篇报道就武断下结论。单一媒体源只能写成弱信号或观察项；要上升到产品判断，尽量结合官方页面、另一家权威媒体、研究/历史上下文或产品能力证据。

分析方法：
- 原调研报告抽象出的 analysis_framework 只作为后台判断框架，不要在正文写“调研报告”“实测维度”“修订版”“降重”等过程话。
- 每条卡片先讲清事实，再回答它落在哪些 cowork 能力维度：入口形态、跨应用执行、企业知识/文件/IM/邮件接入、异步调度、来源溯源、权限审计、任务复用、成本与商业化、稳定交付。
- 报告要像正式公众号文章/研究周报：清晰、具体、有判断。不要泛泛罗列模型新闻；只有当模型变化影响 Agent 工作流成本、能力边界或产品入口时才写。

写作要求：
1. 产出是正式对外可读的研究型周报，不要出现“草稿、修订版、降重、内部要求、按用户要求修改、WorkBuddy 自身改进”等过程话；也不要在正文显式解释“本期只看某个时间段、官网只用于核对、单一传闻不写”等筛选方法，时间范围和来源规则只在后台遵守。
2. 每张产品卡必须先讲清事实，再给 2-3 个分析小标题，至少包含“证据拼图/多源验证”“能力维度影响”“对 cowork 产品的启发”中的两个，最后给一段有判断力的“简评”。
3. 不设固定少量卡片上限：如果本周有多条值得关注且来源可靠的新动向，可以写到 8-10 张，并覆盖不同公司和能力维度；如果没有更多高质量信息，宁可保持 4-6 张，不要凑数。
4. 来源必须可点击，不要编造链接、日期或来源。
5. 只输出 JSON，不要 Markdown。

JSON schema:
{{
  "title": "AI cowork 产品周报｜YYYY-MM-DD 至 YYYY-MM-DD",
  "date": "{end.isoformat()}",
  "period": "YYYY-MM-DD 至 YYYY-MM-DD",
  "summary": "一句话说明本期最重要判断",
  "lead": ["导读段落1", "导读段落2", "导读段落3"],
  "items": [
    {{
      "tag": "分类标签",
      "title": "产品动向标题",
      "date": "YYYY-MM-DD",
      "source": "主来源名称",
      "url": "主来源链接",
      "source_links": [{{"name": "来源名称", "url": "来源链接"}}],
      "fact": "150-240字，具体说明发生了什么、涉及什么产品或能力、来源怎么说",
      "detail_sections": [
        {{"heading": "分析小标题1", "body": "90-180字，讲清产品意义"}},
        {{"heading": "分析小标题2", "body": "90-180字，讲清对 cowork/buddy 的影响"}}
      ],
      "commentary": "180-300字，明确给出判断、可借鉴点和风险限制"
    }}
  ],
  "signals": ["关键判断1", "关键判断2", "关键判断3", "关键判断4", "关键判断5"]
}}

analysis_framework_from_prior_cowork_research:
{json.dumps(framework, ensure_ascii=False, indent=2)}

official_reference_sources_for_positioning_only:
{json.dumps(official_references, ensure_ascii=False, indent=2)}

sources_already_strictly_filtered_to_period:
{json.dumps(sources, ensure_ascii=False, indent=2)}
""".strip()
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是严谨的中文科技产品分析师，擅长从新闻中提炼产品竞争信号。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.25,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.loads(response.read().decode("utf-8"))
    return json.loads(extract_json(result["choices"][0]["message"]["content"]))


def p(values: list[str]) -> str:
    return "".join(f"<p>{e(value)}</p>" for value in values if value)


def render_report(report: dict) -> str:
    cards = []
    for item in report.get("items", []):
        detail_sections = item.get("detail_sections") or item.get("sections") or []
        section_html = ""
        if isinstance(detail_sections, list):
            for section in detail_sections[:3]:
                if isinstance(section, dict):
                    heading = section.get("heading") or section.get("title") or "关键观察"
                    body = section.get("body") or section.get("analysis") or ""
                elif isinstance(section, (list, tuple)) and len(section) >= 2:
                    heading, body = section[0], section[1]
                else:
                    continue
                section_html += f'<div class="mini">{e(heading)}</div><p>{e(body)}</p>'
        if not section_html:
            section_html = f'<div class="mini">{e(item.get("analysis_heading"))}</div><p>{e(item.get("analysis"))}</p>'
            if item.get("implication"):
                section_html += f'<div class="mini">对 cowork 产品的启发</div><p>{e(item.get("implication"))}</p>'
        links = item.get("source_links") or []
        if isinstance(links, list) and links:
            source_html = " / ".join(
                f'<a href="{e(link.get("url"))}" target="_blank" rel="noopener">{e(link.get("name") or "原文")}</a>'
                for link in links
                if isinstance(link, dict) and link.get("url")
            )
        else:
            source_html = f'<a href="{e(item.get("url"))}" target="_blank" rel="noopener">点击查看原文 →</a>'
        cards.append(
            f"""<article class="card"><span class="tag">{e(item.get("tag"))}</span><h2>{e(item.get("title"))}</h2><div class="source">{e(item.get("date"))} · {e(item.get("source"))} · {source_html}</div><p>{e(item.get("fact"))}</p>{section_html}<div class="take"><b>简评：</b>{e(item.get("commentary"))}</div></article>"""
        )
    signals = "".join(f"<p><b>{idx}. </b>{e(signal)}</p>" for idx, signal in enumerate(report.get("signals", []), start=1))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(report.get("title"))}</title>
<style>{REPORT_STYLE}</style>
</head>
<body><div style="position:sticky;top:0;z-index:9999;background:#fff7dc;border-bottom:1px solid #ead8a8;padding:10px 18px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"><a href="../index.html" style="color:#7a4f00;font-weight:800;text-decoration:none">← 返回全部周报</a><span style="margin-left:14px;color:#667085;font-size:14px">{e(report.get("title"))}</span></div>
<header class="hero"><div class="wrap"><span class="kicker">AI COWORK TRACKER</span><h1>{e(report.get("title"))}</h1><div class="meta">{e(report.get("period"))} · 正式发布</div></div></header>
<nav class="nav"><div class="wrap"><div class="chips"><a class="chip" href="#read">本期导读</a><a class="chip" href="#moves">产品动向</a><a class="chip" href="#signals">关键判断</a></div></div></nav>
<main class="wrap">
<section id="read"><h2 class="section-title">本期导读</h2><div class="lead">{p(report.get("lead", []))}</div></section>
<section id="moves"><h2 class="section-title">产品动向</h2>{''.join(cards)}</section>
<section id="signals"><h2 class="section-title">关键判断</h2><div class="lead">{signals}</div></section>
</main>
</body>
</html>
"""


def reports_list() -> list[dict]:
    if not REPORTS_JSON.exists():
        return []
    return json.loads(REPORTS_JSON.read_text(encoding="utf-8-sig"))


def render_index(reports: list[dict]) -> str:
    latest = reports[0] if reports else None
    latest_html = f"""<b>当前最新：</b><a href="{e(latest['path'])}">{e(latest['title'])}</a> · {e(latest['date'])}<br>每周确认发布后的报告会自动追加到下方历史列表。""" if latest else "暂无周报。"
    rows = []
    for idx, report in enumerate(reports, start=1):
        rows.append(
            f"""<a class="row" href="{e(report['path'])}"><div class="icon">{idx}</div><div class="info"><div class="title">{e(report['title'])}</div><div class="meta">{e(report.get('type', '自动发布'))} · {e(report['date'])} · {e(report.get('sources', 0))} 个来源</div><div class="summary">{e(report.get('summary', ''))}</div></div><div class="open">打开 →</div></a>"""
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>cowork报告</title>
<style>{INDEX_STYLE}</style>
</head>
<body>
<header class="hero"><div class="wrap"><span class="eyebrow">COWORK REPORT ARCHIVE</span><h1>cowork报告</h1><p>所有已发布周报都会保存在这里，可按期打开、分享和回溯来源。</p></div></header>
<main class="wrap">
<section class="panel">{latest_html}</section>
<div class="toolbar"><h2>全部周报</h2><span class="count">{len(reports)} 期</span></div>
<section class="list">{''.join(rows)}</section>
</main>
</body>
</html>
"""


def write_outputs(report: dict) -> None:
    REPORTS.mkdir(exist_ok=True)
    report_id = report["date"]
    (REPORTS / f"{report_id}.html").write_text(render_report(report), encoding="utf-8")
    reports = [item for item in reports_list() if item.get("id") != report_id]
    reports.insert(
        0,
        {
            "id": report_id,
            "title": report["title"],
            "date": report["date"],
            "path": f"reports/{report_id}.html",
            "sources": len(report.get("items", [])),
            "type": "正式发布",
            "summary": report.get("summary", ""),
        }
    )
    reports.sort(key=lambda item: item["date"], reverse=True)
    REPORTS_JSON.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    INDEX.write_text(render_index(reports), encoding="utf-8")
    GENERATED.mkdir(exist_ok=True)
    (GENERATED / "report_date.txt").write_text(report["date"], encoding="utf-8")
    (GENERATED / "pr_body.md").write_text(
        textwrap.dedent(
            f"""\
            本 PR 是自动生成的 cowork 报告草稿。

            - 观察周期：{report.get('period')}
            - 来源数量：{len(report.get('items', []))}
            - 生成文件：`reports/{report['date']}.html`

            请在 `Files changed` 中阅读本期内容。确认无误后点击 **Merge pull request**，GitHub Pages 会自动更新公开网站。
            """
        ),
        encoding="utf-8",
    )


def main() -> None:
    parsed = args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    start, end = period(config, parsed)
    sources = collect_sources(config, start, end)
    official_references = collect_official_references(config)
    if not sources and not parsed.dry_run:
        raise RuntimeError("No sources collected. Adjust config/sources.json or run again later.")
    report = call_deepseek(config, sources, official_references, start, end, parsed.dry_run)
    write_outputs(report)
    print(f"generated report {report['date']} with {len(report.get('items', []))} items")


if __name__ == "__main__":
    main()
