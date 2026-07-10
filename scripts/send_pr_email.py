#!/usr/bin/env python3
"""Send a QQ/SMTP notification for a report review pull request."""

from __future__ import annotations

import argparse
import os
import smtplib
from email.message import EmailMessage
from html import escape


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr-url", required=True)
    parser.add_argument("--report-date", required=True)
    parser.add_argument("--site-url", default="https://zhangyyynn-create.github.io/cowork-report/")
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required secret/environment variable: {name}")
    return value


def main() -> None:
    args = parse_args()
    smtp_host = os.environ.get("SMTP_HOST", "smtp.qq.com").strip() or "smtp.qq.com"
    smtp_port = int(os.environ.get("SMTP_PORT", "465").strip() or "465")
    smtp_user = require_env("SMTP_USER")
    smtp_password = require_env("SMTP_PASSWORD")
    mail_to = require_env("MAIL_TO")

    subject = f"待确认发布：cowork报告 {args.report_date}"
    text = f"""cowork报告草稿已生成，等待你确认发布。

查看草稿 PR：
{args.pr_url}

确认方式：
1. 打开 PR。
2. 点击 Files changed 阅读本期周报。
3. 确认无误后点击 Merge pull request。
4. GitHub Pages 会自动更新：{args.site_url}
"""
    html = f"""\
<!doctype html>
<html lang="zh-CN">
<body style="margin:0;background:#fffaf0;color:#1d2f42;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',Arial,sans-serif;line-height:1.7">
  <div style="max-width:720px;margin:0 auto;padding:28px">
    <div style="background:linear-gradient(135deg,#6f4a00,#b77900 55%,#e2a90c);color:#fff;border-radius:8px;padding:24px 28px">
      <div style="font-size:13px;letter-spacing:.08em;opacity:.9">COWORK REPORT REVIEW</div>
      <h1 style="margin:10px 0 4px;font-size:28px;line-height:1.25">cowork报告草稿已生成</h1>
      <div style="opacity:.92">报告日期：{escape(args.report_date)}</div>
    </div>
    <div style="background:#fff;border:1px solid #ead8a8;border-radius:8px;margin-top:18px;padding:22px 24px">
      <p style="margin:0 0 14px">本期周报已经生成 Pull Request，等待你确认发布。</p>
      <p style="margin:0 0 18px">请打开草稿，进入 <b>Files changed</b> 阅读内容；确认无误后点击 <b>Merge pull request</b>，公开网页会自动更新。</p>
      <p style="margin:0 0 18px">
        <a href="{escape(args.pr_url)}" style="display:inline-block;background:#b77900;color:#fff;text-decoration:none;padding:10px 16px;border-radius:6px;font-weight:700">查看草稿 / 确认发布</a>
      </p>
      <p style="margin:0;color:#667085;font-size:14px">公开网站：<a href="{escape(args.site_url)}">{escape(args.site_url)}</a></p>
    </div>
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
