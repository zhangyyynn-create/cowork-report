#!/usr/bin/env python3
"""Send a QQ/SMTP notification for a report review pull request."""

from __future__ import annotations

import argparse
import os
import re
import smtplib
import urllib.request
from email.message import EmailMessage
from html import escape


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr-url", required=True)
    parser.add_argument("--report-date", required=True)
    parser.add_argument("--site-url", default="https://zhangyyynn-create.github.io/cowork-report/")
    parser.add_argument("--preview-url", default="")
    parser.add_argument("--report-file", default="")
    parser.add_argument("--report-raw-url", default="")
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required secret/environment variable: {name}")
    return value


def read_report_html(args: argparse.Namespace) -> str:
    if args.report_file and os.path.exists(args.report_file):
        with open(args.report_file, "r", encoding="utf-8") as file:
            return file.read()
    if args.report_raw_url:
        request = urllib.request.Request(args.report_raw_url, headers={"User-Agent": "Mozilla/5.0 cowork-report-mailer"})
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    return ""


def report_email_body(report_html: str) -> str:
    if not report_html:
        return '<p style="margin:0 0 14px">本期周报草稿已生成，请点击下方按钮查看。</p>'

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
        'class="lens"': 'style="background:#f8fbff;border:1px solid #d9e8f7;border-radius:8px;padding:14px 16px;margin:14px 0"',
        'class="take"': 'style="background:#fff3bf;border-left:4px solid #f0a400;border-radius:0 8px 8px 0;padding:14px 16px;margin-top:16px;color:#6a3e00"',
    }
    for old, new in replacements.items():
        body = body.replace(old, new)
    return body


def main() -> None:
    args = parse_args()
    smtp_host = os.environ.get("SMTP_HOST", "smtp.qq.com").strip() or "smtp.qq.com"
    smtp_port = int(os.environ.get("SMTP_PORT", "465").strip() or "465")
    smtp_user = require_env("SMTP_USER")
    smtp_password = require_env("SMTP_PASSWORD")
    mail_to = os.environ.get("MAIL_TO", "").strip() or smtp_user
    preview_url = args.preview_url or args.pr_url
    report_body = report_email_body(read_report_html(args))

    subject = f"待确认发布：cowork报告 {args.report_date}"
    text = f"""cowork报告草稿已生成，等待你确认发布。

查看完整网页预览：
{preview_url}

确认发布：
{args.pr_url}

确认方式：
1. 在邮件中先阅读正文，或打开完整网页预览。
2. 确认无误后打开确认发布链接。
3. 点击 Merge pull request。
4. GitHub Pages 会自动更新：{args.site_url}
"""
    html = f"""\
<!doctype html>
<html lang="zh-CN">
<body style="margin:0;background:#fffaf0;color:#1d2f42;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',Arial,sans-serif;line-height:1.7">
  <div style="max-width:760px;margin:0 auto;padding:28px">
    <div style="background:#fff;border:1px solid #ead8a8;border-radius:8px;margin-bottom:18px;padding:22px 24px">
      <p style="margin:0 0 14px">本期周报已经生成，下面可直接阅读渲染后的正文。</p>
      <p style="margin:0 0 18px">确认无误后点击 <b>确认发布</b>，进入 GitHub 后选择 <b>Merge pull request</b>，公开网页会自动更新。</p>
      <p style="margin:0">
        <a href="{escape(preview_url)}" style="display:inline-block;background:#7a4f00;color:#fff;text-decoration:none;padding:10px 16px;border-radius:6px;font-weight:700;margin-right:8px">查看完整网页预览</a>
        <a href="{escape(args.pr_url)}" style="display:inline-block;background:#b77900;color:#fff;text-decoration:none;padding:10px 16px;border-radius:6px;font-weight:700">确认发布</a>
      </p>
    </div>
    {report_body}
  </div>
</body>
</html>
"""

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_user
    message["To"] = mail_to
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as smtp:
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)

    print(f"sent review email to {mail_to}")


if __name__ == "__main__":
    main()
