# EverOS Memory Admin

> 让 AI Agent 拥有项目记忆、团队协作和知识治理能力的一站式系统。

## 这是什么

一个基于 [EverOS](https://github.com/ever-os/everos) 的记忆管理中台。你可以把它部署在本地，让你的 Codex / WorkBuddy / Hermes 等 AI Agent 获得：

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
everos-memory-admin/
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

## 架构

```
┌─────────────── 用户 ───────────────┐
│  Codex / WorkBuddy / Hermes         │
└──────────┬──────────────────────────┘
           │ 对话写入
┌──────────▼──────────────────────────┐
│            EverOS                    │
│  ┌────────┐  ┌────────┐            │
│  │user 轨 │  │agent 轨│ 双轨隔离    │
│  └────────┘  └────────┘            │
│       │            │                │
│  ┌────▼─────┐  ┌──▼──────────┐     │
│  │episode   │  │agent_case   │     │
│  │atomic_fact│ │agent_skill  │     │
│  └──────────┘  │project_insight│   │
│                └──────────────┘     │
└─────────────────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│       Memory-Admin 治理层            │
│  ┌────────┐ ┌──────┐ ┌──────────┐  │
│  │ 巡检   │ │ 去重 │ │ 升级共享 │  │
│  └────────┘ └──────┘ └──────────┘  │
│  ┌────────────────────────────────┐ │
│  │        审计追溯链              │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## License

MIT
