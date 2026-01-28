# family_baseball
棒球相关知识

## 信息检索工具

`tools/search_report.py` 可根据输入关键词检索维基百科、MLB 官方网站、Google 搜索前 10 条与 YouTube 搜索前 10 条结果，生成中文 Markdown 报告。

### 使用示例

```bash
python3 tools/search_report.py --query "棒球 历史" --sources "wikipedia,mlb,google,youtube" --output report.md
```
