# Claude Skills 实用挖掘周报 - 2026-04-03

> 自动挖掘 GitHub 上实用型 Claude Skills 隐藏宝石
> 本期 Top 15 | 3 个新发现 | 已排除官方仓库和大型聚合列表
> 评分 = Stars 25% + 活跃度 20% + 内容质量 20% + **外部热度(HN/Dev.to/RSS) 20%** + 专注度 10% + 完整度 5%

## 速览

| # | 状态 | 来源 | Skill | Stars | 一句话 | 分数 |
|---|------|------|-------|-------|--------|------|
| 1 | #2 | GitHub | [nanoclaw](https://github.com/qwibitai/nanoclaw) | 26,341 | A lightweight alternative to OpenClaw that runs in | 95.0 |
| 2 | #3 | GitHub | [agents](https://github.com/wshobson/agents) | 32,854 | Intelligent automation and multi-agent orchestrati | 94.9 |
| 3 | #2 | GitHub | [agentskills](https://github.com/agentskills/agentskills) | 14,939 | Specification and documentation for Agent Skills | 93.0 |
| 4 | #4 | GitHub | [claude-skills](https://github.com/Jeffallan/claude-skills) | 7,597 | 66 Specialized Skills for Full-Stack Developers. T | 92.1 |
| 5 | #4 | GitHub | [claude-skills](https://github.com/Jeffallan/claude-skills) | 7,597 | 66 Specialized Skills for Full-Stack Developers. T | 92.1 |
| 6 | #2 | GitHub | [eigent](https://github.com/eigent-ai/eigent) | 13,393 | Eigent: The Open Source Cowork Desktop to Unlock Y | 92.0 |
| 7 | #2 | GitHub | [hive](https://github.com/aden-hive/hive) | 10,007 | Outcome driven agent development framework and run | 92.0 |
| 8 | #2 | GitHub | [cli](https://github.com/googleworkspace/cli) | 23,641 | Google Workspace CLI — one command-line tool for D | 91.9 |
| 9 | #3 | GitHub | [AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs) | 6,050 | Comprehensive open-source library of AI research a | 90.3 |
| 10 | #3 | GitHub | [claude-mem](https://github.com/thedotmack/claude-mem) | 44,784 | A Claude Code plugin that automatically captures e | 87.9 |
| 11 | #2 | GitHub | [claude-code-tips](https://github.com/ykdojo/claude-code-tips) | 7,094 | 45 tips for getting the most out of Claude Code, f | 87.3 |
| 12 | **NEW** | GitHub | [claude-hud](https://github.com/jarrodwatts/claude-hud) | 16,495 | A Claude Code plugin that shows what's happening - | 85.5 |
| 13 | **NEW** | GitHub | [notebooklm-py](https://github.com/teng-lin/notebooklm-py) | 8,863 | Unofficial Python API and agentic skill for Google | 85.3 |
| 14 | **NEW** | GitHub | [refly](https://github.com/refly-ai/refly) | 7,170 | The first open-source agent skills builder. Define | 84.8 |
| 15 | #2 | GitHub | [skills](https://github.com/trailofbits/skills) | 4,254 | Trail of Bits Claude Code skills for security rese | 84.5 |

## C端应用精选 (11 个)

> 非开发者也能直接用: 文档办公、创意设计、效率提升、数据分析等

### [nanoclaw](https://github.com/qwibitai/nanoclaw)

> Stars 26,341 | Forks 10,332 | 近30天 404 commits | 更新于 2026-04-03 | TypeScript | C端友好

**它是什么:** An AI assistant that runs agents securely in their own containers. Lightweight, built to be easily understood and completely customized for your needs.

**核心功能:**
- No installation wizard; Claude Code guides setup.
- No monitoring dashboard; ask Claude what's happening.
- No debugging tools; describe the problem and Claude fixes it.
- Isolated group context - Each group has its own CLAUDE.md memory, isolated filesystem, and runs in its own container sandbox with only that filesy
- Main channel - Your private channel (self-chat) for admin control; every group is completely isolated

**安装/使用:** `git clone https://github.com//nanoclaw.git`

**兼容:** Claude Code

**外部讨论与文章:**
- [GitHub] [sskarz/nanoclawbster](https://github.com/sskarz/nanoclawbster)
- [GitHub] [mk-knight23/AGENTS-COLLECTION](https://github.com/mk-knight23/AGENTS-COLLECTION)
- [Hacker News] [Show HN: NanoClaw – “Clawdbot” in 500 lines of TS with Apple container isolation](https://github.com/gavrielc/nanoclaw) (533 pts, 224 comments)
- [Hacker News] [NanoClaw moved from Apple Containers to Docker](https://twitter.com/Gavriel_Cohen/status/2025603982769410356) (169 pts, 141 comments)
- [Hacker News] [Running NanoClaw in a Docker Shell Sandbox](https://www.docker.com/blog/run-nanoclaw-in-docker-shell-sandboxes/) (163 pts, 80 comments)

**外部热度:** HN 865 pts | 热度分 25.0/30

*Topics: ai-agents, ai-assistant, claude-code, claude-skills, openclaw*

---

### [agents](https://github.com/wshobson/agents)

> Stars 32,854 | Forks 3,577 | 近30天 49 commits | 更新于 2026-04-01 | Python | C端友好

**它是什么:** ⚡ Updated for Opus 4.6, Sonnet 4.6 & Haiku 4.5 — Three-tier model strategy for optimal performance

**核心功能:**
- Granular Plugin Architecture: 72 focused plugins optimized for minimal token usage
- Comprehensive Tooling: 79 development tools including test generation, scaffolding, and security scanning
- 100% Agent Coverage: All plugins include specialized agents
- Agent Skills: 146 specialized skills following for progressive disclosure and token efficiency
- Clear Organization: 23 categories with 1-6 plugins each for easy discovery

**安装/使用:** `/plugin marketplace add wshobson/agents`

**兼容:** Claude Code

**外部讨论与文章:**
- [GitHub] [Putra213/claude-workflow-v2](https://github.com/Putra213/claude-workflow-v2)
- [GitHub] [Lmgsd-2024/skill-security-scan](https://github.com/Lmgsd-2024/skill-security-scan)
- [Hacker News] [Huginn: Create agents that monitor and act on your behalf](https://github.com/huginn/huginn) (1303 pts, 143 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 1303 pts | 热度分 20.0/30

*Topics: agents, anthropic, anthropic-claude, automation, claude, claude-code, claude-code-cli, claude-code-commands*

---

### [agentskills](https://github.com/agentskills/agentskills)

> Stars 14,939 | Forks 878 | 近30天 38 commits | 更新于 2026-04-02 | Python | C端友好

**它是什么:** Agent Skills are a simple, open format for giving agents new capabilities and expertise.

**核心功能:**
- Documentation — Guides and tutorials
- Specification — Format details
- Example Skills — See what's possible
- Discord — Join the discussion!

**安装/使用:** `- Documentation — Guides and tutorials - Specification — Format details - Example Skills — See what's possible`

**外部讨论与文章:**
- [GitHub] [kambleakash0/agent-skills](https://github.com/kambleakash0/agent-skills)
- [GitHub] [trancong12102/agentskills](https://github.com/trancong12102/agentskills)
- [Hacker News] [Agent Skills](https://agentskills.io/home) (544 pts, 260 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 544 pts | 热度分 20.0/30

*Topics: agent-skills*

---

### [eigent](https://github.com/eigent-ai/eigent)

> Stars 13,393 | Forks 1,560 | 近30天 48 commits | 更新于 2026-04-03 | TypeScript | C端友好

**它是什么:** [![][image-head]][eigent-site]

**核心功能:**
- ✅ Local Deployment
- ✅ Open Source
- ✅ Custom Model Support
- ✅ MCP Integration
- 🏭 Workforce

**安装/使用:** `git clone https://github.com/eigent-ai/eigent.git`

**外部讨论与文章:**
- [Hacker News] [Eigentechno – Principal Component Analysis applied to electronic music](https://www.math.uci.edu/~isik/posts/Eigentechno.html) (315 pts, 58 comments)
- [Hacker News] [Eigent: An open source Claude Cowork alternative](https://github.com/eigent-ai/eigent) (35 pts, 7 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 460 pts | 热度分 25.0/30

*Topics: agent-framework, agent-skills, agentic-ai, agentic-workflow, claude-cowork, claude-cowork-alternative, claude-cowork-free, desktop-agent*

---

### [hive](https://github.com/aden-hive/hive)

> Stars 10,007 | Forks 5,605 | 近30天 945 commits | 更新于 2026-04-03 | Python | C端友好

**它是什么:** English 简体中文 Español हिन्दी Português 日本語 Русский 한국어

**核心功能:**
- Contributing - How to contribute and submit PRs

**安装/使用:** `- Python 3.11+ for agent development`

**外部讨论与文章:**
- [GitHub] [wrsmith108/launchpad-claude-skill](https://github.com/wrsmith108/launchpad-claude-skill)
- [GitHub] [babel3-com/b3-plugins](https://github.com/babel3-com/b3-plugins)
- [Hacker News] ["You've angered the hive"](http://arstechnica.com/tech-policy/news/2011/02/anonymous-to-security-firm-working-with-fbi-youve-angered-the-hive.ars) (521 pts, 214 comments)
- [Hacker News] [We found critical vulnerabilities in Hive Social](https://zerforschung.org/posts/hive-en/) (219 pts, 78 comments)
- [Hacker News] [HiveNightmare a.k.a. SeriousSAM – anybody can read the registry in Windows 10](https://doublepulsar.com/hivenightmare-aka-serioussam-anybody-can-read-the-registry-in-windows-10-7a871c465fa5) (171 pts, 175 comments)

**外部热度:** HN 911 pts | 热度分 25.0/30

*Topics: agent, agent-framework, agent-skills, anthropic, automation, autonomous-agents, claude, harness*

---

### [cli](https://github.com/googleworkspace/cli)

> Stars 23,641 | Forks 1,169 | 近30天 238 commits | 更新于 2026-03-31 | Rust | C端友好

**它是什么:** gws

**核心功能:**
- Environment Variables
- Node.js 18+ — for npm install (or download a pre-built binary from GitHub Releases)
- A Google Cloud project — required for OAuth credentials. You can create one via the Google Cloud Console or with the gcloud CLI or with the gws a
- A Google account with access to Google Workspace
- OAuth consent screen: https://console.cloud.google.com/apis/crede

**安装/使用:** `npm install -g @googleworkspace/cli`

**外部讨论与文章:**
- [GitHub] [pvydro/clik-engine](https://github.com/pvydro/clik-engine)
- [GitHub] [flatitas/OhMySkills](https://github.com/flatitas/OhMySkills)
- [Hacker News] [“Click to subscribe, call to cancel” is illegal, FTC says](https://www.niemanlab.org/2021/11/the-end-of-click-to-subscribe-call-to-cancel-one-of-the-news-industrys-favorite-retention-tactics-is-illegal-ftc-says/) (3192 pts, 861 comments)
- [Hacker News] [Stimulation Clicker](https://neal.fun/stimulation-clicker/) (3082 pts, 589 comments)
- [Hacker News] [Vulnerability in the Mac Zoom client allows malicious websites to enable camera](https://medium.com/@jonathan.leitschuh/zoom-zero-day-4-million-webcams-maybe-an-rce-just-get-them-to-visit-your-website-ac75c83f4ef5) (1937 pts, 456 comments)

**外部热度:** HN 8211 pts | 热度分 25.0/30

*Topics: agent-skills, ai-agent, automation, cli, discovery-api, gemini-cli-extension, google-admin, google-api*

---

### [claude-mem](https://github.com/thedotmack/claude-mem)

> Stars 44,784 | Forks 3,385 | 近30天 53 commits | 更新于 2026-04-02 | TypeScript | C端友好

**它是什么:** 🇨🇳 中文 • 🇹🇼 繁體中文 • 🇯🇵 日本語 • 🇵🇹 Português • 🇧🇷 Português • 🇰🇷 한국어 • 🇪🇸 Español • 🇩🇪 Deutsch • 🇫🇷 Français • 🇮🇱 עברית • 🇸🇦 العربية • 🇷🇺 Русский • 🇵🇱 Polski • 🇨🇿 Čeština • 🇳🇱 Nederlands • 🇹🇷 Türkçe • 🇺🇦 Українська • 🇻🇳 Tiếng Việt • 🇵🇭 Tagalog • 🇮🇩 Indonesia • 🇹🇭 ไทย • 🇮🇳 हिन्दी • 🇧🇩 বাংলা • 🇵🇰 اردو • 🇷🇴 Română • 🇸🇪 Svenska • 🇮🇹 Italiano • 🇬🇷 Ελληνικά • 🇭🇺 Magyar • 🇫🇮 Suomi • 🇩🇰 Dansk • 🇳🇴 Norsk

**安装/使用:** `/plugin marketplace add thedotmack/claude-mem`

**兼容:** Claude Code

**外部讨论与文章:**
- [GitHub] [kaicmurilo/gemini-skill-claude-mem](https://github.com/kaicmurilo/gemini-skill-claude-mem)
- [GitHub] [Mboloi/claude-memory-starter-kit](https://github.com/Mboloi/claude-memory-starter-kit)
- [Hacker News] [Claude’s memory architecture is the opposite of ChatGPT’s](https://www.shloked.com/writing/claude-memory) (448 pts, 236 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 448 pts | 热度分 20.0/30

*Topics: ai, ai-agents, ai-memory, anthropic, artificial-intelligence, chromadb, claude, claude-agent-sdk*

---

### [claude-code-tips](https://github.com/ykdojo/claude-code-tips)

> Stars 7,094 | Forks 492 | 近30天 30 commits | 更新于 2026-04-02 | JavaScript | C端友好

**它是什么:** Here are my tips for getting the most out of Claude Code, including a custom status line script, cutting the system prompt in half, using Gemini CLI as Claude Code's minion, and Claude Code running itself in a container. Also includes the dx plugin.

**核心功能:**
- Tip 0: Customize your status line
- Tip 1: Learn a few essential slash commands
- Tip 2: Talk to Claude Code with your voice
- Tip 3: Break down large problems into smaller ones
- Tip 4: Using Git and GitHub CLI like a pro

**安装/使用:** 将 Skill 文件夹放入 Claude 的 skills 目录，或参考仓库 README 的安装说明。

**兼容:** Claude Code, Gemini CLI

**外部讨论与文章:**
- [GitHub] [4riel/cc-bible](https://github.com/4riel/cc-bible)
- [GitHub] [ccwriter369-beep/claude-skill-claude-code-tips](https://github.com/ccwriter369-beep/claude-skill-claude-code-tips)
- [Hacker News] [Claude Code Tips](https://agenticcoding.substack.com/p/32-claude-code-tips-from-basics-to) (9 pts, 2 comments)
- [Hacker News] [Claude Code Tips](https://github.com/ykdojo/claude-code-tips) (3 pts, 1 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 12 pts | 热度分 17.4/30

*Topics: agentic, agentic-ai, agentic-coding, agentic-workflow, ai, claude, claude-ai, claude-code*

---

### [claude-hud](https://github.com/jarrodwatts/claude-hud)

> Stars 16,495 | Forks 696 | 近30天 96 commits | 更新于 2026-03-28 | JavaScript | C端友好

**它是什么:** A Claude Code plugin that shows what's happening — context usage, active tools, running agents, and todo progress. Always visible below your input.

**核心功能:**
- Native token data from Claude Code (not estimated)
- Scales with Claude Code's reported context window size, including newer 1M-context sessions
- Parses the transcript for tool/agent activity
- Updates every 300ms

**安装/使用:** `/plugin marketplace add jarrodwatts/claude-hud`

**兼容:** Claude Code

**外部讨论与文章:**
- [Hacker News] [Show HN: Codex HUD – Claude-HUD Style Status Line for Codex CLI](https://github.com/anhannin/codex-hud) (3 pts, 0 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 4 pts | 热度分 10.8/30

*Topics: anthropic, claude, claude-code, cli, plugin, statusline, typescript*

---

### [refly](https://github.com/refly-ai/refly)

> Stars 7,170 | Forks 709 | 近30天 6 commits | 更新于 2026-03-25 | TypeScript | C端友好

**它是什么:** English · 中文

**核心功能:**
- ⚡ Run instantly: Execute skills in Refly with one click
- 🧩 Reusable infrastructure: Versioned skills, not one-off prompts
- 🔌 Export anywhere: Ship skills to Claude Code or deploy as APIs
- 🌍 Community-powered: Import, fork, and publish your own skills
- 📘 Self-Deployment Guide

**安装/使用:** `- 📘 Self-Deployment Guide`

**兼容:** Claude Code

**外部讨论与文章:**
- [GitHub] [joneshong-skills/_ref-workshop-patterns](https://github.com/joneshong-skills/_ref-workshop-patterns)
- [GitHub] [joneshong-skills/_ref-review-criteria](https://github.com/joneshong-skills/_ref-review-criteria)
- [Hacker News] [After botched test flight, Boeing will refly its Starliner spacecraft for NASA](https://www.washingtonpost.com/technology/2020/04/06/boeing-starliner-test-repeat/) (8 pts, 2 comments)
- [Hacker News] [J.K. Lundblad on X: "Rise of the Reflyable Rocket (Part 1)" / X](https://twitter.com/JK_Lundblad/status/2015034130640306649) (3 pts, 0 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 11 pts | 热度分 17.2/30

*Topics: agent, agent-skills, automation, claude, clawdbot, codex, cursor, lark-bot*

---

### [skills](https://github.com/trailofbits/skills)

> Stars 4,254 | Forks 377 | 近30天 12 commits | 更新于 2026-04-01 | Python | C端友好

**它是什么:** A Claude Code plugin marketplace from Trail of Bits providing skills to enhance AI-assisted security analysis, testing, and development workflows.

**安装/使用:** `/plugin marketplace add trailofbits/skills`

**兼容:** Claude Code, Codex

**外部讨论与文章:**
- [GitHub] [imbflool/cc-plugin-eval](https://github.com/imbflool/cc-plugin-eval)
- [GitHub] [HDineshG/ux](https://github.com/HDineshG/ux)
- [Hacker News] [Tech sector job interviews assess anxiety, not software skills: study](https://news.ncsu.edu/2020/07/tech-job-interviews-anxiety/) (1782 pts, 1141 comments)
- [Hacker News] [My dad's resume and skills from 1980](https://github.com/runvnc/dadsresume) (1482 pts, 583 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 3264 pts | 热度分 25.0/30

*Topics: agent-skills*

---

## 开发者工具 (4 个)

### [claude-skills](https://github.com/Jeffallan/claude-skills)

> Stars 7,597 | Forks 544 | 近30天 13 commits | 更新于 2026-03-23 | Python

**它是什么:** /plugin marketplace add jeffallan/claude-skills

**核心功能:**
- Quick Start Guide - Installation and first steps
- Skills Guide - Skill reference and decision trees
- Common Ground - Context engineering with /common-ground
- Workflow Commands - Project workflow commands guide
- Atlassian MCP Setup - Atlassian MCP server setup

**安装/使用:** `/plugin marketplace add jeffallan/claude-skills`

**兼容:** Claude Code

**外部讨论与文章:**
- [GitHub] [Putra213/claude-workflow-v2](https://github.com/Putra213/claude-workflow-v2)
- [GitHub] [Lmgsd-2024/skill-security-scan](https://github.com/Lmgsd-2024/skill-security-scan)
- [Hacker News] [Claude Skills are awesome, maybe a bigger deal than MCP](https://simonwillison.net/2025/Oct/16/claude-skills/) (738 pts, 370 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 738 pts | 热度分 20.0/30

*Topics: ai-agents, claude, claude-code, claude-marketplace, claude-skills*

---

### [claude-skills](https://github.com/Jeffallan/claude-skills)

> Stars 7,597 | Forks 544 | 近30天 13 commits | 更新于 2026-03-23 | Python

**它是什么:** /plugin marketplace add jeffallan/claude-skills

**核心功能:**
- Quick Start Guide - Installation and first steps
- Skills Guide - Skill reference and decision trees
- Common Ground - Context engineering with /common-ground
- Workflow Commands - Project workflow commands guide
- Atlassian MCP Setup - Atlassian MCP server setup

**安装/使用:** `/plugin marketplace add jeffallan/claude-skills`

**兼容:** Claude Code

**外部讨论与文章:**
- [GitHub] [Putra213/claude-workflow-v2](https://github.com/Putra213/claude-workflow-v2)
- [GitHub] [Lmgsd-2024/skill-security-scan](https://github.com/Lmgsd-2024/skill-security-scan)
- [Hacker News] [Claude Skills are awesome, maybe a bigger deal than MCP](https://simonwillison.net/2025/Oct/16/claude-skills/) (738 pts, 370 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 738 pts | 热度分 20.0/30

*Topics: ai-agents, claude, claude-code, claude-marketplace, claude-skills*

---

### [AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs)

> Stars 6,050 | Forks 468 | 近30天 56 commits | 更新于 2026-04-01 | TeX

**它是什么:** The most comprehensive open-source skills library enabling AI agents to autonomously conduct AI research — from idea to paper

**核心功能:**
- Path Towards AI Research Agent
- Available AI Research Engineering Skills
- Repository Structure
- Autonomous Research - The autoresearch skill orchestrates the entire research workflow using a two-loop architecture, routing to domain skills as
- Specialized Expertise - Each domain skill provides deep, production-ready knowledge of a specific framework (Megatron-LM, vLLM, TRL, etc.)

**安装/使用:** `/plugin marketplace add orchestra-research/AI-research-SKILLs`

**兼容:** Claude Code

**外部讨论与文章:**
- [GitHub] [markli1hoshipu/embody-ai-research-skills](https://github.com/markli1hoshipu/embody-ai-research-skills)
- [Hacker News] [CC can't help my AI research exp – so I open-source this "AI research skills"](https://github.com/zechenzhangAGI/claude-ai-research-skills) (1 pts, 1 comments)
- [Hacker News] [Claude can now run ML research experiments for you](https://github.com/zechenzhangAGI/AI-research-SKILLs) (1 pts, 0 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 2 pts | 热度分 15.4/30

*Topics: ai, ai-research, claude, claude-code, claude-skills, codex, gemini, gpt-5*

---

### [notebooklm-py](https://github.com/teng-lin/notebooklm-py)

> Stars 8,863 | Forks 1,121 | 近30天 135 commits | 更新于 2026-04-01 | Python

**它是什么:** A Comprehensive NotebookLM Skill & Unofficial Python API. Full programmatic access to NotebookLM's features—including capabilities the web UI doesn't expose—via Python, CLI, and AI agents like Claude Code, Codex, and OpenClaw.

**核心功能:**
- Batch downloads - Download all artifacts of a type at once
- Quiz/Flashcard export - Get structured JSON, Markdown, or HTML (web UI only shows interactive view)
- Mind map data extraction - Export hierarchical JSON for visualization tools
- Data table CSV export - Download structured tables as spreadsheets
- Slide deck as PPTX - Download editable PowerPoint files (web UI only offers PDF)

**安装/使用:** `pip install notebooklm-py`

**兼容:** Claude Code, Codex

**外部讨论与文章:**
- [GitHub] [Lynden-Group-Cyber-Tekuma/notebooklm-py](https://github.com/Lynden-Group-Cyber-Tekuma/notebooklm-py)
- [Hacker News] [Show HN: Notebooklm-Py – Unofficial Python API for Google NotebookLM](https://github.com/teng-lin/notebooklm-py) (2 pts, 0 comments)
- [infoq_cn] [从数据留底到隐身进开源，Claude Code 泄露的代码里，处处写着：这家公司人品不行](https://www.infoq.cn/article/oyztKc9IQUguMOOx6imT?utm_source=rss&amp;utm_medium=article)

**外部热度:** HN 2 pts | 热度分 10.4/30

*Topics: agentic-skill, api, claude, claude-skills, google-notebooklm, notebooklm, notebooklm-api, notebooklm-skill*

---

## 本期洞察

**新发现 3 个 Skill**，其中值得重点关注的:
- **[claude-hud](https://github.com/jarrodwatts/claude-hud)** (score 85.5) - A Claude Code plugin that shows what's happening - context usage, active tools, 
- **[notebooklm-py](https://github.com/teng-lin/notebooklm-py)** (score 85.3) - Unofficial Python API and agentic skill for Google NotebookLM. Full programmatic
- **[refly](https://github.com/refly-ai/refly)** (score 84.8) - The first open-source agent skills builder. Define skills by vibe workflow, run 

**近30天最活跃:**
- [hive](https://github.com/aden-hive/hive) - 945 commits
- [nanoclaw](https://github.com/qwibitai/nanoclaw) - 404 commits
- [cli](https://github.com/googleworkspace/cli) - 238 commits

**外部热议 (HN/Dev.to/中文RSS):**
- [nanoclaw](https://github.com/qwibitai/nanoclaw) - HN 865pts, 4 篇文章
- [eigent](https://github.com/eigent-ai/eigent) - HN 460pts, 3 篇文章
- [hive](https://github.com/aden-hive/hive) - HN 911pts, 4 篇文章
- [cli](https://github.com/googleworkspace/cli) - HN 8211pts, 4 篇文章
- [skills](https://github.com/trailofbits/skills) - HN 3264pts, 3 篇文章

---
*Claude Skills Scout v3 | 2026-04-03 | github.com*