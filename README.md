# cowork报告

这是 AI cowork / AI buddy / Agentic workspace 产品周报的静态归档站。首页列出已发布报告，`reports/` 目录保存每一期详情页。

## 当前流程

现在采用“手动触发生成 + 邮件审核 + PR 确认发布”的方式，不再使用 GitHub 定时任务。

1. 登录 GitHub，进入本仓库的 **Actions**。
2. 打开 **Manual cowork report draft** 工作流，点击 **Run workflow**。
3. 通常保持默认参数：`dry_run=false`，`start/end` 留空。
4. 每点击一次，工作流都会重新抓取上一完整周的 AI cowork / buddy / agentic workspace 公开信息，生成一版新的待审核草稿。
5. 工作流会创建一个新的 Pull Request，并把渲染后的报告正文和确认发布入口发送到配置好的邮箱。
6. 在邮箱或 GitHub PR 页面审核内容；确认无误后点击 **Merge pull request**。
7. 合并后 GitHub Pages 会自动更新公开网站。

长期查看和分享的网址：

`https://zhangyyynn-create.github.io/cowork-report/`

## 常用参数

- `dry_run=false`：正式生成报告。只有测试流程时才改成 `true`。
- `start/end`：通常留空。只有需要补生成某个历史周期时，才手动填写日期。

现在没有重复生成锁：同一周可以多次手动触发，每次都会生成新的待审核草稿并发送邮件，方便你修改提示词或重新审稿。

## 密钥

DeepSeek API Key 放在 GitHub Actions Secret：

`DEEPSEEK_API_KEY`

邮件发送相关 Secret：

`SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `MAIL_TO`
