# Skill Scout

Claude Skills 发现与推荐情报助手 — 自动搜索、评估和推荐优质 Claude Code Skills。

## 这是什么

Skill Scout 是一个 [Claude Code Skill](https://docs.anthropic.com/en/docs/claude-code/skills)，帮你从 GitHub、HN、中文科技媒体等多个信号源中挖掘**真正实用的隐藏宝石 Skills**，而不是大家都知道的官方仓库。

你只需要说：

- "帮我找好用的 skill"
- "有什么新 skill 推荐"
- "最近有什么好的 claude 插件"
- "推荐几个提升效率的 skill"
- "有没有整活的 skill"

Skill Scout 会自动执行多源搜索，生成一份交互式 HTML 发现报告。

## 安装

```bash
claude skill add --from github:yanyuliu01/skill-scout
```

或者手动将 `SKILL.md` 复制到 `~/.claude/skills/skill-scout/SKILL.md`。

## 功能特色

- **多源搜索** — GitHub 深度搜索、HN、Dev.to、中文科技媒体（卡尔的AI沃茨、向阳乔木、知乎、CSDN 等）
- **智能去重** — 自动记忆已推荐的 Skills，不重复推荐
- **分类体系** — C 端应用、开发者工具、整活/创意型、垂直行业四大分类
- **交互式报告** — 生成精美的 HTML 报告，可离线浏览
- **历史存档** — 自动保存每期报告，支持回溯查看

## 报告存档

| 期数 | 日期 | 新发现 | 分类 |
|------|------|--------|------|
| #002 | 2026-04-08 | 15 个 | 安全审计、自动化/Meta、高星精选、开发者工具、垂直行业 |
| #001 | 2026-04-03 | 8 个 | 开发者工具、C 端精选、整活/创意型、垂直行业 |

报告 HTML 文件存放在 [reports/](reports/) 目录下。

## 项目结构

```
skill-scout/
├── SKILL.md              # Skill 定义文件（核心）
└── reports/
    ├── index.json        # 报告索引
    ├── skill-scout-report-2026-04-03.html
    └── skill-scout-report-2026-04-08.html
```

## License

MIT
