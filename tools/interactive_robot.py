#!/usr/bin/env python3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

import search_report  # noqa: E402

DEFAULT_SOURCES = "wikipedia,mlb,google,youtube"
DEFAULT_OUTPUT = "interactive_report.md"


def prompt(text, default=None):
    if default:
        prompt_text = f"{text}（默认：{default}）："
    else:
        prompt_text = f"{text}："
    value = input(prompt_text).strip()
    if not value and default is not None:
        return default
    return value


def main():
    print("棒球信息检索交互式机器人")
    print("请按提示输入你的问题，我们将整理搜索结果并输出 Markdown 报告。")
    query = prompt("请输入你的问题/关键词")
    if not query:
        print("未提供关键词，已退出。")
        return
    sources_input = prompt(
        "请输入来源列表（逗号分隔）", default=DEFAULT_SOURCES
    )
    output = prompt("请输入输出文件名", default=DEFAULT_OUTPUT)

    sources = [s.strip().lower() for s in sources_input.split(",") if s.strip()]
    content = search_report.generate_report(query, sources)
    output_path = Path(output)
    output_path.write_text(content, encoding="utf-8")
    print(f"已生成：{output_path}")


if __name__ == "__main__":
    main()
