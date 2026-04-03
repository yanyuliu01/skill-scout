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
    text = (repo.get("description", "") + " " + repo.get("full_name", "")).lower()
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
    "claude skill automation workflow",
    "claude skill data analysis csv",
    "claude skill document pdf docx",
    "agent skill SKILL.md creative",
    "claude skill productivity",
    "claude code plugin tool",
]

# 中文搜索
SEARCH_QUERIES_CN = [
    "claude 技能 SKILL.md",
    "claude code 插件 实用",
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
        """搜索与该 Skill 相关的中文博客/文章 (通过 GitHub search 间接)"""
        short = skill_name.split("/")[-1]
        queries = [
            f"{short} claude skill",
            f"{short} claude 教程 OR 推荐 OR 测评",
        ]
        articles = []
        for q in queries:
            encoded = urllib.parse.quote(q)
            url = f"{GITHUB_API}/search/repositories?q={encoded}&sort=updated&per_page=3"
            data = self._request(url)
            for item in data.get("items", [])[:2]:
                if item.get("full_name") != skill_name:
                    articles.append({
                        "title": item.get("full_name", ""),
                        "url": item.get("html_url", ""),
                        "desc": item.get("description", "")[:100],
                    })
            time.sleep(0.3)
        return articles[:3]


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

    # ── 相关文章 ──
    if articles:
        lines.append("**相关资源:**")
        for a in articles[:3]:
            if a.get("url"):
                title = a.get("title", "") or a.get("desc", "")[:60]
                lines.append(f"- [{title}]({a['url']})")
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

def compute_score(repo: dict, commits: int = 0, readme_info: dict = None) -> float:
    """
    实用型 Skill 评分 (0-100):
    - Stars (30%): 但降低头部效应，让小众精品也能出头
    - 活跃度 (25%): 近期更新 + 提交频率
    - 内容质量 (25%): README 信息量 (有功能列表、安装说明、示例)
    - 完整度 (10%): 描述、License、Topics
    - 专注度 (10%): 奖励聚焦单一功能的仓库，惩罚过大的集合
    """
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    has_desc = bool(repo.get("description"))
    has_license = bool(repo.get("license"))
    has_topics = len(repo.get("topics", [])) > 0

    # Stars: 对数+平方根混合，让 50 星和 5000 星的差距不要太大
    star_score = min((math.log10(max(stars, 1)) * 0.6 + math.sqrt(stars) * 0.01) / 3, 1.0) * 30

    # 活跃度
    pushed_at = repo.get("pushed_at", "")
    recency = 0
    if pushed_at:
        try:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            days_ago = (datetime.now(timezone.utc) - pushed).days
            recency = max(0, (1 - days_ago / 180)) * 12  # 半年内有更新
        except Exception:
            pass
    commit_s = min(commits / 15, 1.0) * 13

    # 内容质量 (README 信息量)
    quality = 0
    if readme_info:
        if readme_info.get("features"):
            quality += 8
        if readme_info.get("usage"):
            quality += 6
        if readme_info.get("example"):
            quality += 6
        if readme_info.get("tools"):
            quality += 3
        if len(readme_info.get("what", "")) > 100:
            quality += 2
    quality = min(quality, 25)

    # 完整度
    completeness = sum([has_desc, has_license, has_topics]) / 3 * 10

    # 专注度: 惩罚名字里带 awesome/collection 的，奖励单一功能
    focus = 5  # 基础分
    name_lower = repo.get("full_name", "").lower()
    desc_lower = (repo.get("description", "") or "").lower()
    if any(kw in name_lower for kw in ["awesome", "collection", "registry"]):
        focus = 0
    elif any(kw in desc_lower for kw in ["220+", "100+", "comprehensive collection"]):
        focus = 2
    else:
        focus = 10  # 聚焦型仓库满分

    return round(star_score + recency + commit_s + quality + completeness + focus, 1)


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

    def _add(repos):
        for r in repos:
            name = r.get("full_name", "")
            if name and name not in seen and not is_excluded(name):
                seen[name] = r

    # 阶段 1: 从 awesome-list 矿脉中挖掘单个 Skill
    print("  [1/4] 解析聚合仓库中的 Skill 链接...", file=sys.stderr)
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
    print("  [2/4] 关键词搜索...", file=sys.stderr)
    for q in SEARCH_QUERIES:
        if verbose:
            print(f"    搜索: {q}", file=sys.stderr)
        _add(client.search_repos(q, per_page=15))
        time.sleep(0.5)

    # 阶段 3: 中文搜索
    print("  [3/4] 中文关键词...", file=sys.stderr)
    for q in SEARCH_QUERIES_CN:
        if verbose:
            print(f"    搜索: {q}", file=sys.stderr)
        _add(client.search_repos(q, per_page=10))
        time.sleep(0.5)

    # 阶段 4: Topic 搜索
    print("  [4/4] Topic 搜索...", file=sys.stderr)
    for tq in ["topic:claude-skills", "topic:agent-skills", "topic:claude-code-plugin"]:
        _add(client.search_repos(tq, per_page=20))
        time.sleep(0.5)

    # 过滤掉聚合仓库
    final = {k: v for k, v in seen.items() if not is_aggregator(v)}

    return final


def rank_and_enrich(client: GitHubClient, repos: dict, top_n: int, verbose=False) -> list:
    """粗排 → 精排 → 深度信息补充"""

    # 粗排 (只用 stars + 基本信息)
    candidates = []
    for name, repo in repos.items():
        if repo.get("stargazers_count", 0) < 2:
            continue
        repo["_score_rough"] = compute_score(repo)
        candidates.append(repo)

    candidates.sort(key=lambda r: r["_score_rough"], reverse=True)
    # 取 top_n * 2 进入精排
    finalists = candidates[:top_n * 2]
    print(f"  粗排完成: {len(candidates)} 候选 -> {len(finalists)} 入围", file=sys.stderr)

    # 精排: 补充详细信息
    for i, r in enumerate(finalists):
        name = r["full_name"]
        if verbose:
            print(f"  [{i+1}/{len(finalists)}] 深度分析: {name}", file=sys.stderr)

        # 近期提交
        commits = client.get_recent_commits(name, days=30)
        time.sleep(0.3)

        # 深度解析 README
        readme = client.get_readme_text(name, max_chars=6000)
        time.sleep(0.3)
        readme_info = parse_readme_deep(readme, r)

        # 搜索相关文章
        articles = client.search_articles(name)
        time.sleep(0.3)

        r["_commits"] = commits
        r["_readme_info"] = readme_info
        r["_articles"] = articles
        r["_score"] = compute_score(r, commits, readme_info)

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
    lines.append(f"> 评分 = 内容质量 25% + 活跃度 25% + Stars 30% + 专注度 10% + 完整度 10%")
    lines.append("")

    # ── 速览表 ──
    lines.append("## 速览")
    lines.append("")
    lines.append("| # | 状态 | Skill | Stars | 一句话 | 分数 |")
    lines.append("|---|------|-------|-------|--------|------|")
    for i, r in enumerate(ranked, 1):
        name = r["full_name"]
        short = name.split("/")[-1]
        stars = r.get("stargazers_count", 0)
        score = r.get("_score", 0)
        desc = (r.get("description", "") or "")[:50]
        badge = "**NEW**" if name not in history else f"#{history[name].get('appearances',0)+1}"
        lines.append(f"| {i} | {badge} | [{short}](https://github.com/{name}) | {stars:,} | {desc} | {score} |")
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
