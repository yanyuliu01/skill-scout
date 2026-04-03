#!/usr/bin/env python3
"""
Claude Skills Scout — 自动抓取 GitHub 上最优秀的 Claude Skills
支持多维度搜索、去重、评分排序，输出 Markdown 报告

使用方法:
  python scrape_skills.py                    # 默认输出到 stdout
  python scrape_skills.py -o report.md       # 输出到文件
  python scrape_skills.py --top 20           # 获取 top 20
  python scrape_skills.py --token ghp_xxx    # 使用 GitHub token (提高限额)
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Optional


# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────

# 搜索关键词组合 — 覆盖 Claude Skills 生态的多种命名方式
SEARCH_QUERIES = [
    "claude skills SKILL.md",
    "claude-skills agent",
    "claude code skills",
    "awesome-claude-skills",
    "agent skills SKILL.md",
    "claude skill plugin",
]

# 已知的优质聚合仓库 — 直接抓取
CURATED_REPOS = [
    "anthropics/skills",
    "alirezarezvani/claude-skills",
    "travisvn/awesome-claude-skills",
    "ComposioHQ/awesome-claude-skills",
    "BehiSecc/awesome-claude-skills",
    "K-Dense-AI/claude-scientific-skills",
    "posit-dev/skills",
    "obra/superpowers-skills",
]

# 排除的仓库 (fork 聚合、低质量等)
EXCLUDE_PATTERNS = [
    "awesome-list",  # 纯列表仓库不参与排名
]

GITHUB_API = "https://api.github.com"
USER_AGENT = "Claude-Skills-Scout/1.0"


# ──────────────────────────────────────────────
# GitHub API 封装
# ──────────────────────────────────────────────

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.remaining = 30  # 未认证默认限额
        self.reset_at = 0

    def _headers(self):
        h = {
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, url: str) -> dict:
        """带限流保护的请求"""
        if self.remaining <= 1 and time.time() < self.reset_at:
            wait = self.reset_at - time.time() + 1
            print(f"⏳ Rate limit hit, waiting {wait:.0f}s...", file=sys.stderr)
            time.sleep(wait)

        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                self.remaining = int(resp.headers.get("X-RateLimit-Remaining", 30))
                self.reset_at = int(resp.headers.get("X-RateLimit-Reset", 0))
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print(f"⚠️  Rate limited. Use --token for higher limits.", file=sys.stderr)
                return {"items": []}
            elif e.code == 422:
                return {"items": []}
            print(f"⚠️  HTTP {e.code} for {url}", file=sys.stderr)
            return {"items": []}
        except (urllib.error.URLError, OSError) as e:
            print(f"⚠️  Network error: {e} — skipping", file=sys.stderr)
            return {"items": []}

    def search_repos(self, query: str, sort="stars", per_page=30) -> list:
        """搜索仓库"""
        q = urllib.parse.quote(query)
        url = f"{GITHUB_API}/search/repositories?q={q}&sort={sort}&order=desc&per_page={per_page}"
        data = self._request(url)
        return data.get("items", [])

    def get_repo(self, full_name: str) -> Optional[dict]:
        """获取单个仓库详情"""
        url = f"{GITHUB_API}/repos/{full_name}"
        try:
            return self._request(url)
        except Exception:
            return None

    def get_readme(self, full_name: str) -> str:
        """获取 README 内容（用于分析 skill 质量）"""
        url = f"{GITHUB_API}/repos/{full_name}/readme"
        try:
            data = self._request(url)
            if data.get("content"):
                import base64
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            pass
        return ""

    def get_recent_commits(self, full_name: str, days=30) -> int:
        """获取近 N 天的提交数"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        url = f"{GITHUB_API}/repos/{full_name}/commits?since={since}&per_page=1"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                # 通过 Link header 估算总数
                link = resp.headers.get("Link", "")
                if 'rel="last"' in link:
                    import re
                    m = re.search(r'page=(\d+)>; rel="last"', link)
                    if m:
                        return int(m.group(1))
                data = json.loads(resp.read().decode())
                return len(data)
        except Exception:
            return 0


# ──────────────────────────────────────────────
# Skill 评分模型
# ──────────────────────────────────────────────

def compute_score(repo: dict, recent_commits: int = 0) -> float:
    """
    综合评分 (0-100):
    - Stars (40%): 对数归一化
    - Forks (15%): 社区参与度
    - Recency (25%): 最近更新时间 + 近期提交频率
    - Completeness (20%): 描述、README、license 等
    """
    import math

    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    has_desc = bool(repo.get("description"))
    has_license = bool(repo.get("license"))
    has_topics = len(repo.get("topics", [])) > 0

    # Stars score (log scale, max at ~10000 stars)
    star_score = min(math.log10(max(stars, 1)) / 4, 1.0) * 40

    # Forks score
    fork_score = min(math.log10(max(forks, 1)) / 3, 1.0) * 15

    # Recency score
    pushed_at = repo.get("pushed_at", "")
    recency_score = 0
    if pushed_at:
        try:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            days_ago = (datetime.now(timezone.utc) - pushed).days
            recency_score = max(0, (1 - days_ago / 365)) * 15
        except Exception:
            pass
    commit_score = min(recent_commits / 20, 1.0) * 10

    # Completeness score
    completeness = sum([has_desc, has_license, has_topics]) / 3 * 20

    return round(star_score + fork_score + recency_score + commit_score + completeness, 1)


# ──────────────────────────────────────────────
# 数据采集 & 去重
# ──────────────────────────────────────────────

def collect_repos(client: GitHubClient, verbose=False) -> dict:
    """多策略采集仓库，返回 {full_name: repo_dict}"""
    seen = {}

    # 策略1: 关键词搜索
    for q in SEARCH_QUERIES:
        if verbose:
            print(f"🔍 Searching: {q}", file=sys.stderr)
        results = client.search_repos(q, per_page=20)
        for r in results:
            name = r["full_name"]
            if name not in seen:
                seen[name] = r
        time.sleep(0.5)  # 礼貌延迟

    # 策略2: 已知优质仓库
    for name in CURATED_REPOS:
        if name not in seen:
            if verbose:
                print(f"📌 Fetching curated: {name}", file=sys.stderr)
            repo = client.get_repo(name)
            if repo and "id" in repo:
                seen[name] = repo
            time.sleep(0.3)

    # 策略3: topic 搜索
    for topic_q in ["topic:claude-skills", "topic:agent-skills SKILL.md"]:
        if verbose:
            print(f"🏷️  Topic search: {topic_q}", file=sys.stderr)
        results = client.search_repos(topic_q, per_page=20)
        for r in results:
            name = r["full_name"]
            if name not in seen:
                seen[name] = r
        time.sleep(0.5)

    return seen


def enrich_and_rank(client: GitHubClient, repos: dict, top_n: int, verbose=False) -> list:
    """补充数据并排序"""
    scored = []
    for name, repo in repos.items():
        # 跳过自己的 fork
        if repo.get("fork", False):
            continue

        # 最低门槛: 至少 2 stars
        if repo.get("stargazers_count", 0) < 2:
            continue

        # 获取近期提交数 (仅对 top 候选者)
        commits = 0
        if repo.get("stargazers_count", 0) >= 5:
            if verbose:
                print(f"  📊 Checking commits for {name}", file=sys.stderr)
            commits = client.get_recent_commits(name, days=30)
            time.sleep(0.3)

        score = compute_score(repo, commits)
        repo["_score"] = score
        repo["_recent_commits"] = commits
        scored.append(repo)

    scored.sort(key=lambda r: r["_score"], reverse=True)
    return scored[:top_n]


# ──────────────────────────────────────────────
# Markdown 报告生成
# ──────────────────────────────────────────────

def classify_repo(repo: dict) -> str:
    """基于描述和名称推断类别"""
    text = (repo.get("description", "") + " " + repo.get("full_name", "")).lower()
    if any(k in text for k in ["awesome", "curated", "collection", "list"]):
        return "📚 聚合/索引"
    if any(k in text for k in ["scientific", "research", "science"]):
        return "🔬 科学研究"
    if any(k in text for k in ["security", "pentest", "vuln"]):
        return "🔒 安全"
    if any(k in text for k in ["data", "analytics", "csv", "database"]):
        return "📊 数据分析"
    if any(k in text for k in ["design", "art", "creative", "music"]):
        return "🎨 创意/设计"
    if any(k in text for k in ["devops", "aws", "cloud", "docker"]):
        return "☁️ DevOps/云"
    if any(k in text for k in ["doc", "pdf", "pptx", "xlsx", "document"]):
        return "📄 文档处理"
    if any(k in text for k in ["automation", "workflow", "composio"]):
        return "⚙️ 自动化"
    return "🧩 通用/工具"


def generate_report(ranked: list, run_date: str) -> str:
    """生成 Markdown 报告"""
    lines = []
    lines.append(f"# 🏆 Claude Skills Top {len(ranked)} — {run_date}")
    lines.append("")
    lines.append(f"> 自动生成于 {run_date} · 数据来源: GitHub API · 排名基于 Stars/活跃度/完整度综合评分")
    lines.append("")

    # 总览表格
    lines.append("## 📋 排行榜")
    lines.append("")
    lines.append("| # | 仓库 | ⭐ Stars | 🍴 Forks | 📅 最近更新 | 🏷️ 类别 | 📊 得分 |")
    lines.append("|---|------|---------|--------|-----------|--------|-------|")

    for i, r in enumerate(ranked, 1):
        name = r["full_name"]
        stars = r.get("stargazers_count", 0)
        forks = r.get("forks_count", 0)
        pushed = r.get("pushed_at", "")[:10]
        cat = classify_repo(r)
        score = r.get("_score", 0)
        lines.append(f"| {i} | [{name}](https://github.com/{name}) | {stars:,} | {forks:,} | {pushed} | {cat} | {score} |")

    lines.append("")

    # 详细介绍
    lines.append("## 📝 详细信息")
    lines.append("")

    for i, r in enumerate(ranked, 1):
        name = r["full_name"]
        desc = r.get("description", "暂无描述")
        stars = r.get("stargazers_count", 0)
        forks = r.get("forks_count", 0)
        lang = r.get("language", "N/A")
        license_name = r.get("license", {})
        if license_name:
            license_name = license_name.get("spdx_id", "N/A")
        else:
            license_name = "N/A"
        topics = ", ".join(r.get("topics", [])[:8]) or "无"
        commits = r.get("_recent_commits", 0)
        score = r.get("_score", 0)
        cat = classify_repo(r)

        lines.append(f"### {i}. [{name}](https://github.com/{name})")
        lines.append("")
        lines.append(f"**{desc}**")
        lines.append("")
        lines.append(f"- 类别: {cat}")
        lines.append(f"- 评分: **{score}/100** · ⭐ {stars:,} · 🍴 {forks:,}")
        lines.append(f"- 语言: {lang} · License: {license_name}")
        lines.append(f"- 近30天提交: {commits} · Topics: `{topics}`")
        lines.append("")
        lines.append("---")
        lines.append("")

    # 趋势洞察
    lines.append("## 📈 趋势洞察")
    lines.append("")

    # 类别分布
    cat_counts = {}
    for r in ranked:
        c = classify_repo(r)
        cat_counts[c] = cat_counts.get(c, 0) + 1
    for c, n in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {c}: {n} 个仓库")

    lines.append("")

    # 最活跃
    active = sorted(ranked, key=lambda r: r.get("_recent_commits", 0), reverse=True)[:3]
    if active and active[0].get("_recent_commits", 0) > 0:
        lines.append("**近30天最活跃:**")
        for r in active:
            if r.get("_recent_commits", 0) > 0:
                lines.append(f"- [{r['full_name']}](https://github.com/{r['full_name']}) — {r['_recent_commits']} commits")
        lines.append("")

    # 新星 (created in last 90 days)
    now = datetime.now(timezone.utc)
    new_repos = [r for r in ranked if r.get("created_at") and
                 (now - datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))).days < 90]
    if new_repos:
        lines.append("**新星 (90天内创建):**")
        for r in new_repos:
            lines.append(f"- [{r['full_name']}](https://github.com/{r['full_name']}) — ⭐ {r['stargazers_count']:,}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generated by Claude Skills Scout · {run_date}*")

    return "\n".join(lines)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Claude Skills Scout — GitHub 排行榜抓取器")
    parser.add_argument("--top", type=int, default=10, help="返回 Top N (默认 10)")
    parser.add_argument("--token", type=str, default="", help="GitHub personal access token")
    parser.add_argument("-o", "--output", type=str, default="", help="输出文件路径 (默认 stdout)")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    args = parser.parse_args()

    client = GitHubClient(token=args.token)
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"🚀 Claude Skills Scout 启动 — {run_date}", file=sys.stderr)

    # Step 1: 采集
    repos = collect_repos(client, verbose=args.verbose)
    print(f"📦 共发现 {len(repos)} 个去重仓库", file=sys.stderr)

    # Step 2: 评分排名
    ranked = enrich_and_rank(client, repos, top_n=args.top, verbose=args.verbose)
    print(f"🏆 Top {len(ranked)} 已生成", file=sys.stderr)

    # Step 3: 生成报告
    report = generate_report(ranked, run_date)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✅ 报告已写入: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
