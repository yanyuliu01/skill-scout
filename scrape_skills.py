#!/usr/bin/env python3
"""
Claude Skills Scout v3 — 挖掘实用型 Claude Skills 隐藏宝石
核心逻辑: 从聚合仓库中解析出单个 Skill，深度分析 README，搜索中文文章

使用方法:
  python scrape_skills.py --top 15 --token ghp_xxx -o report.md --history reports/history.json -v
"""

import argparse
import base64
import json
import math
import os
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Optional

GITHUB_API = "https://api.github.com"
USER_AGENT = "Claude-Skills-Scout/3.0"


# ════════════════════════════════════════════════
# 1. 排除名单 — 太知名 / 纯聚合 / 不实用
# ════════════════════════════════════════════════

EXCLUDE_REPOS = {
    # 官方 & 大型聚合 (大家都知道，不需要我推荐)
    "anthropics/skills",
    "alirezarezvani/claude-skills",
    "travisvn/awesome-claude-skills",
    "ComposioHQ/awesome-claude-skills",
    "BehiSecc/awesome-claude-skills",
    "abubakarsiddik31/claude-skills-collection",
}

EXCLUDE_NAME_PATTERNS = [
    r"^awesome-",          # awesome-list 类
    r"-collection$",       # 合集类
    r"-registry$",         # 注册表类
]


def is_excluded(full_name: str) -> bool:
    if full_name in EXCLUDE_REPOS:
        return True
    repo_name = full_name.split("/")[-1].lower()
    return any(re.search(p, repo_name) for p in EXCLUDE_NAME_PATTERNS)


def is_aggregator(repo: dict) -> bool:
    """判断是否为聚合/索引仓库 (非实际 Skill)"""
    text = ((repo.get("description") or "") + " " + (repo.get("full_name") or "")).lower()
    signals = ["curated list", "awesome", "collection of", "registry",
               "marketplace", "directory of", "index of"]
    return sum(1 for s in signals if s in text) >= 2


# ════════════════════════════════════════════════
# 2. 矿脉: 从聚合仓库的 README 中提取单个 Skill 链接
# ════════════════════════════════════════════════

# 这些仓库不进榜单，但用来发现新 Skill
SOURCE_AWESOME_LISTS = [
    "travisvn/awesome-claude-skills",
    "BehiSecc/awesome-claude-skills",
    "ComposioHQ/awesome-claude-skills",
    "abubakarsiddik31/claude-skills-collection",
]

# 直接搜索的关键词 (聚焦具体 Skill 而非合集)
SEARCH_QUERIES = [
    "SKILL.md claude -awesome -collection",
    "claude code skill plugin",
    "skill automation workflow",
    "skill data csv",
    "skill document pdf",
    "agent skill SKILL.md",
    "claude code plugin tool",
    "skill productivity",
    "skill creative writing",
]

# 中文搜索
SEARCH_QUERIES_CN = [
    "skill 榜单",
    "实用 skill",
    "必备 skill",
    "十大 skill",
    "skill 集合",
]


def extract_repo_links_from_readme(readme_text: str) -> list:
    """从 README 的 markdown 文本中提取所有 GitHub 仓库链接"""
    patterns = [
        r'github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)',
        r'\[([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\]',
    ]
    repos = set()
    for p in patterns:
        for m in re.finditer(p, readme_text):
            name = m.group(1).rstrip("/.).>,;:'\"")
            # 基本校验
            if "/" in name and len(name) > 3 and not name.endswith(".md"):
                repos.add(name)
    return list(repos)


# ════════════════════════════════════════════════
# 3. GitHub API Client
# ════════════════════════════════════════════════

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.remaining = 30
        self.reset_at = 0

    def _headers(self):
        h = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, url: str) -> dict:
        if self.remaining <= 2 and time.time() < self.reset_at:
            wait = self.reset_at - time.time() + 2
            print(f"  ... rate limit, waiting {wait:.0f}s", file=sys.stderr)
            time.sleep(wait)

        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                self.remaining = int(resp.headers.get("X-RateLimit-Remaining", 30))
                self.reset_at = int(resp.headers.get("X-RateLimit-Reset", 0))
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 422, 451):
                return {"items": [], "_error": e.code}
            return {"items": [], "_error": e.code}
        except (urllib.error.URLError, OSError) as e:
            return {"items": [], "_error": str(e)}

    def search_repos(self, query: str, sort="stars", per_page=30) -> list:
        q = urllib.parse.quote(query)
        url = f"{GITHUB_API}/search/repositories?q={q}&sort={sort}&order=desc&per_page={per_page}"
        return self._request(url).get("items", [])

    def get_repo(self, full_name: str) -> Optional[dict]:
        data = self._request(f"{GITHUB_API}/repos/{full_name}")
        return data if "id" in data else None

    def get_readme_text(self, full_name: str, max_chars=6000) -> str:
        data = self._request(f"{GITHUB_API}/repos/{full_name}/readme")
        if data.get("content"):
            try:
                text = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                return text[:max_chars]
            except Exception:
                pass
        return ""

    def get_recent_commits(self, full_name: str, days=30) -> int:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        url = f"{GITHUB_API}/repos/{full_name}/commits?since={since}&per_page=1"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                link = resp.headers.get("Link", "")
                if 'rel="last"' in link:
                    m = re.search(r'page=(\d+)>; rel="last"', link)
                    if m:
                        return int(m.group(1))
                return len(json.loads(resp.read().decode()))
        except Exception:
            return 0

    def search_articles(self, skill_name: str) -> list:
        """搜索 GitHub 上与该 Skill 相关的讨论"""
        short = skill_name.split("/")[-1]
        q = urllib.parse.quote(f"{short} claude skill")
        url = f"{GITHUB_API}/search/repositories?q={q}&sort=updated&per_page=3"
        data = self._request(url)
        articles = []
        for item in data.get("items", [])[:2]:
            if item.get("full_name") != skill_name:
                articles.append({
                    "title": item.get("full_name", ""),
                    "url": item.get("html_url", ""),
                    "desc": (item.get("description") or "")[:100],
                    "source": "GitHub",
                })
        time.sleep(0.3)
        return articles


# ════════════════════════════════════════════════
# 3.5 外部信号采集器 (HN / Dev.to / RSS)
#     全部免费无认证，GitHub Actions 可直接使用
# ════════════════════════════════════════════════

class WebSignalCollector:
    """从 GitHub 之外的信号源采集 Skill 相关信息"""

    HN_API = "https://hn.algolia.com/api/v1"
    DEVTO_API = "https://dev.to/api"

    # 中文科技 RSS (公开可访问)
    CN_RSS_FEEDS = {
        "sspai": "https://sspai.com/feed",
    }

    def __init__(self):
        self.hn_cache = {}
        self.devto_cache = {}
        self.cn_cache = {}

    def _fetch_json(self, url: str, timeout=10) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return {}

    def _fetch_text(self, url: str, timeout=10) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            return ""

    # ── Hacker News ──

    def search_hn(self, query: str, max_results=5) -> list:
        """搜索 Hacker News 上的讨论 (免费无限额)"""
        if query in self.hn_cache:
            return self.hn_cache[query]

        q = urllib.parse.quote(query)
        # 搜 story 和 show_hn
        url = f"{self.HN_API}/search?query={q}&tags=story&hitsPerPage={max_results}"
        data = self._fetch_json(url)
        results = []
        for hit in data.get("hits", [])[:max_results]:
            title = hit.get("title", "")
            hn_url = f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            ext_url = hit.get("url", "")
            points = hit.get("points", 0) or 0
            comments = hit.get("num_comments", 0) or 0
            created = hit.get("created_at", "")[:10]
            results.append({
                "title": title,
                "url": ext_url or hn_url,
                "hn_url": hn_url,
                "points": points,
                "comments": comments,
                "date": created,
                "source": "Hacker News",
            })
        self.hn_cache[query] = results
        time.sleep(0.2)
        return results

    # ── Dev.to ──

    def search_devto(self, query: str, max_results=5) -> list:
        """搜索 Dev.to 博客文章 (免费无限额)"""
        if query in self.devto_cache:
            return self.devto_cache[query]

        q = urllib.parse.quote(query)
        url = f"{self.DEVTO_API}/articles?per_page={max_results}&search={q}"
        data = self._fetch_json(url)
        results = []
        if isinstance(data, list):
            for article in data[:max_results]:
                results.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "reactions": article.get("positive_reactions_count", 0),
                    "date": (article.get("published_at", "") or "")[:10],
                    "author": article.get("user", {}).get("username", ""),
                    "source": "Dev.to",
                })
        self.devto_cache[query] = results
        time.sleep(0.2)
        return results

    # ── 中文 RSS ──

    def search_cn_rss(self, keyword: str) -> list:
        """搜索中文科技 RSS 中包含关键词的文章"""
        results = []
        for name, feed_url in self.CN_RSS_FEEDS.items():
            if name in self.cn_cache:
                xml = self.cn_cache[name]
            else:
                xml = self._fetch_text(feed_url)
                self.cn_cache[name] = xml
                time.sleep(0.3)

            if not xml:
                continue

            # 简易 XML 解析 (不依赖 xml.etree 的复杂逻辑)
            items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL)
            for item_xml in items:
                title_m = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item_xml)
                if not title_m:
                    title_m = re.search(r'<title>(.*?)</title>', item_xml)
                link_m = re.search(r'<link>(.*?)</link>', item_xml)
                desc_m = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item_xml, re.DOTALL)

                if not title_m:
                    continue

                title = title_m.group(1).strip()
                # 检查关键词是否在标题或描述中
                desc_text = desc_m.group(1) if desc_m else ""
                search_text = (title + " " + desc_text).lower()

                if keyword.lower() in search_text:
                    results.append({
                        "title": title,
                        "url": link_m.group(1).strip() if link_m else "",
                        "source": name,
                    })
        return results[:5]

    # ── 综合搜索 ──

    def discover_skills_from_web(self, verbose=False) -> list:
        """
        核心: 从外部信号源中 *发现* Skill 仓库。
        搜索 HN/Dev.to 上关于 Claude Skills 的文章，
        从中提取 GitHub 仓库链接作为新候选。
        返回 [{name, source, article_title, article_url, points}, ...]
        """
        discovered = []
        seen_repos = set()

        # HN 搜索 — 用推荐体/榜单体/教程体关键词
        hn_queries = [
            # 推荐体
            "best claude skills",
            "must have claude code",
            "favorite claude plugins",
            "claude code setup skills",
            # 榜单体
            "top claude skills 2025",
            "top claude skills 2026",
            "claude code extensions",
            # 教程/Show HN
            "Show HN claude skill",
            "Show HN SKILL.md",
            "claude code workflow",
            # 具体场景
            "claude skill productivity",
            "claude code plugin github",
            "AI coding agent skills",
            "custom claude instructions SKILL",
        ]
        if verbose:
            print("    HN: 搜索中...", file=sys.stderr)
        for q in hn_queries:
            results = self.search_hn(q, max_results=10)
            for r in results:
                # 从文章 URL 或标题中提取 GitHub 仓库
                repos = self._extract_github_repos(
                    r.get("url", ""), r.get("title", "")
                )
                for repo_name in repos:
                    if repo_name not in seen_repos:
                        seen_repos.add(repo_name)
                        discovered.append({
                            "name": repo_name,
                            "source": "Hacker News",
                            "article_title": r.get("title", ""),
                            "article_url": r.get("hn_url", ""),
                            "points": r.get("points", 0),
                        })
            time.sleep(0.3)

        # Dev.to 搜索 — 博客/教程体
        devto_queries = [
            # 推荐体
            "best claude skills",
            "must have claude code skills",
            "essential claude code plugins",
            "my favorite claude skills",
            # 教程体
            "how to use claude skills",
            "claude code skills tutorial",
            "claude code tips tricks",
            "getting started claude skills",
            # 榜单体
            "top 10 claude skills",
            "claude code workflow 2026",
            "awesome claude code",
            # 场景体
            "claude skill development",
            "AI coding assistant plugins",
            "claude code productivity",
        ]
        if verbose:
            print("    Dev.to: 搜索中...", file=sys.stderr)
        for q in devto_queries:
            results = self.search_devto(q, max_results=10)
            for r in results:
                # Dev.to 文章 URL 不是 GitHub，但文章内可能提到 GitHub 仓库
                # 先用标题推断
                repos = self._extract_github_repos(
                    r.get("url", ""), r.get("title", "")
                )
                for repo_name in repos:
                    if repo_name not in seen_repos:
                        seen_repos.add(repo_name)
                        discovered.append({
                            "name": repo_name,
                            "source": "Dev.to",
                            "article_title": r.get("title", ""),
                            "article_url": r.get("url", ""),
                            "points": r.get("reactions", 0),
                        })
            time.sleep(0.3)

        # 中文 RSS — 搜 claude 相关
        if verbose:
            print("    RSS: 搜索中...", file=sys.stderr)
        for kw in ["claude", "skill", "AI 编程", "Claude Code", "AI 插件"]:
            cn_results = self.search_cn_rss(kw)
            for r in cn_results:
                # RSS 里的链接可能指向 GitHub
                repos = self._extract_github_repos(r.get("url", ""), r.get("title", ""))
                for repo_name in repos:
                    if repo_name not in seen_repos:
                        seen_repos.add(repo_name)
                        discovered.append({
                            "name": repo_name,
                            "source": r.get("source", "RSS"),
                            "article_title": r.get("title", ""),
                            "article_url": r.get("url", ""),
                            "points": 0,
                        })

        if verbose:
            print(f"    外部信号共发现 {len(discovered)} 个仓库线索", file=sys.stderr)
        return discovered

    def _extract_github_repos(self, url: str, title: str) -> list:
        """从 URL 和标题文本中提取 GitHub owner/repo"""
        repos = set()
        # 从 URL 提取
        m = re.search(r'github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', url)
        if m:
            name = m.group(1).rstrip("/.)>")
            if not name.endswith(".md") and not name.endswith(".io"):
                repos.add(name)
        # 从标题提取 owner/repo 模式
        for m in re.finditer(r'([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)', title):
            candidate = m.group(1)
            # 基本过滤: 不是日期、不是路径
            if len(candidate) > 5 and "/" in candidate and \
               not re.match(r'\d+/\d+', candidate):
                repos.add(candidate)
        return list(repos)

    def collect_signals(self, skill_name: str, verbose=False) -> dict:
        """
        为一个 Skill 采集所有外部信号。
        返回 {articles: [...], hn_points: int, devto_reactions: int, buzz_score: float}
        """
        short_name = skill_name.split("/")[-1]
        all_articles = []
        total_hn_points = 0
        total_devto_reactions = 0

        # HN 搜索 (尝试多个 query)
        for q in [short_name, f"{short_name} claude", f"{short_name} AI skill"]:
            hn_results = self.search_hn(q, max_results=3)
            for r in hn_results:
                if short_name.lower() in r.get("title", "").lower() or \
                   short_name.lower() in r.get("url", "").lower():
                    all_articles.append(r)
                    total_hn_points += r.get("points", 0)
            if hn_results:
                break  # 第一个有结果的 query 就够了

        # Dev.to 搜索
        for q in [f"claude {short_name}", short_name]:
            devto_results = self.search_devto(q, max_results=3)
            for r in devto_results:
                title_lower = r.get("title", "").lower()
                if short_name.lower() in title_lower or "claude" in title_lower:
                    all_articles.append(r)
                    total_devto_reactions += r.get("reactions", 0)
            if devto_results:
                break

        # 中文 RSS
        for kw in [short_name, "claude skill", "claude code"]:
            cn_results = self.search_cn_rss(kw)
            all_articles.extend(cn_results)
            if cn_results:
                break

        # 去重 (按 URL)
        seen_urls = set()
        unique = []
        for a in all_articles:
            url = a.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(a)

        # 计算综合 buzz score (0-30)
        buzz = min(total_hn_points / 50, 1.0) * 10 + \
               min(total_devto_reactions / 20, 1.0) * 5 + \
               min(len(unique) / 3, 1.0) * 15

        return {
            "articles": unique[:8],
            "hn_points": total_hn_points,
            "devto_reactions": total_devto_reactions,
            "buzz_score": round(buzz, 1),
        }


# ════════════════════════════════════════════════
# 4. README 深度解析 — 提取有价值的信息
# ════════════════════════════════════════════════

def parse_readme_deep(readme: str, repo: dict) -> dict:
    """
    从 README 中提取结构化信息:
    - what: 这个 Skill 具体做什么
    - features: 核心功能点列表
    - usage: 怎么安装和使用
    - example: 使用示例/效果展示
    - tools: 兼容的工具
    """
    info = {
        "what": "",
        "features": [],
        "usage": "",
        "example": "",
        "tools": [],
        "skill_count": "",
    }

    if not readme:
        info["what"] = repo.get("description", "") or "暂无详细描述"
        return info

    lines = readme.split("\n")
    full_lower = readme.lower()

    # ── 提取 What (第一段非空非标题文本) ──
    found_first_para = False
    para_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("![") or stripped.startswith("<!--"):
            if para_lines:
                break
            continue
        if stripped.startswith("|") or stripped.startswith("```") or stripped.startswith("---"):
            if para_lines:
                break
            continue
        para_lines.append(stripped)
        found_first_para = True

    if para_lines:
        info["what"] = " ".join(para_lines)[:500]
    else:
        info["what"] = repo.get("description", "") or "暂无详细描述"

    # ── 提取 Features (查找带 bullet 的列表) ──
    feature_section = False
    for line in lines:
        lower = line.lower().strip()
        if any(kw in lower for kw in ["feature", "what it does", "capabilities",
                                       "highlights", "what you get"]):
            feature_section = True
            continue
        if feature_section:
            if line.strip().startswith(("#", "##")):
                feature_section = False
                continue
            m = re.match(r'^[\s]*[-*]\s+(.+)', line)
            if m and len(info["features"]) < 6:
                feat = m.group(1).strip()
                # 清理 markdown 格式
                feat = re.sub(r'\*\*(.+?)\*\*', r'\1', feat)
                feat = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', feat)
                if len(feat) > 10:
                    info["features"].append(feat[:150])

    # 如果没找到 feature section，提取所有 bullet points 中看起来像功能的
    if not info["features"]:
        for line in lines:
            m = re.match(r'^[\s]*[-*]\s+\*?\*?(.+)', line)
            if m:
                text = m.group(1).strip().rstrip("*")
                text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
                if 15 < len(text) < 200 and not text.startswith("http"):
                    info["features"].append(text[:150])
                    if len(info["features"]) >= 5:
                        break

    # ── 提取安装命令 ──
    install_patterns = [
        r'(npx skills add [^\n`]+)',
        r'(/plugin (?:marketplace add|install) [^\n`]+)',
        r'(pip install [^\n`]+)',
        r'(npm install [^\n`]+)',
        r'(git clone [^\n`]+)',
    ]
    for p in install_patterns:
        m = re.search(p, readme)
        if m:
            info["usage"] = m.group(1).strip()[:200]
            break

    # 如果没找到命令，找 Installation/Usage 段落
    if not info["usage"]:
        for i, line in enumerate(lines):
            if re.match(r'^#{1,3}\s*(install|usage|getting started|setup|quick start)', line, re.I):
                # 取后面几行
                snippet = []
                for j in range(i+1, min(i+5, len(lines))):
                    s = lines[j].strip()
                    if s and not s.startswith("#"):
                        snippet.append(s)
                if snippet:
                    info["usage"] = " ".join(snippet)[:300]
                break

    # ── 提取使用示例 ──
    for i, line in enumerate(lines):
        if re.match(r'^#{1,3}\s*(example|demo|usage example|how to use)', line, re.I):
            snippet = []
            for j in range(i+1, min(i+6, len(lines))):
                s = lines[j].strip()
                if s and not s.startswith("#"):
                    snippet.append(s)
            if snippet:
                info["example"] = " ".join(snippet)[:400]
            break

    # ── 兼容工具 ──
    for tool in ["Claude Code", "Claude.ai", "Cursor", "Codex", "Windsurf",
                  "Aider", "Gemini CLI", "Kilo Code", "OpenCode"]:
        if tool.lower() in full_lower:
            info["tools"].append(tool)

    # ── Skill 数量 ──
    m = re.search(r'(\d+)\+?\s*(?:skills?|plugins?|tools?)', readme, re.I)
    if m:
        info["skill_count"] = m.group(0)

    return info


# ════════════════════════════════════════════════
# 5. 中文描述生成器
# ════════════════════════════════════════════════

# C端分类关键词
CONSUMER_KEYWORDS = {
    "doc", "pdf", "pptx", "xlsx", "word", "excel", "slide", "presentation",
    "design", "art", "creative", "music", "writing", "blog", "brand", "poster",
    "resume", "epub", "video", "tts", "image", "gif", "animation",
    "automation", "workflow", "email", "slack", "notion", "calendar", "todo",
    "task", "kanban", "gmail", "meeting", "bookmark", "productivity",
    "data", "analytics", "csv", "chart", "visualization", "dashboard",
    "learn", "teach", "education", "translate", "language", "i18n",
    "health", "fitness", "diet", "recipe", "wellness", "travel",
    "summariz", "report", "template", "memo", "letter", "invoice",
}


def generate_cn_report_entry(repo: dict, readme_info: dict, articles: list,
                              commits: int, is_new: bool) -> str:
    """为单个 Skill 生成详细中文报告段落"""
    name = repo["full_name"]
    short_name = name.split("/")[-1]
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    desc = repo.get("description", "") or ""
    pushed = repo.get("pushed_at", "")[:10]
    lang = repo.get("language", "")
    topics = repo.get("topics", [])

    # 判断是否 C 端
    text_lower = (desc + " " + short_name + " " + " ".join(topics)).lower()
    is_consumer = any(kw in text_lower for kw in CONSUMER_KEYWORDS)

    lines = []
    lines.append(f"### [{short_name}](https://github.com/{name})")
    lines.append("")

    # 核心数据行
    badges = []
    badges.append(f"Stars {stars:,}")
    badges.append(f"Forks {forks:,}")
    if commits > 0:
        badges.append(f"近30天 {commits} commits")
    badges.append(f"更新于 {pushed}")
    if lang:
        badges.append(lang)
    if is_consumer:
        badges.append("C端友好")
    lines.append(f"> {' | '.join(badges)}")
    lines.append("")

    # ── 这是什么 ──
    what = readme_info.get("what", desc) or desc
    # 清理 markdown
    what = re.sub(r'\[(.+?)\]\(.+?\)', r'\\1', what)
    what = re.sub(r'\*\*(.+?)\*\*', r'\\1', what)
    what = what.strip()

    lines.append(f"**它是什么:** {what}")
    lines.append("")

    # ── 核心功能 ──
    features = readme_info.get("features", [])
    if features:
        lines.append("**核心功能:**")
        for f in features[:5]:
            f_clean = re.sub(r'\*\*(.+?)\*\*', r'\\1', f)
            f_clean = re.sub(r'\[(.+?)\]\(.+?\)', r'\\1', f_clean)
            lines.append(f"- {f_clean}")
        lines.append("")

    # ── 怎么安装 ──
    usage = readme_info.get("usage", "")
    if usage:
        lines.append(f"**安装/使用:** `{usage}`")
        lines.append("")
    else:
        lines.append(f"**安装/使用:** 将 Skill 文件夹放入 Claude 的 skills 目录，或参考仓库 README 的安装说明。")
        lines.append("")

    # ── 兼容工具 ──
    tools = readme_info.get("tools", [])
    if tools:
        lines.append(f"**兼容:** {', '.join(tools)}")
        lines.append("")

    # ── 使用示例 ──
    example = readme_info.get("example", "")
    if example:
        example_clean = re.sub(r'\[(.+?)\]\(.+?\)', r'\\1', example)
        example_clean = re.sub(r'```[a-z]*', '', example_clean).strip()
        if len(example_clean) > 20:
            lines.append(f"**示例:** {example_clean[:300]}")
            lines.append("")

    # ── 相关文章/讨论 ──
    if articles:
        lines.append("**外部讨论与文章:**")
        for a in articles[:5]:
            if a.get("url"):
                source = a.get("source", "")
                title = a.get("title", "") or a.get("desc", "")[:60]
                extra = ""
                if a.get("points"):
                    extra = f" ({a['points']} pts, {a.get('comments', 0)} comments)"
                elif a.get("reactions"):
                    extra = f" ({a['reactions']} reactions)"
                lines.append(f"- [{source}] [{title}]({a['url']}){extra}")
        lines.append("")

    # ── 外部热度指标 ──
    web_sig = repo.get("_web_signals", {})
    if web_sig.get("buzz_score", 0) > 0:
        parts = []
        if web_sig.get("hn_points", 0) > 0:
            parts.append(f"HN {web_sig['hn_points']} pts")
        if web_sig.get("devto_reactions", 0) > 0:
            parts.append(f"Dev.to {web_sig['devto_reactions']} reactions")
        parts.append(f"热度分 {web_sig['buzz_score']}/30")
        lines.append(f"**外部热度:** {' | '.join(parts)}")
        lines.append("")

    # ── Topics ──
    if topics:
        lines.append(f"*Topics: {', '.join(topics[:8])}*")
        lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines), is_consumer


# ════════════════════════════════════════════════
# 6. 评分模型
# ════════════════════════════════════════════════

def compute_score(repo: dict, commits: int = 0, readme_info: dict = None, web_buzz: float = 0) -> float:
    """
    实用型 Skill 评分 (0-100):
    - Stars (25%): 降低头部效应
    - 活跃度 (20%): 近期更新 + 提交频率
    - 内容质量 (20%): README 信息量
    - 外部热度 (20%): HN/Dev.to/中文科技媒体讨论
    - 完整度 (5%): 描述、License、Topics
    - 专注度 (10%): 奖励聚焦单一功能
    """
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    has_desc = bool(repo.get("description"))
    has_license = bool(repo.get("license"))
    has_topics = len(repo.get("topics", [])) > 0

    # Stars: 对数+平方根混合，让小众精品也能出头
    star_score = min((math.log10(max(stars, 1)) * 0.6 + math.sqrt(stars) * 0.01) / 3, 1.0) * 25

    # 活跃度
    pushed_at = repo.get("pushed_at", "")
    recency = 0
    if pushed_at:
        try:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            days_ago = (datetime.now(timezone.utc) - pushed).days
            recency = max(0, (1 - days_ago / 180)) * 10
        except Exception:
            pass
    commit_s = min(commits / 15, 1.0) * 10

    # 内容质量 (README 信息量)
    quality = 0
    if readme_info:
        if readme_info.get("features"):
            quality += 7
        if readme_info.get("usage"):
            quality += 5
        if readme_info.get("example"):
            quality += 5
        if readme_info.get("tools"):
            quality += 2
        if len(readme_info.get("what", "")) > 100:
            quality += 1
    quality = min(quality, 20)

    # 完整度
    completeness = sum([has_desc, has_license, has_topics]) / 3 * 5

    # 专注度
    focus = 5
    name_lower = repo.get("full_name", "").lower()
    desc_lower = (repo.get("description", "") or "").lower()
    if any(kw in name_lower for kw in ["awesome", "collection", "registry"]):
        focus = 0
    elif any(kw in desc_lower for kw in ["220+", "100+", "comprehensive collection"]):
        focus = 2
    else:
        focus = 10

    # 外部热度 (HN/Dev.to/中文RSS) — 最高 20 分
    buzz = min(web_buzz, 20)

    return round(star_score + recency + commit_s + quality + completeness + focus + buzz, 1)


# ════════════════════════════════════════════════
# 7. 历史追踪
# ════════════════════════════════════════════════

def load_history(path: str) -> dict:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_history(history: dict, path: str):
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ════════════════════════════════════════════════
# 8. Pipeline
# ════════════════════════════════════════════════

def collect_all(client: GitHubClient, verbose=False) -> dict:
    """采集所有候选 Skill 仓库"""
    seen = {}
    web_discovered = {}  # 从外部信号发现的仓库，带来源标注

    def _add(repos):
        for r in repos:
            name = r.get("full_name", "")
            if name and name not in seen and not is_excluded(name):
                seen[name] = r

    # ★ 阶段 0: 从外部信号(HN/Dev.to/RSS)中发现 Skill
    print("  [0/5] 外部信号发现 (HN/Dev.to/RSS)...", file=sys.stderr)
    web = WebSignalCollector()
    web_leads = web.discover_skills_from_web(verbose=verbose)
    web_count = 0
    for lead in web_leads:
        name = lead["name"]
        if is_excluded(name) or name in seen:
            continue
        repo = client.get_repo(name)
        if repo and not repo.get("fork", False):
            # 标记这个仓库是从外部信号发现的
            repo["_discovered_via"] = {
                "source": lead["source"],
                "article_title": lead["article_title"],
                "article_url": lead["article_url"],
                "points": lead["points"],
            }
            seen[name] = repo
            web_discovered[name] = lead
            web_count += 1
        time.sleep(0.3)
    print(f"    外部信号发现 {web_count} 个有效仓库", file=sys.stderr)

    # 阶段 1: 从 awesome-list 矿脉中挖掘单个 Skill
    print("  [1/5] 解析聚合仓库中的 Skill 链接...", file=sys.stderr)
    mined_names = set()
    for source in SOURCE_AWESOME_LISTS:
        if verbose:
            print(f"    矿脉: {source}", file=sys.stderr)
        readme = client.get_readme_text(source, max_chars=15000)
        if readme:
            links = extract_repo_links_from_readme(readme)
            mined_names.update(links)
        time.sleep(0.5)
    print(f"    从聚合仓库中提取到 {len(mined_names)} 个链接", file=sys.stderr)

    # 获取挖掘出的仓库详情 (取前 80 个，避免 API 超限)
    count = 0
    for name in sorted(mined_names):
        if is_excluded(name) or name in seen:
            continue
        if count >= 80:
            break
        repo = client.get_repo(name)
        if repo and not repo.get("fork", False):
            seen[name] = repo
            count += 1
        time.sleep(0.3)

    # 阶段 2: 关键词搜索
    print("  [2/5] 关键词搜索...", file=sys.stderr)
    for q in SEARCH_QUERIES:
        if verbose:
            print(f"    搜索: {q}", file=sys.stderr)
        _add(client.search_repos(q, per_page=15))
        time.sleep(0.5)

    # 阶段 3: 中文搜索
    print("  [3/5] 中文关键词...", file=sys.stderr)
    for q in SEARCH_QUERIES_CN:
        if verbose:
            print(f"    搜索: {q}", file=sys.stderr)
        _add(client.search_repos(q, per_page=10))
        time.sleep(0.5)

    # 阶段 4: Topic 搜索
    print("  [4/5] Topic 搜索...", file=sys.stderr)
    for tq in ["topic:claude-skills", "topic:agent-skills", "topic:claude-code-plugin"]:
        _add(client.search_repos(tq, per_page=20))
        time.sleep(0.5)

    # 过滤掉聚合仓库
    final = {k: v for k, v in seen.items() if not is_aggregator(v)}

    return final


def rank_and_enrich(client: GitHubClient, repos: dict, top_n: int, verbose=False) -> list:
    """粗排 -> 精排 -> 深度信息补充 (含外部信号)"""
    web = WebSignalCollector()

    # 粗排
    candidates = []
    for name, repo in repos.items():
        if repo.get("stargazers_count", 0) < 2:
            continue
        repo["_score_rough"] = compute_score(repo)
        candidates.append(repo)

    candidates.sort(key=lambda r: r["_score_rough"], reverse=True)
    finalists = candidates[:top_n * 2]
    print(f"  粗排: {len(candidates)} 候选 -> {len(finalists)} 入围", file=sys.stderr)

    # 精排
    for i, r in enumerate(finalists):
        name = r["full_name"]
        if verbose:
            print(f"  [{i+1}/{len(finalists)}] {name}", file=sys.stderr)

        # GitHub 数据
        commits = client.get_recent_commits(name, days=30)
        time.sleep(0.3)
        readme = client.get_readme_text(name, max_chars=6000)
        time.sleep(0.3)
        readme_info = parse_readme_deep(readme, r)
        gh_articles = client.search_articles(name)
        time.sleep(0.3)

        # 外部信号 (HN / Dev.to / 中文 RSS)
        if verbose:
            print(f"    外部信号采集...", file=sys.stderr)
        web_signals = web.collect_signals(name, verbose=verbose)

        # 合并文章列表 (GitHub + 外部)
        all_articles = gh_articles + web_signals.get("articles", [])

        r["_commits"] = commits
        r["_readme_info"] = readme_info
        r["_articles"] = all_articles
        r["_web_signals"] = web_signals
        r["_score"] = compute_score(r, commits, readme_info, web_signals.get("buzz_score", 0))

    finalists.sort(key=lambda r: r.get("_score", 0), reverse=True)
    return finalists[:top_n]


# ════════════════════════════════════════════════
# 9. 报告生成
# ════════════════════════════════════════════════

def generate_report(ranked: list, history: dict, run_date: str) -> str:
    lines = []
    new_count = sum(1 for r in ranked if r["full_name"] not in history)

    lines.append(f"# Claude Skills 实用挖掘周报 - {run_date}")
    lines.append("")
    lines.append(f"> 自动挖掘 GitHub 上实用型 Claude Skills 隐藏宝石")
    lines.append(f"> 本期 Top {len(ranked)} | {new_count} 个新发现 | 已排除官方仓库和大型聚合列表")
    lines.append(f"> 评分 = Stars 25% + 活跃度 20% + 内容质量 20% + **外部热度(HN/Dev.to/RSS) 20%** + 专注度 10% + 完整度 5%")
    lines.append("")

    # ── 外部信号发现的 Skill (置顶) ──
    web_found = [r for r in ranked if r.get("_discovered_via")]
    if web_found:
        lines.append(f"## 外部信号发现 ({len(web_found)} 个)")
        lines.append("")
        lines.append("> 这些 Skill 是从 Hacker News、Dev.to、中文科技 RSS 的文章中挖掘出来的")
        lines.append("")
        for r in web_found:
            via = r["_discovered_via"]
            name = r["full_name"]
            short = name.split("/")[-1]
            stars = r.get("stargazers_count", 0)
            desc = (r.get("description") or "")[:80]
            source = via.get("source", "")
            article = via.get("article_title", "")[:60]
            article_url = via.get("article_url", "")
            pts = via.get("points", 0)
            lines.append(f"- **[{short}](https://github.com/{name})** ({stars} stars) - {desc}")
            if article and article_url:
                extra = f" ({pts} pts)" if pts else ""
                lines.append(f"  - 发现来源: [{source}] [{article}]({article_url}){extra}")
            lines.append("")

    # ── 速览表 ──
    lines.append("## 速览")
    lines.append("")
    lines.append("| # | 状态 | 来源 | Skill | Stars | 一句话 | 分数 |")
    lines.append("|---|------|------|-------|-------|--------|------|")
    for i, r in enumerate(ranked, 1):
        name = r["full_name"]
        short = name.split("/")[-1]
        stars = r.get("stargazers_count", 0)
        score = r.get("_score", 0)
        desc = (r.get("description") or "")[:50]
        badge = "**NEW**" if name not in history else f"#{history[name].get('appearances',0)+1}"
        # 来源标记
        if r.get("_discovered_via"):
            src = r["_discovered_via"]["source"][:5]
        else:
            src = "GitHub"
        lines.append(f"| {i} | {badge} | {src} | [{short}](https://github.com/{name}) | {stars:,} | {desc} | {score} |")
    lines.append("")

    # ── C端应用子榜 ──
    consumer_entries = []
    all_entries = []

    for r in ranked:
        entry_text, is_consumer = generate_cn_report_entry(
            r, r.get("_readme_info", {}), r.get("_articles", []),
            r.get("_commits", 0), r["full_name"] not in history
        )
        all_entries.append((r, entry_text, is_consumer))
        if is_consumer:
            consumer_entries.append((r, entry_text))

    if consumer_entries:
        lines.append(f"## C端应用精选 ({len(consumer_entries)} 个)")
        lines.append("")
        lines.append("> 非开发者也能直接用: 文档办公、创意设计、效率提升、数据分析等")
        lines.append("")
        for r, text in consumer_entries:
            lines.append(text)

    # ── 开发者工具 ──
    dev_entries = [(r, t) for r, t, ic in all_entries if not ic]
    if dev_entries:
        lines.append(f"## 开发者工具 ({len(dev_entries)} 个)")
        lines.append("")
        for r, text in dev_entries:
            lines.append(text)

    # ── 本期洞察 ──
    lines.append("## 本期洞察")
    lines.append("")

    if new_count > 0:
        lines.append(f"**新发现 {new_count} 个 Skill**，其中值得重点关注的:")
        new_repos = [r for r in ranked if r["full_name"] not in history]
        new_repos.sort(key=lambda r: r.get("_score", 0), reverse=True)
        for r in new_repos[:3]:
            name = r["full_name"]
            score = r.get("_score", 0)
            desc = (r.get("description", "") or "")[:80]
            lines.append(f"- **[{name.split('/')[-1]}](https://github.com/{name})** (score {score}) - {desc}")
        lines.append("")

    active = sorted(ranked, key=lambda r: r.get("_commits", 0), reverse=True)[:3]
    if active and active[0].get("_commits", 0) > 0:
        lines.append("**近30天最活跃:**")
        for r in active:
            if r.get("_commits", 0) > 0:
                lines.append(f"- [{r['full_name'].split('/')[-1]}](https://github.com/{r['full_name']}) - {r['_commits']} commits")
        lines.append("")

    # 外部热议排行
    buzzed = sorted(ranked, key=lambda r: r.get("_web_signals", {}).get("buzz_score", 0), reverse=True)[:5]
    has_buzz = [r for r in buzzed if r.get("_web_signals", {}).get("buzz_score", 0) > 0]
    if has_buzz:
        lines.append("**外部热议 (HN/Dev.to/中文RSS):**")
        for r in has_buzz:
            ws = r.get("_web_signals", {})
            name = r['full_name'].split('/')[-1]
            parts = []
            if ws.get("hn_points", 0) > 0:
                parts.append(f"HN {ws['hn_points']}pts")
            if ws.get("devto_reactions", 0) > 0:
                parts.append(f"Dev.to {ws['devto_reactions']}x")
            n_articles = len(ws.get("articles", []))
            if n_articles > 0:
                parts.append(f"{n_articles} 篇文章")
            lines.append(f"- [{name}](https://github.com/{r['full_name']}) - {', '.join(parts)}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Claude Skills Scout v3 | {run_date} | github.com*")

    return "\n".join(lines)


# ════════════════════════════════════════════════
# 10. Main
# ════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Claude Skills Scout v3")
    parser.add_argument("--top", type=int, default=15, help="Top N (default 15)")
    parser.add_argument("--token", type=str, default="", help="GitHub token")
    parser.add_argument("-o", "--output", type=str, default="", help="Output file")
    parser.add_argument("--history", type=str, default="", help="History JSON path")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    client = GitHubClient(token=args.token)
    run_date = datetime.now().strftime("%Y-%m-%d")

    print(f"=== Claude Skills Scout v3 === {run_date}", file=sys.stderr)

    history = load_history(args.history)
    print(f"历史: {len(history)} 个已知仓库", file=sys.stderr)

    # 采集
    print("采集中...", file=sys.stderr)
    repos = collect_all(client, verbose=args.verbose)
    print(f"发现 {len(repos)} 个候选 (已过滤聚合仓库)", file=sys.stderr)

    # 排名
    print("评分排名中...", file=sys.stderr)
    ranked = rank_and_enrich(client, repos, top_n=args.top, verbose=args.verbose)
    print(f"Top {len(ranked)} 完成", file=sys.stderr)

    # 报告
    report = generate_report(ranked, history, run_date)

    # 更新历史
    for i, r in enumerate(ranked, 1):
        name = r["full_name"]
        if name in history:
            history[name]["last_seen"] = run_date
            history[name]["appearances"] = history[name].get("appearances", 0) + 1
            history[name]["best_rank"] = min(history[name].get("best_rank", 999), i)
        else:
            history[name] = {"first_seen": run_date, "last_seen": run_date,
                             "appearances": 1, "best_rank": i}
    save_history(history, args.history)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
