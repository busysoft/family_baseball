# family_baseball
棒球相关知识

## 信息检索工具

`tools/search_report.py` 可根据输入关键词检索维基百科、MLB 官方网站、Google 搜索前 10 条与 YouTube 搜索前 10 条结果，生成中文 Markdown 报告。
`tools/interactive_robot.py` 提供交互式流程，引导输入问题并输出整合后的 Markdown 报告。

### 在 GitHub Actions 运行

你可以用 GitHub Actions 在仓库里自动执行并生成报告（适合在仓库里快速验证或保存结果）。

1. 添加工作流文件 `.github/workflows/search_report.yml`（仓库中已提供示例）。
2. 手动触发 workflow（Actions → Search report → Run workflow），并输入查询关键词与输出文件名。
3. 运行完成后，Artifacts 中会提供生成的报告文件下载。

### 使用示例

```bash
python3 tools/search_report.py --query "棒球 历史" --sources "wikipedia,mlb,google,youtube" --output report.md
```

### 交互式使用

```bash
python3 tools/interactive_robot.py
```

### 本地测试

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 tools/search_report.py --query "棒球 历史" --sources "wikipedia,mlb,google,youtube" --output report.md
```
