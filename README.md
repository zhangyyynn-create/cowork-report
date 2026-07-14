# cowork报告

静态周报归档站。首页列出全部已发布周报，`reports/` 目录保存每一期详情页。

## 当前流程

现在采用“手动触发生成 + 邮件审核 + PR 确认发布”的方式，不再使用 GitHub 定时任务。

1. 登录 GitHub，进入本仓库的 **Actions**。
2. 打开 **Manual cowork report draft** 工作流，点击 **Run workflow**。
3. 保持默认参数：`dry_run=false`，`force=false`，`start/end` 留空。
4. 工作流会自动抓取上一完整周的 AI cowork / buddy / agentic workspace 产品公开信息。
5. `scripts/generate_report.py` 调用 DeepSeek API 生成中文深度周报草稿。
6. 工作流创建一个 Pull Request，并把渲染后的预览链接发送到配置好的邮箱。
7. 在邮箱或 GitHub PR 页面审核内容；确认无误后点击 **Merge pull request**。
8. 合并后 GitHub Pages 自动更新公开网站。

长期查看和分享的网址：

`https://zhangyyynn-create.github.io/cowork-report/`

## 常用参数

- `dry_run=false`：正式生成报告。只有测试流程时才改成 `true`。
- `force=false`：默认避免同一周重复生成草稿。如果同一周期已经生成过但你确实要重跑，改成 `true`。
- `start/end`：通常留空。只有需要补生成某个历史周期时，才手动填写日期。

## 密钥

DeepSeek API Key 放在 GitHub Actions Secret：

`DEEPSEEK_API_KEY`

邮件发送相关 Secret：

`SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `MAIL_TO`
