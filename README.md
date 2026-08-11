# yao-memory：跨 Agent 长期记忆系统

> 让 AI Agent 拥有项目记忆、团队协作和知识治理能力的一站式系统。

## 这是什么

一个记忆管理中台。你可以把它部署在本地，让你的 Codex / WorkBuddy / Hermes 等 AI Agent 获得：

- **双轨记忆** — user 轨（个人对话经验）+ agent 轨（任务执行经验），物理隔离
- **Multi-Agent 协作** — 多个 agent 通过共享记忆空间协同工作，不需要互相发消息
- **记忆管理员** — 自动巡检、去重、合并、升级项目经验为共享知识
- **治理审计链** — 每条治理操作可追溯、可回滚
- **项目级隔离** — 不同项目记忆空间独立，default 项目作为全局中枢

## 5 分钟快速开始

### 前提

- Python 3.10+
- 已安装 EverOS（`pip install everos` 或源码启动）
- 至少一个 LLM API Key（阿里百联 / DeepSeek / OpenAI）

### 安装

```bash
git clone https://github.com/your-org/everos-memory-admin.git
cd everos-memory-admin
python install.py
```

`install.py` 会引导你完成：
1. 连接 EverOS 服务
2. 创建默认项目空间
3. 初始化 memory-admin agent
4. 授权所有 agent 全局视野
5. 生成第一个 agent 模板

### 验证

```bash
# 查看项目总览
python scripts/project_status.py default

# 执行记忆治理
python scripts/governance_exec.py

# 查看审计追溯
python scripts/audit_viewer.py default
```

## 目录结构

```
yao-memory-admin/
├── README.md
├── install.py              ← 一键安装向导
├── everos/
│   ├── everos.toml          ← EverOS 配置模板
│   └── ome.toml             ← OME 策略配置
├── agents/
│   ├── memory-admin/        ← 记忆管理员（项目自动创建）
│   │   ├── AGENTS.md         ← 角色 + 工作规则
│   │   └── SKILL.md          ← 可安装给 Codex/WorkBuddy 的 Skill
│   └── agent-template/      ← 新建 agent 的模板
│       └── AGENTS.md.template
├── scripts/
│   ├── governance_exec.py   ← 治理执行（巡检→去重→合并）
│   ├── governance_audit.py  ← 审计模块
│   ├── audit_viewer.py      ← 追溯面板
│   ├── project_status.py    ← 项目总览
│   └── project_setup.py     ← 新建项目脚手架
├── src/                     ← 源码 Patch（权限治理、跨项目）
│   ├── permissions.py
│   ├── admin_routes.py
│   └── cross_project.patch
└── docs/
    ├── 快速开始.md
    ├── 架构说明.md
    ├── Multi-Agent-协作指南.md
    └── 常见问题.md
```

## 在 Codex / WorkBuddy 中使用

将 `agents/memory-admin/SKILL.md` 安装为 Skill，此后在你的 agent 对话中：

```
> 执行治理巡检
→ memory-admin 自动巡检、去重、产出报告

> 帮我新建一个 Agent
→ 自动创建 agent 目录、授权、写入模板
```

## 系统架构

### 一、全链路写入管道

```
Codex Agent 对话
      │
      ▼
  消息缓冲层（内存 + SQLite）
      │  接收 role=user/assistant 的原始对话流
      │  按 session_id 分组，去重排序
      ▼
  LLM 边界检测
      │  将长对话切分为 MemCell（对话单元）
      │  不是按字数/时间切，而是 LLM 语义理解"这里话题换了"
      │  Chat 模式看 user+assistant，Agent 模式保留 tool_calls 完整链路
      │  最多重试 3 次，JSON 解析失败自动容错
      ▼
  ┌──────────────────────────────────────────────┐
  │              OME 双轨提取引擎                 │
  │                                              │
  │  User 轨（同步）         Agent 轨（异步）      │
  │  ─────────────          ─────────────         │
  │  Episode 提取 (LLM)      AgentPipeline fire   │
  │  Subject + Summary        -and-forget         │
  │  + Content 叙事               │               │
  │       │                 extract_agent_case    │
  │  中文 prompt 优化         (LLM，离线策略)       │
  │       │                 TaskIntent + Approach  │
  │  episodes/*.md           + KeyInsight         │
  │  + OKF 元数据字段             │               │
  │  + 同步 OKF 导出         .cases/*.md          │
  │                          + OKF 元数据字段      │
  │                          + 异步 OKF 导出       │
  └──────────────────────────────────────────────┘
      │
      ▼
  Cascade 索引层（后台守护进程）
      │  Watcher: watchdog 实时文件监控
      │  Scanner: 每 30s 全量扫描兜底
      │  Worker:  读 md → diff 内容 → embed 向量 + tokenize 全文
      │           → 写入 LanceDB（向量搜索 + BM25 全文检索）
      ▼
  可搜索记忆库（实时可用）
```

### 二、双轨记忆模型

yao-memory 的核心创新在于**将"用户说了什么"和"Agent 做了什么"完全解耦**：

| 维度   | User 轨                                   | Agent 轨                       |
| ---- | ---------------------------------------- | ----------------------------- |
| 记录内容 | 对话语义、用户意图、决策变化                           | 任务意图、执行方法、关键洞察                |
| 写入实体 | Episode（对话叙事）                            | AgentCase（任务记录）               |
| 存储路径 | `users/<uid>/episodes/`                  | `agents/<aid>/.cases/`        |
| 搜索范围 | 用户对话历史                                   | Agent 执行经验                    |
| 下游产出 | atomic_facts + foresights + user_profile | agent_skill + project_insight |
| 提取时机 | /flush 时同步                               | /flush 后异步（fire-and-forget）   |

**设计目的**：Agent 搜索"怎么写反贿赂政策"时，不会被用户闲聊记录污染；用户回顾"上周讨论了哪些 ESG 要点"时，不会被 Agent 的工具调用日志干扰。

### 三、文件系统 → 向量索引的实时同步

Cascade 层是一个独立的后台守护进程，三组件并行工作确保记忆"写了就能搜"：

1. **Watcher**（watchdog 实时监听）：文件创建/修改/删除事件 → SQLite 变更队列
2. **Scanner**（每 30s 兜底扫描）：全量 glob 遍历 → 与已知状态对比 → 捕获 watcher 漏掉的事件
3. **Worker**（队列消费者）：领用 pending 行 → 按 kind 分派 handler → 解析 md → 对每个 entry 做 content_sha256 diff → 只处理变化的 entry → embed 向量 + BM25 tokenize → 写入 LanceDB → 定期 optimize 合并索引

**关键设计**：文件系统是唯一的真相源。LanceDB 是从 md 文件重建的，不存储独立状态。文件删了，索引就删了。这保证了任何外部工具直接编辑 md 文件，Cascade 都能正确同步。

---

## 治理管道（governance）

yao-memory 不仅仅是"记住"，更是"记住之后能管"。治理层是一个可独立运行的五步管道：

### [1/5] 全量拉取

通过向量搜索 API 分多关键词拉取全量 agent_case，合并去重。不用直接读文件的原因：LanceDB 已做好去重和向量排序，比 grep md 文件更快更准。

### [2/5] Cross-Model 交叉质量审核

这是 yao-memory 对 AI 记忆质量的独特创新：

- 原始记忆提取时 LLM 会自评 `quality_score`，但自评天然偏高（实测 0.95-1.0，无区分度）
- 治理层用**两个完全独立的 LLM 模型**重新打分：
  - **Qwen2.5-7B**（硅基流动）：小模型，严谨苛刻，专门捕捉"内容空泛""洞察无价值"的 case
  - **DeepSeek-V3**（硅基流动）：大模型，稳健全面，确保不误杀高质量产出
- 取两个模型的**较低分**作为最终判断
- `is_badcase` 判定完全交给 LLM 语义判断，不设硬性分数门槛——因为"bad"的定义是语义性的，无法量化

**为什么不用 OME 自评分？** 自评是给搜索排序用的近似信号，交叉审核才是给质量淘汰用的精准判定。两者职责不同，分层共存。

### [3/5] 主题聚类 — 排除 badcase

被标记的 badcase 不参与后续聚类和合并。不删除——标记 `deprecated_by` 后保留在搜索中可查，但不污染共享知识。删除该行即可回滚。

### [4/5] 合并去重 + 审计留痕

同主题 >=2 条 agent_case 合并为 1 条 `project_insight`（项目共享知识）。多个 Agent 重复探索同一个问题 → 系统自动合并精华 → 新 Agent 直接读取，不再重复踩坑。

每次合并操作都生成审计记录：`audit_id` + 时间戳 + 原始 case 列表 + 合并结果路径 + 回滚方法。

### [5/5] OKF 分轨导出

将 user 轨、agent 轨、治理产出分别导出为 OKF v0.1 标准格式。user/agent/governance 三轨独立目录，与原始数据同级并列，可被 Google OKF Visualizer 等外部工具直接消费。

---

## OKF v0.1 标准

yao-memory 定义了 OKF (Open Knowledge Format) v0.1 作为 Agent 记忆的通用交换格式：

```yaml
---
title: "中国石油天然气集团 (CNPC) ESG 档案"
type: entity-profile
description: "CNPC ESG 关键绩效：碳排放 1.87 亿吨，甲烷强度 0.27%"
tags: [能源央企, CNPC, 碳排放, 甲烷, 供应链ESG]
resource: reports/CNPC-2024-ESG-Report.pdf
okf_version: v0.1
updated: 2026-08-11T12:00:00+00:00
---
```

**OKF 的价值**：将 Codex 产出的记忆从"特定项目的 md 文件"提升为"可被任何 OKF consumer 消费的通用知识资产"。Google Visualizer、其他 AI Agent、人类知识管理工具都可以直接读取和索引。

已实现 OKF 对齐的产出类型：

- `conversation-episode`：user 轨对话记忆
- `agent-case`：agent 轨执行经验
- `project-insight`：治理层合并后的项目共享知识
- `entity-profile`、`concept`、`methodology` 等：静态知识库类型

---

## Badcase 管理与审计追溯

yao-memory 对记忆质量有完整的审计闭环：

### 决策链追溯

每条被标记的 badcase 生成独立的审计文件：

```markdown
---
audit_id: bc-1750000000-a1b2c3
type: badcase_mark
timestamp: 2026-08-11T08:00:00+00:00
---

## 审计决策链

| 步骤 | 模型 | 分数 | badcase | 理由 |
|------|------|------|---------|------|
| 1. 原始提取 | — | 0.95 | — | 自评 |
| 2. 交叉评估 | Qwen2.5-7B | 0.5 | true | 方法空泛 |
| 2. 交叉评估 | DeepSeek-V3 | 0.6 | true | 洞察不足 |
| 最终判定 | 交叉取低 | 0.5 | true | 双模型一致 |
```

### 可回滚设计

badcase 标记通过在原文件中写入 `**deprecated_by**` 行实现。删除该行即恢复。不涉及数据删除，不留不可逆操作。

### badcase 库积累

所有 badcase 集中在 `governance/badcase/` 目录，附带 `index.md` 汇总索引和完整审计文件。支持人工复核流程：确认 → 标记完成 / 误标 → 移入 golden case / 内容待补 → 返回修改。

---

## 目录结构

```
project/
├── users/<uid>/                  ← User 轨
│   ├── episodes/                  ← 原始 episode（Subject/Summary/Content）
│   ├── okf/                       ← OKF 导出
│   ├── .atomic_facts/             ← 原子事实
│   ├── .foresights/               ← 前瞻洞察
│   └── user.md                    ← 用户画像
│
├── agents/<aid>/                  ← Agent 轨
│   ├── .cases/                    ← 原始 agent_case（TaskIntent/Approach/KeyInsight）
│   ├── okf/                       ← OKF 导出
│   ├── skills/                    ← Agent 技能聚类
│   └── governance/                ← 治理产出
│       ├── quality-review/        ← 双模型交叉审核报告
│       ├── badcase/               ← badcase 库（审计文件 + index.md）
│       ├── audit-trail/           ← 合并操作审计记录
│       ├── project-insights/       ← 项目共享知识
│       └── okf/                   ← 治理层 OKF 导出
│
└── memory-meta/                   ← 治理脚本
    ├── governance_exec.py         ← 治理主流程
    ├── quality_review.py          ← 交叉质量审核
    ├── governance_audit.py        ← 审计留痕
    └── okf_export.py              ← OKF 分轨导出
```

---


## License

MIT
