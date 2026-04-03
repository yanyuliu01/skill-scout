#!/usr/bin/env python3
"""
Claude Skills Scout v2 — 自动抓取 GitHub 上最优秀的 Claude Skills
新增: 中文描述 · C端应用榜 · 历史去重 · 中文互联网信号加权

使用方法:
  python scrape_skills.py                          # 默认 top 15
  python scrape_skills.py --top 20 -o report.md    # 输出到文件
  python scrape_skills.py --token ghp_xxx -v       # 使用 token + 详细日志
  python scrape_skills.py --history reports/history.json  # 指定历史文件
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


# ════════════════════════════════════════════════
# 1. 配置
# ════════════════════════════════════════════════

GITHUB_API = "https://api.github.com"
USER_AGENT = "Claude-Skills-Scout/2.0"

# ── 搜索关键词 (英文 + 中文) ──
SEARCH_QUERIES_EN = [
    "claude skills SKILL.md",
    "claude-skills agent",
    "claude code skills plugin",
    "awesome-claude-skills",
    "agent skills SKILL.md",
    "claude skill marketplace",
]

# 中文互联网信号: GitHub 上中文内容搜索
SEARCH_QUERIES_CN = [
    "claude 技能 推荐",
    "claude skills 中文",
    "claude code 插件 技巧",
    "SKILL.md 教程",
]

# 中文博客/社区搜索 (通过 GitHub search 间接抓取提及)
CN_BUZZ_QUERIES = [
    "claude skills site:juejin.cn OR site:sspai.com OR site:zhuanlan.zhihu.com",
    "claude code skills 推荐 blog",
    "claude 插件 awesome 中文",
]

# ── 已知优质仓库 ──
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


# ════════════════════════════════════════════════
# 2. 已知仓库中文知识库
#    对高频出现的仓库预写详细中文描述
# ════════════════════════════════════════════════

KNOWN_DESCRIPTIONS = {
    "anthropics/skills": {
        "cn_name": "Anthropic 官方 Skills 合集",
        "cn_desc": "Anthropic 官方发布的 Claude Skills 示例仓库，涵盖文档处理（docx/pdf/pptx/xlsx）、创意设计（算法艺术、画布设计）、开发工具（MCP 服务器构建、Web 前端组件）和企业通信模板等。",
        "cn_usage": "在 Claude Code 中运行 `/plugin marketplace add anthropics/skills` 即可浏览和安装。也可在 Claude.ai 的 Skills 设置中上传使用。",
        "cn_effect": "安装后 Claude 会在相关场景自动调用对应 Skill，例如你说"帮我做个PPT"时会自动加载 pptx Skill 并按照专业模板输出。输出质量显著提升，格式规范、样式统一。",
        "is_consumer": True,
    },
    "alirezarezvani/claude-skills": {
        "cn_name": "220+ Claude Skills 最大开源合集",
        "cn_desc": "目前 GitHub 上最大的单体 Claude Skills 仓库，包含 220+ 个 Skills，覆盖工程、营销、产品、合规、C-level 咨询等领域。所有 Python 工具零依赖。支持 11 种 AI Agent 工具。",
        "cn_usage": "克隆仓库后运行 `./scripts/install.sh` 自动安装。也支持通过 `./scripts/convert.sh --tool cursor` 转换为其他工具格式。",
        "cn_effect": "像一个"技能百宝箱"——需要写营销文案时有营销 Skill，需要做代码审查时有安全 Skill。每个 Skill 都是独立的 SKILL.md，按需启用。",
        "is_consumer": False,
    },
    "travisvn/awesome-claude-skills": {
        "cn_name": "Awesome Claude Skills 精选索引",
        "cn_desc": "社区维护的精选 Claude Skills 列表，按类别分类整理，附带安装方法和使用场景说明。更新频率高，是发现新 Skill 的首选入口。",
        "cn_usage": "作为索引使用——浏览列表找到感兴趣的 Skill，然后点链接跳转到对应仓库安装。",
        "cn_effect": "不是一个直接使用的工具，而是一个"导航站"。定期浏览可以发现最新最热门的 Skills。",
        "is_consumer": False,
    },
    "K-Dense-AI/claude-scientific-skills": {
        "cn_name": "136 个科学研究 Skills",
        "cn_desc": "覆盖癌症基因组学、药物靶点结合、分子动力学、RNA 速度分析、地理空间科学、时间序列预测等领域，对接 78+ 科学数据库。配套 K-Dense 桌面 AI 助手。",
        "cn_usage": "安装 uv 包管理器后，将 Skill 文件夹复制到 Claude Code 的 skills 目录。每个 Skill 自动处理依赖。",
        "cn_effect": "让 Claude 变成一个多学科科研助手——可以执行多步骤的科学工作流，如"分析这个基因组数据并找出潜在的药物靶点"。",
        "is_consumer": False,
    },
    "posit-dev/skills": {
        "cn_name": "Posit 数据科学 Skills",
        "cn_desc": "由 RStudio/Posit 公司出品的 Claude Skills 合集，专注 R 语言、Shiny、Quarto 等数据科学工具链。含代码审查、架构文档生成、PR 工作流等通用开发技能。",
        "cn_usage": "运行 `npx skills add posit-dev/skills --all` 一键安装，或在 Claude Code 中添加为插件市场。",
        "cn_effect": "R 语言开发者的效率加速器——自动遵循 Posit 团队的最佳实践来写 R 包、Shiny 应用和 Quarto 文档。",
        "is_consumer": False,
    },
    "ComposioHQ/awesome-claude-skills": {
        "cn_name": "Composio 跨应用自动化 Skills",
        "cn_desc": "由 Composio 团队策划的 Skills 列表，特色是跨应用自动化——让 Claude 直接操作 Gmail、Slack、Asana、Jira 等 500+ 应用。包含连接器插件和操作指南。",
        "cn_usage": "安装 connect-apps 插件后，Claude 可以直接发邮件、创建 Issue、发 Slack 消息。需要 Composio API key（免费）。",
        "cn_effect": "把 Claude 变成一个"全能行政助手"——"帮我在 Asana 创建一个任务，然后发 Slack 通知团队"这种跨应用操作都能一句话搞定。",
        "is_consumer": True,
    },
    "obra/superpowers-skills": {
        "cn_name": "Superpowers 社区 Skills 市场",
        "cn_desc": "Jesse Vincent 创建的 Claude Code Superpowers 生态的社区 Skills 仓库。包含实验性和前沿的 Skills，更新快，适合喜欢尝鲜的用户。",
        "cn_usage": "在 Claude Code 中运行 `/plugin marketplace add obra/superpowers-marketplace` 进入市场浏览安装。",
        "cn_effect": "一个活跃的社区"应用商店"，里面的 Skill 偏实验性质，可能不如官方稳定但往往有创新的玩法。",
        "is_consumer": False,
    },
    "BehiSecc/awesome-claude-skills": {
        "cn_name": "全品类 Claude Skills 大全",
        "cn_desc": "另一个活跃的 awesome list，分类细致——文档处理、数据库、AI 媒体工具包、健康助手、音乐创作、游戏开发等应有尽有。更新频率高。",
        "cn_usage": "作为发现入口浏览，找到感兴趣的 Skill 后点击链接安装。",
        "cn_effect": "覆盖面非常广的索引，特别适合探索"原来 Claude 还能做这个"的惊喜感。",
        "is_consumer": False,
    },
}


# ════════════════════════════════════════════════
# 3. 分类体系 (含 C端 标记)
# ════════════════════════════════════════════════

CATEGORIES = {
    "consumer_creative": {
        "label": "🎨 创意/写作/设计",
        "is_consumer": True,
        "keywords": ["design", "art", "creative", "music", "writing", "blog", "brand",
                     "presentation", "poster", "resume", "epub", "video", "tts",
                     "image", "gif", "animation", "reveal"],
    },
    "consumer_doc": {
        "label": "📄 文档/办公",
        "is_consumer": True,
        "keywords": ["doc", "pdf", "pptx", "xlsx", "word", "excel", "spreadsheet",
                     "slide", "template", "report", "memo", "letter", "invoice"],
    },
    "consumer_productivity": {
        "label": "⚡ 效率/自动化",
        "is_consumer": True,
        "keywords": ["automation", "workflow", "composio", "zapier", "email", "slack",
                     "notion", "calendar", "todo", "task", "kanban", "gmail",
                     "meeting", "schedule", "bookmark"],
    },
    "consumer_data": {
        "label": "📊 数据分析/可视化",
        "is_consumer": True,
        "keywords": ["data", "analytics", "csv", "chart", "visualization", "dashboard",
                     "summariz", "insight", "notebook"],
    },
    "consumer_learning": {
        "label": "📚 学习/知识",
        "is_consumer": True,
        "keywords": ["learn", "teach", "education", "tutorial", "explain", "flashcard",
                     "language", "translate", "dictionary", "i18n"],
    },
    "consumer_health": {
        "label": "🏥 健康/生活",
        "is_consumer": True,
        "keywords": ["health", "fitness", "diet", "meal", "recipe", "wellness",
                     "dna", "genome", "medical", "travel"],
    },
    "dev_tools": {
        "label": "🛠️ 开发工具",
        "is_consumer": False,
        "keywords": ["code", "debug", "test", "review", "lint", "refactor", "git",
                     "ci", "tdd", "playwright", "jest", "typescript", "python",
                     "rust", "golang", "swift", "react", "vue", "ios", "android"],
    },
    "dev_infra": {
        "label": "☁️ DevOps/基础设施",
        "is_consumer": False,
        "keywords": ["devops", "aws", "cloud", "docker", "k8s", "terraform",
                     "deploy", "serverless", "cloudflare", "worker", "lambda"],
    },
    "dev_security": {
        "label": "🔒 安全",
        "is_consumer": False,
        "keywords": ["security", "pentest", "vuln", "audit", "codeql", "semgrep",
                     "vibesec", "compliance", "mdr"],
    },
    "dev_mcp": {
        "label": "🔌 MCP/集成",
        "is_consumer": False,
        "keywords": ["mcp", "api", "integration", "connector", "plugin",
                     "protocol", "server", "sdk"],
    },
    "scientific": {
        "label": "🔬 科学研究",
        "is_consumer": False,
        "keywords": ["scientific", "research", "science", "bio", "chem", "genomic",
                     "molecular", "physics", "math", "simulation"],
    },
    "aggregator": {
        "label": "📚 聚合/索引",
        "is_consumer": False,
        "keywords": ["awesome", "curated", "collection", "list", "marketplace",
                     "registry", "directory"],
    },
}


def classify_repo(repo: dict) -> dict:
    """分类仓库，返回 {label, is_consumer, category_key}"""
    text = (
        repo.get("description", "") + " " +
        repo.get("full_name", "") + " " +
        " ".join(repo.get("topics", []))
    ).lower()

    # 先查已知库
    known = KNOWN_DESCRIPTIONS.get(repo.get("full_name", ""))
    if known:
        # 仍要找最匹配的 label
        for key, cat in CATEGORIES.items():
            if any(kw in text for kw in cat["keywords"]):
                return {"label": cat["label"], "is_consumer": known.get("is_consumer", cat["is_consumer"]), "key": key}

    # 按关键词匹配
    best_key = "dev_tools"
    best_score = 0
    for key, cat in CATEGORIES.items():
        score = sum(1 for kw in cat["keywords"] if kw in text)
        if score > best_score:
            best_score = score
            best_key = key

    cat = CATEGORIES[best_key]
    return {"label": cat["label"], "is_consumer": cat["is_consumer"], "key": best_key}


# ════════════════════════════════════════════════
# 4. GitHub API Client
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
            print(f"  ⏳ Rate limit, waiting {wait:.0f}s...", file=sys.stderr)
            time.sleep(wait)

        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                self.remaining = int(resp.headers.get("X-RateLimit-Remaining", 30))
                self.reset_at = int(resp.headers.get("X-RateLimit-Reset", 0))
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (403, 422, 404):
                print(f"  ⚠️  HTTP {e.code} for {url[:80]}", file=sys.stderr)
                return {"items": []}
            print(f"  ⚠️  HTTP {e.code} for {url[:80]}", file=sys.stderr)
            return {"items": []}
        except (urllib.error.URLError, OSError) as e:
            print(f"  ⚠️  Network: {e}", file=sys.stderr)
            return {"items": []}

    def search_repos(self, query: str, sort="stars", per_page=30) -> list:
        q = urllib.parse.quote(query)
        url = f"{GITHUB_API}/search/repositories?q={q}&sort={sort}&order=desc&per_page={per_page}"
        return self._request(url).get("items", [])

    def get_repo(self, full_name: str) -> Optional[dict]:
        data = self._request(f"{GITHUB_API}/repos/{full_name}")
        return data if "id" in data else None

    def get_readme_excerpt(self, full_name: str, max_chars=3000) -> str:
        """获取 README 的前 N 个字符用于描述提取"""
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

    def search_cn_buzz(self, repo_name: str) -> int:
        """搜索中文互联网对该仓库的讨论热度 (GitHub code/issue 里的中文提及)"""
        short_name = repo_name.split("/")[-1]
        q = urllib.parse.quote(f"{short_name} claude skill 推荐 OR 教程 OR 测评")
        url = f"{GITHUB_API}/search/repositories?q={q}&sort=updated&per_page=5"
        data = self._request(url)
        return data.get("total_count", 0)


# ════════════════════════════════════════════════
# 5. 中文描述生成 (README 解析 + 知识库)
# ════════════════════════════════════════════════

def extract_cn_description(repo: dict, readme: str) -> dict:
    """
    为 Skill 生成中文详细描述。
    优先使用知识库，否则从 README 智能提取。
    返回 {cn_name, cn_desc, cn_usage, cn_effect}
    """
    full_name = repo.get("full_name", "")

    # 优先查知识库
    if full_name in KNOWN_DESCRIPTIONS:
        return KNOWN_DESCRIPTIONS[full_name]

    # 从 README 提取关键信息
    desc = repo.get("description", "") or ""
    name = full_name.split("/")[-1].replace("-", " ").replace("_", " ").title()

    # 提取 skill 数量
    skill_count = ""
    m = re.search(r'(\d+)\+?\s*(?:skills?|plugins?)', readme, re.IGNORECASE)
    if m:
        skill_count = f"包含 {m.group(1)}+ 个 Skill。"

    # 提取安装命令
    install_cmd = ""
    for pattern in [
        r'(npx skills add [^\n]+)',
        r'(/plugin (?:marketplace add|install) [^\n]+)',
        r'(pip install [^\n]+)',
        r'(npm install [^\n]+)',
    ]:
        m = re.search(pattern, readme)
        if m:
            install_cmd = m.group(1).strip()
            break

    # 提取支持的工具
    tools = []
    for tool in ["Claude Code", "Cursor", "Codex", "Windsurf", "Aider", "Gemini CLI"]:
        if tool.lower() in readme.lower():
            tools.append(tool)

    # 组装中文描述
    cn_desc = desc
    if skill_count:
        cn_desc += " " + skill_count
    if tools:
        cn_desc += f" 兼容: {', '.join(tools[:4])}。"

    cn_usage = ""
    if install_cmd:
        cn_usage = f"安装命令: `{install_cmd}`"
    else:
        cn_usage = "克隆仓库后将 Skill 文件夹复制到 Claude 的 skills 目录即可使用。"

    # 根据分类推断效果
    cat = classify_repo(repo)
    effect_map = {
        "consumer_creative": "让 Claude 在创意和设计任务上输出更专业的结果，减少手动调整。",
        "consumer_doc": "自动生成格式规范的文档，支持模板、样式和批量处理。",
        "consumer_productivity": "把跨应用的重复操作变成一句话指令，大幅提升日常效率。",
        "consumer_data": "让 Claude 能直接处理和可视化数据，无需手动写分析脚本。",
        "consumer_learning": "将 Claude 变成个人化的学习助手，支持互动式教学。",
        "consumer_health": "提供健康和生活方面的结构化分析与建议。",
        "dev_tools": "让 Claude 在编码任务中遵循最佳实践，提升代码质量和开发效率。",
        "dev_infra": "自动化云基础设施和部署流程，减少手动配置工作。",
        "dev_security": "在开发过程中自动检测安全隐患，防患于未然。",
        "dev_mcp": "扩展 Claude 与外部服务的连接能力，实现更复杂的自动化。",
        "scientific": "让 Claude 能执行复杂的科学计算和研究工作流。",
        "aggregator": "作为发现入口，帮你快速找到适合的 Skills。不直接提供功能。",
    }
    cn_effect = effect_map.get(cat["key"], "增强 Claude 在该领域的专业表现。")

    return {
        "cn_name": name,
        "cn_desc": cn_desc,
        "cn_usage": cn_usage,
        "cn_effect": cn_effect,
        "is_consumer": cat["is_consumer"],
    }


# ════════════════════════════════════════════════
# 6. 评分模型 (含中文热度加权)
# ════════════════════════════════════════════════

def compute_score(repo: dict, recent_commits: int = 0, cn_buzz: int = 0) -> float:
    """
    综合评分 (0-100):
    - Stars (35%): 对数归一化
    - Forks (10%): 社区参与度
    - Recency (20%): 更新时间 + 提交频率
    - Completeness (15%): 描述、License、Topics
    - CN Buzz (20%): 中文互联网热度 (新增！)
    """
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    has_desc = bool(repo.get("description"))
    has_license = bool(repo.get("license"))
    has_topics = len(repo.get("topics", [])) > 0

    star_score = min(math.log10(max(stars, 1)) / 4, 1.0) * 35
    fork_score = min(math.log10(max(forks, 1)) / 3, 1.0) * 10

    # Recency
    pushed_at = repo.get("pushed_at", "")
    recency_score = 0
    if pushed_at:
        try:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            days_ago = (datetime.now(timezone.utc) - pushed).days
            recency_score = max(0, (1 - days_ago / 365)) * 12
        except Exception:
            pass
    commit_score = min(recent_commits / 20, 1.0) * 8

    completeness = sum([has_desc, has_license, has_topics]) / 3 * 15

    # 中文热度加权 (0-20)
    # cn_buzz 是 GitHub 搜索中中文相关结果数
    # 同时对已知仓库(知识库里有的)给予基础分
    cn_score = 0
    if repo.get("full_name", "") in KNOWN_DESCRIPTIONS:
        cn_score += 10  # 知识库覆盖 = 基础中文热度
    cn_score += min(cn_buzz / 10, 1.0) * 10

    return round(star_score + fork_score + recency_score + commit_score + completeness + cn_score, 1)


# ════════════════════════════════════════════════
# 7. 历史追踪
# ════════════════════════════════════════════════

def load_history(path: str) -> dict:
    """加载历史数据 {full_name: {first_seen, last_seen, appearances, best_rank}}"""
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def update_history(history: dict, ranked: list, run_date: str) -> dict:
    """更新历史记录"""
    for i, r in enumerate(ranked, 1):
        name = r["full_name"]
        if name in history:
            history[name]["last_seen"] = run_date
            history[name]["appearances"] = history[name].get("appearances", 0) + 1
            history[name]["best_rank"] = min(history[name].get("best_rank", 999), i)
        else:
            history[name] = {
                "first_seen": run_date,
                "last_seen": run_date,
                "appearances": 1,
                "best_rank": i,
            }
    return history


def save_history(history: dict, path: str):
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ════════════════════════════════════════════════
# 8. 数据采集 Pipeline
# ════════════════════════════════════════════════

def collect_repos(client: GitHubClient, verbose=False) -> dict:
    """多策略采集，返回 {full_name: repo}"""
    seen = {}

    def _add(results):
        for r in results:
            name = r.get("full_name", "")
            if name and name not in seen:
                seen[name] = r

    # 英文关键词搜索
    for q in SEARCH_QUERIES_EN:
        if verbose:
            print(f"  🔍 EN: {q}", file=sys.stderr)
        _add(client.search_repos(q, per_page=20))
        time.sleep(0.5)

    # 中文关键词搜索 (新增)
    for q in SEARCH_QUERIES_CN:
        if verbose:
            print(f"  🔍 CN: {q}", file=sys.stderr)
        _add(client.search_repos(q, per_page=15))
        time.sleep(0.5)

    # 已知优质仓库
    for name in CURATED_REPOS:
        if name not in seen:
            if verbose:
                print(f"  📌 Curated: {name}", file=sys.stderr)
            repo = client.get_repo(name)
            if repo:
                seen[name] = repo
            time.sleep(0.3)

    # Topic 搜索
    for tq in ["topic:claude-skills", "topic:agent-skills SKILL.md"]:
        if verbose:
            print(f"  🏷️  {tq}", file=sys.stderr)
        _add(client.search_repos(tq, per_page=20))
        time.sleep(0.5)

    return seen


def enrich_repos(client: GitHubClient, repos: dict, top_n: int, verbose=False) -> list:
    """评分、补充数据、排序"""
    candidates = []

    for name, repo in repos.items():
        if repo.get("fork", False):
            continue
        if repo.get("stargazers_count", 0) < 2:
            continue
        candidates.append(repo)

    # 先粗排取 top_n * 2 进入精排
    for r in candidates:
        r["_score_rough"] = compute_score(r)
    candidates.sort(key=lambda r: r["_score_rough"], reverse=True)
    finalists = candidates[:top_n * 2]

    # 精排: 补充提交数 + 中文热度 + README
    for r in finalists:
        name = r["full_name"]
        if verbose:
            print(f"  📊 Enriching: {name}", file=sys.stderr)

        commits = 0
        if r.get("stargazers_count", 0) >= 5:
            commits = client.get_recent_commits(name, days=30)
            time.sleep(0.3)

        # 中文热度抽样 (对 top 候选做)
        cn_buzz = 0
        if r.get("stargazers_count", 0) >= 10:
            cn_buzz = client.search_cn_buzz(name)
            time.sleep(0.5)

        # README 摘要 (用于生成中文描述)
        readme = ""
        if name not in KNOWN_DESCRIPTIONS:
            readme = client.get_readme_excerpt(name, max_chars=2000)
            time.sleep(0.3)

        r["_score"] = compute_score(r, commits, cn_buzz)
        r["_recent_commits"] = commits
        r["_cn_buzz"] = cn_buzz
        r["_cn_info"] = extract_cn_description(r, readme)

    finalists.sort(key=lambda r: r.get("_score", 0), reverse=True)
    return finalists[:top_n]


# ════════════════════════════════════════════════
# 9. Markdown 报告生成
# ════════════════════════════════════════════════

def _novelty_badge(repo: dict, history: dict) -> str:
    """根据历史记录返回标记"""
    name = repo.get("full_name", "")
    if name not in history:
        return "🆕 新上榜"
    h = history[name]
    if h.get("appearances", 0) >= 3:
        return f"🔁 连续上榜({h['appearances']}次)"
    return f"📌 回归 (首次: {h.get('first_seen', '?')})"


def generate_report(ranked: list, history: dict, run_date: str) -> str:
    """生成完整报告: 总榜 + C端榜 + 详情"""
    lines = []

    # ── Header ──
    lines.append(f"# 🏆 Claude Skills 周报 — {run_date}")
    lines.append("")

    # 统计新上榜数量
    new_count = sum(1 for r in ranked if r["full_name"] not in history)
    lines.append(f"> 自动生成 · 本期 Top {len(ranked)} · 其中 **{new_count} 个新上榜** · 评分 = Stars×35% + 活跃度×20% + 完整度×15% + 中文热度×20% + Forks×10%")
    lines.append("")

    # ── 总榜 ──
    lines.append("## 📋 总榜 Top " + str(len(ranked)))
    lines.append("")
    lines.append("| # | 状态 | 仓库 | ⭐ | 🏷️ 类别 | 📊 分 |")
    lines.append("|---|------|------|-----|--------|------|")
    for i, r in enumerate(ranked, 1):
        name = r["full_name"]
        stars = r.get("stargazers_count", 0)
        cat = classify_repo(r)
        score = r.get("_score", 0)
        badge = _novelty_badge(r, history)
        lines.append(f"| {i} | {badge} | [{name}](https://github.com/{name}) | {stars:,} | {cat['label']} | {score} |")
    lines.append("")

    # ── C端应用榜 ──
    consumer_repos = [r for r in ranked if r.get("_cn_info", {}).get("is_consumer", classify_repo(r)["is_consumer"])]
    if consumer_repos:
        lines.append("## 🎯 C端应用榜 (普通用户可直接受益)")
        lines.append("")
        lines.append("> 筛选标准: 非开发者也能直接使用，覆盖文档/创意/效率/数据/生活等日常场景")
        lines.append("")
        lines.append("| # | 仓库 | ⭐ | 场景 | 一句话说明 |")
        lines.append("|---|------|-----|------|----------|")
        for i, r in enumerate(consumer_repos, 1):
            name = r["full_name"]
            stars = r.get("stargazers_count", 0)
            cat = classify_repo(r)
            cn = r.get("_cn_info", {})
            short = cn.get("cn_name", name.split("/")[-1])
            lines.append(f"| {i} | [{name}](https://github.com/{name}) | {stars:,} | {cat['label']} | {short} |")
        lines.append("")

    # ── 详细信息 (新上榜 展开 / 老面孔 折叠) ──
    lines.append("## 📝 详细信息")
    lines.append("")

    # 先展示新上榜的
    new_repos = [r for r in ranked if r["full_name"] not in history]
    old_repos = [r for r in ranked if r["full_name"] in history]

    if new_repos:
        lines.append("### 🆕 本期新上榜")
        lines.append("")
        for r in new_repos:
            _append_detail(lines, r, expanded=True)

    if old_repos:
        lines.append("### 📌 往期已收录 (简略)")
        lines.append("")
        for r in old_repos:
            _append_detail(lines, r, expanded=False)

    # ── 趋势洞察 ──
    lines.append("## 📈 趋势洞察")
    lines.append("")

    cat_counts = {}
    for r in ranked:
        c = classify_repo(r)["label"]
        cat_counts[c] = cat_counts.get(c, 0) + 1
    lines.append("**类别分布:**")
    for c, n in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {c}: {n} 个")
    lines.append("")

    # 最活跃
    active = sorted(ranked, key=lambda r: r.get("_recent_commits", 0), reverse=True)[:3]
    if active and active[0].get("_recent_commits", 0) > 0:
        lines.append("**近30天最活跃:**")
        for r in active:
            if r.get("_recent_commits", 0) > 0:
                lines.append(f"- [{r['full_name']}](https://github.com/{r['full_name']}) — {r['_recent_commits']} commits")
        lines.append("")

    # 中文热度 top
    cn_hot = sorted(ranked, key=lambda r: r.get("_cn_buzz", 0), reverse=True)[:3]
    if cn_hot and cn_hot[0].get("_cn_buzz", 0) > 0:
        lines.append("**中文社区最受关注:**")
        for r in cn_hot:
            if r.get("_cn_buzz", 0) > 0:
                lines.append(f"- [{r['full_name']}](https://github.com/{r['full_name']}) — 中文相关结果: {r['_cn_buzz']}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generated by Claude Skills Scout v2 · {run_date}*")

    return "\n".join(lines)


def _append_detail(lines: list, r: dict, expanded: bool):
    """添加单个仓库的详情"""
    name = r["full_name"]
    cn = r.get("_cn_info", {})
    cat = classify_repo(r)
    score = r.get("_score", 0)
    stars = r.get("stargazers_count", 0)
    forks = r.get("forks_count", 0)
    commits = r.get("_recent_commits", 0)
    cn_buzz = r.get("_cn_buzz", 0)

    cn_name = cn.get("cn_name", name.split("/")[-1])

    if not expanded:
        # 老面孔: 一行简略
        lines.append(f"- **[{name}](https://github.com/{name})** ({cn_name}) — ⭐ {stars:,} · 得分 {score} · 近30天 {commits} commits")
        return

    # 新上榜: 详细展开
    lines.append(f"#### [{name}](https://github.com/{name})")
    lines.append("")

    cn_desc = cn.get("cn_desc", r.get("description", "暂无描述"))
    cn_usage = cn.get("cn_usage", "")
    cn_effect = cn.get("cn_effect", "")

    lines.append(f"**{cn_name}** · {cat['label']}")
    lines.append("")
    lines.append(f"📖 **是什么:** {cn_desc}")
    lines.append("")
    if cn_usage:
        lines.append(f"🔧 **怎么用:** {cn_usage}")
        lines.append("")
    if cn_effect:
        lines.append(f"✨ **效果:** {cn_effect}")
        lines.append("")

    # 数据卡片
    lang = r.get("language", "N/A")
    lic = r.get("license", {})
    lic_name = lic.get("spdx_id", "N/A") if lic else "N/A"
    topics = ", ".join(r.get("topics", [])[:6]) or "无"

    lines.append(f"> ⭐ {stars:,} · 🍴 {forks:,} · 📊 得分 {score} · 近30天 {commits} commits · 中文热度 {cn_buzz}")
    lines.append(f"> 语言: {lang} · License: {lic_name} · Topics: `{topics}`")
    lines.append("")
    lines.append("---")
    lines.append("")


# ════════════════════════════════════════════════
# 10. Main
# ════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Claude Skills Scout v2")
    parser.add_argument("--top", type=int, default=15, help="Top N (默认 15)")
    parser.add_argument("--token", type=str, default="", help="GitHub token")
    parser.add_argument("-o", "--output", type=str, default="", help="输出文件路径")
    parser.add_argument("--history", type=str, default="", help="历史记录 JSON 路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细日志")
    args = parser.parse_args()

    client = GitHubClient(token=args.token)
    run_date = datetime.now().strftime("%Y-%m-%d")

    print(f"🚀 Claude Skills Scout v2 — {run_date}", file=sys.stderr)

    # 加载历史
    history = load_history(args.history)
    print(f"📜 历史记录: {len(history)} 个已知仓库", file=sys.stderr)

    # 采集
    print("📡 采集中...", file=sys.stderr)
    repos = collect_repos(client, verbose=args.verbose)
    print(f"📦 发现 {len(repos)} 个仓库 (去重后)", file=sys.stderr)

    # 评分排名
    print("⚡ 评分排名中...", file=sys.stderr)
    ranked = enrich_repos(client, repos, top_n=args.top, verbose=args.verbose)
    print(f"🏆 Top {len(ranked)} 生成完毕", file=sys.stderr)

    # 生成报告
    report = generate_report(ranked, history, run_date)

    # 更新历史
    history = update_history(history, ranked, run_date)
    save_history(history, args.history)
    print(f"💾 历史已更新: {len(history)} 个仓库", file=sys.stderr)

    # 输出
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"✅ 报告: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
