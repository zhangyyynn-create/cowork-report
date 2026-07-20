#!/usr/bin/env python3
"""Send the published cowork report to a distribution mailbox/list."""

from __future__ import annotations

import argparse
import json
import os
import re
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from pathlib import Path


DEFAULT_ARCHIVE_URL = "https://zhangyyynn-create.github.io/cowork-report/"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-file", required=True)
    parser.add_argument("--report-date", required=True)
    parser.add_argument("--report-url", required=True)
    parser.add_argument("--archive-url", default=DEFAULT_ARCHIVE_URL)
    parser.add_argument("--reports-json", default="reports.json")
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required secret/environment variable: {name}")
    return value


def optional_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def read_report_meta(args: argparse.Namespace, report_html: str) -> dict[str, str]:
    meta = {"title": f"AI cowork 产品周报｜{args.report_date}", "summary": "本期 AI cowork 产品周报已发布。"}
    reports_path = Path(args.reports_json)
    if reports_path.exists():
        reports = json.loads(reports_path.read_text(encoding="utf-8-sig"))
        for item in reports:
            if item.get("id") == args.report_date or item.get("date") == args.report_date:
                meta["title"] = item.get("title") or meta["title"]
                meta["summary"] = item.get("summary") or meta["summary"]
                break
    title_match = re.search(r"<title>(.*?)</title>", report_html, flags=re.S | re.I)
    if title_match:
        meta["title"] = re.sub(r"\s+", " ", title_match.group(1)).strip()
    return meta


def inline_report_body(report_html: str) -> str:
    match = re.search(r"<body[^>]*>(.*)</body>", report_html, re.S | re.I)
    body = match.group(1) if match else report_html
    body = re.sub(r"<script[\s\S]*?</script>", "", body, flags=re.I)
    body = re.sub(r"<style[\s\S]*?</style>", "", body, flags=re.I)
    body = re.sub(r"<nav[\s\S]*?</nav>", "", body, flags=re.I)
    body = re.sub(r'<div style="position:sticky[\s\S]*?</div>\s*', "", body, flags=re.I)
    body = re.sub(r"<header[^>]*>", '<div style="background:#b77900;color:#fff;border-radius:8px;padding:22px 24px;margin-bottom:16px">', body, flags=re.I)
    body = re.sub(r"</header>", "</div>", body, flags=re.I)
    body = re.sub(r'<main[^>]*>', '<div style="max-width:720px;margin:0 auto">', body, flags=re.I)
    body = body.replace("</main>", "</div>")

    replacements = {
        'class="wrap"': 'style="max-width:720px;margin:0 auto"',
        'class="kicker"': 'style="font-size:12px;letter-spacing:.08em;opacity:.88"',
        'class="meta"': 'style="opacity:.9;font-size:14px"',
        'class="section-title"': 'style="font-size:22px;margin:24px 0 12px;color:#06456b"',
        'class="lead"': 'style="background:#fff8df;border:1px solid #ead8a8;border-left:4px solid #f4b400;border-radius:8px;padding:18px 20px;margin:0 0 18px"',
        'class="card"': 'style="background:#fff;border:1px solid #e6edf5;border-radius:8px;padding:20px 22px;margin:18px 0"',
        'class="tag"': 'style="display:inline-block;background:#0b78aa;color:#fff;border-radius:6px;padding:2px 8px;font-size:12px;font-weight:700"',
        'class="source"': 'style="font-size:14px;color:#667085;margin:6px 0 12px"',
        'class="mini"': 'style="font-weight:800;color:#075985;margin-top:16px;border-left:4px solid #65b9e8;padding-left:10px"',
        'class="take"': 'style="background:#fff3bf;border-left:4px solid #f0a400;border-radius:0 8px 8px 0;padding:14px 16px;margin-top:16px;color:#6a3e00"',
    }
    for old, new in replacements.items():
        body = body.replace(old, new)
    return body


def send_smtp(message: EmailMessage, host: str, port: int, user: str, password: str) -> None:
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
            smtp.login(user, password)
            smtp.send_message(message)
        return
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(message)


def main() -> None:
    args = parse_args()
    report_html = Path(args.report_file).read_text(encoding="utf-8")
    meta = read_report_meta(args, report_html)

    smtp_host = os.environ.get("SMTP_HOST", "smtp.qq.com").strip() or "smtp.qq.com"
    smtp_port = int(os.environ.get("SMTP_PORT", "465").strip() or "465")
    smtp_user = require_env("SMTP_USER")
    smtp_password = require_env("SMTP_PASSWORD")
    mail_to = optional_env("PUBLISH_MAIL_TO", "MAIL_TO")
    if not mail_to:
        raise RuntimeError("Missing PUBLISH_MAIL_TO or MAIL_TO. Set a GitHub Secret for the published report recipients.")
    mail_cc = optional_env("PUBLISH_MAIL_CC")
    mail_bcc = optional_env("PUBLISH_MAIL_BCC")

    subject = f"【AI cowork 产品周报】{args.report_date} 已发布"
    text = f"""{meta['title']} 已发布。

本期摘要：
{meta['summary']}

查看当期：
{args.report_url}

查看历史全部周报：
{args.archive_url}
"""
    body = inline_report_body(report_html)
    html = f"""\
<!doctype html>
<html lang="zh-CN">
<body style="margin:0;background:#fffaf0;color:#1d2f42;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',Arial,sans-serif;line-height:1.7">
  <div style="max-width:760px;margin:0 auto;padding:28px">
    <div style="background:#fff;border:1px solid #ead8a8;border-radius:8px;margin-bottom:18px;padding:22px 24px">
      <p style="margin:0 0 10px;color:#7a4f00;font-weight:800">AI cowork 产品周报已发布</p>
      <h1 style="font-size:24px;line-height:1.35;margin:0 0 12px;color:#06456b">{escape(meta['title'])}</h1>
      <p style="margin:0 0 16px">{escape(meta['summary'])}</p>
      <p style="margin:0">
        <a href="{escape(args.report_url)}" style="display:inline-block;background:#b77900;color:#fff;text-decoration:none;padding:10px 16px;border-radius:6px;font-weight:700;margin-right:8px">查看当期网页</a>
        <a href="{escape(args.archive_url)}" style="display:inline-block;background:#fff7dc;color:#7a4f00;text-decoration:none;padding:9px 15px;border-radius:6px;font-weight:700;border:1px solid #ead8a8">查看历史全部</a>
      </p>
    </div>
    {body}
  </div>
</body>
</html>
"""

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(("AI cowork 产品周报", smtp_user))
    message["To"] = mail_to
    if mail_cc:
        message["Cc"] = mail_cc
    if mail_bcc:
        message["Bcc"] = mail_bcc
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    send_smtp(message, smtp_host, smtp_port, smtp_user, smtp_password)
    print(f"sent published email to {mail_to}")


if __name__ == "__main__":
    main()
