# cowork报告

静态周报档案站。首页列出全部周报，`reports/` 目录保存每一期详情页。

## 自动化流程

当前采用免费优先方案：

1. GitHub Actions 每周一 09:30（北京时间）自动运行，也可以手动运行。
2. `scripts/generate_report.py` 抓取公开新闻/RSS 数据源。
3. 脚本调用 DeepSeek API 生成中文深度周报草稿。
4. 工作流把草稿提交到一个 Pull Request。
5. 你在 GitHub 邮件或 PR 页面确认，点击 Merge 后发布。
6. GitHub Pages 自动更新公开网站。

长期查看和分享的网址：

`https://zhangyyynn-create.github.io/cowork-report/`

## 密钥

DeepSeek API Key 放在 GitHub Actions Secret：

`DEEPSEEK_API_KEY`
