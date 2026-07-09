# Multi-Agent 协作指南

## 为什么需要 Multi-Agent 协作

单个 Agent 可以完成独立任务，但复杂项目需要**分工**：前端、后端、运维各司其职。

传统方式是 Agent 之间发消息传递上下文，但：
- ❌ Agent 忘发消息 → 上下文丢失
- ❌ 消息只传摘要 → 丢失完整执行细节
- ❌ 新 Agent 加入 → 无从获取历史经验

EverOS 的方式：每个 Agent 把自己的完整执行过程写入共享记忆，其他 Agent **按需检索**。

## 协作模式

```
┌──────────────┐     写入记忆     ┌──────────────┐
│ Agent A(前端) │ ──────────────→ │   EverOS     │
└──────────────┘                  │              │
                                  │  agent_case  │ ←── 项目共享知识
┌──────────────┐     写入记忆     │  (memory-    │     (memory-admin
│ Agent B(后端) │ ──────────────→ │   admin轨)   │      合并后的)
└──────────────┘                  └──────┬───────┘
                                        │
┌──────────────┐     搜索共享知识       │
│ Agent C(审查) │ ←─────────────────────┘
└──────────────┘
```

### 步骤 1：启动前自检

每个 Agent 开始任务前，搜索自己的历史和项目共享知识：

```
POST /search agent_id=<自己> project_id=<项目> query="<任务关键词>"
POST /search agent_id=memory-admin project_id=<项目> query="项目共享"
```

### 步骤 2：执行任务

正常执行任务，记录完整的工具调用链、踩坑过程、解决方案。

### 步骤 3：写回记忆

任务完成后，将完整对话写入 EverOS 的 agent 轨：

```bash
POST /add   →  写入缓冲区
POST /flush →  触发 OME 提取 agent_case
```

### 步骤 4：管理员巡检

memory-admin 定期扫描所有 agent_case：
- 发现重复 → 合并
- 发现互补 → 关联
- 升级为项目共享知识

## 实际案例：风险舆情监控系统

### Agent 分工

| Agent | 职责 |
|---|---|
| risk-frontend | 搭建前端（React + ECharts 大屏） |
| risk-backend | 搭建后端（FastAPI + Kafka 采集） |
| risk-ops | 部署运维（K8s + Prometheus） |
| risk-review | 代码审查（安全 + 性能） |
| memory-admin（内置） | 记忆治理 |

### 协作流程

1. **risk-backend** 完成 API 设计，agent_case 记录：踩了 Kafka 配置的坑（consumer group offset reset）
2. **risk-frontend** 完成大屏开发，agent_case 记录：ECharts React18 StrictMode 双重渲染的坑
3. **memory-admin** 巡检发现：
   - risk-frontend 和 risk-review 都提到了 ECharts 性能问题 → 合并为 project_insight
   - risk-backend 的 API 设计被 risk-review 标记了 XSS 风险 → 补充关联
4. **新加入的 Agent** 搜索 "ECharts 性能" → 直接命中合并后的最佳实践，不用翻两条原始 case

## 权限模型

```
owner_id 隔离：Agent A 看不到 Agent B 的 agent_case（默认）
    ↓ 叠加
global_view：memory-admin 可以看所有 agent 的 agent_case
    ↓ 叠加
默认所有 agent 都有 global_view → 所有人都能看到项目共享知识
```

## 快速验证

```bash
# 用任意 Agent 搜项目共享知识
python -c "
import httpx, asyncio
async def test():
    async with httpx.AsyncClient() as c:
        r = await c.post('http://127.0.0.1:8000/api/v1/memory/search', json={
            'agent_id': 'risk-frontend', 'project_id': 'risk-monitor',
            'query': 'ECharts 性能 优化', 'top_k': 5, 'method': 'keyword'
        })
        for case in r.json()['data']['agent_cases']:
            print(f'[{case[\"agent_id\"]}] {case[\"task_intent\"][:60]}')

asyncio.run(test())
"
```
