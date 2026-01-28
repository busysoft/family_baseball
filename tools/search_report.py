#!/usr/bin/env python3
import argparse
import datetime
import json
import re
import sys
from html import unescape
from urllib.parse import parse_qs, quote, urlparse

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def fetch(url, params=None):
    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()
    return response.text


def fetch_json(url, params=None):
    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def parse_google_results(html, limit=10):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for block in soup.select("div.g"):
        title_tag = block.select_one("h3")
        link_tag = block.select_one("a")
        if not title_tag or not link_tag:
            continue
        href = link_tag.get("href", "")
        if href.startswith("/url?"):
            query = parse_qs(urlparse(href).query)
            href = query.get("q", [""])[0]
        if not href.startswith("http"):
            continue
        title = title_tag.get_text(strip=True)
        snippet_tag = block.select_one("div.VwiC3b")
        snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ""
        results.append({"title": title, "url": href, "snippet": snippet})
        if len(results) >= limit:
            break
    return results


def parse_youtube_results(html, limit=10):
    match = re.search(r"ytInitialData\s*=\s*(\{.*?\});", html, re.S)
    if not match:
        match = re.search(r"window\[\"ytInitialData\"\]\s*=\s*(\{.*?\});", html, re.S)
    if not match:
        return []
    data = json.loads(match.group(1))
    videos = []

    def walk(node):
        if isinstance(node, dict):
            if "videoRenderer" in node:
                yield node["videoRenderer"]
            for value in node.values():
                yield from walk(value)
        elif isinstance(node, list):
            for item in node:
                yield from walk(item)

    for video in walk(data):
        video_id = video.get("videoId")
        title_runs = video.get("title", {}).get("runs", [])
        title = "".join(run.get("text", "") for run in title_runs).strip()
        if not video_id or not title:
            continue
        url = f"https://www.youtube.com/watch?v={video_id}"
        description_runs = video.get("descriptionSnippet", {}).get("runs", [])
        snippet = "".join(run.get("text", "") for run in description_runs).strip()
        videos.append({"title": title, "url": url, "snippet": snippet})
        if len(videos) >= limit:
            break
    return videos


def search_wikipedia(query, limit=10):
    data = fetch_json(
        "https://zh.wikipedia.org/w/api.php",
        params={
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "namespace": 0,
            "format": "json",
        },
    )
    titles = data[1]
    links = data[3]
    results = []
    for title, link in zip(titles, links):
        summary = ""
        try:
            summary_data = fetch_json(
                f"https://zh.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
            )
            summary = summary_data.get("extract", "")
        except requests.RequestException:
            summary = ""
        results.append({"title": title, "url": link, "snippet": summary})
    return results


def search_mlb(query, limit=10):
    html = fetch("https://www.mlb.com/search", params={"query": query})
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for link in soup.select("a"):
        href = link.get("href", "")
        title = link.get_text(strip=True)
        if not href or not title:
            continue
        if href.startswith("/"):
            href = f"https://www.mlb.com{href}"
        if not href.startswith("https://www.mlb.com"):
            continue
        if href in seen:
            continue
        seen.add(href)
        results.append({"title": title, "url": href, "snippet": ""})
        if len(results) >= limit:
            break
    return results


def format_markdown(query, sections):
    today = datetime.date.today().isoformat()
    lines = [
        f"# 棒球信息检索报告",
        "",
        f"- 查询关键词：{query}",
        f"- 生成日期：{today}",
        "",
    ]
    for name, items in sections:
        lines.append(f"## {name}")
        lines.append("")
        if not items:
            lines.append("暂无结果或访问受限。")
            lines.append("")
            continue
        lines.append("| 序号 | 标题 | 摘要 | 链接 |")
        lines.append("| --- | --- | --- | --- |")
        for idx, item in enumerate(items, start=1):
            title = item["title"].replace("|", " ")
            snippet = unescape(item.get("snippet", "")).replace("|", " ")
            url = item["url"]
            lines.append(f"| {idx} | {title} | {snippet} | {url} |")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "根据输入条件检索维基百科、MLB官网、Google与YouTube结果，"
            "输出中文Markdown报告。"
        )
    )
    parser.add_argument("--query", required=True, help="查询关键词")
    parser.add_argument(
        "--sources",
        default="wikipedia,mlb,google,youtube",
        help="来源列表，用逗号分隔：wikipedia, mlb, google, youtube",
    )
    parser.add_argument(
        "--output", default="search_report.md", help="输出Markdown文件路径"
    )
    args = parser.parse_args()

    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    sections = []

    for source in sources:
        if source == "wikipedia":
            items = search_wikipedia(args.query)
            sections.append(("维基百科", items))
        elif source == "mlb":
            items = search_mlb(args.query)
            sections.append(("MLB 官方网站", items))
        elif source == "google":
            html = fetch("https://www.google.com/search", params={"q": args.query, "hl": "zh-CN"})
            items = parse_google_results(html)
            sections.append(("Google 搜索（前10条）", items))
        elif source == "youtube":
            html = fetch(
                "https://www.youtube.com/results",
                params={"search_query": args.query, "hl": "zh-CN"},
            )
            items = parse_youtube_results(html)
            sections.append(("YouTube 搜索（前10条）", items))
        else:
            print(f"未知来源：{source}", file=sys.stderr)

    content = format_markdown(args.query, sections)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(content)
    print(f"已生成：{args.output}")


if __name__ == "__main__":
    main()
