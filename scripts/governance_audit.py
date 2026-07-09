"""
治理操作审计记录格式 & 写入器

每条治理操作生成一条审计记录，写入 memory-admin 的 agent_case 轨，
形成可追溯的不可变审计链。

审计记录类型：
  - MERGE: 多条 agent_case 合并为 project_insight
  - FLAG: 标记低质量记忆
  - SUPPLEMENT: 跨 agent 补充
  - UPGRADE: 升级为项目共享知识
"""

from __future__ import annotations

import json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx

GovernanceAction = Literal["MERGE", "FLAG", "SUPPLEMENT", "UPGRADE"]


class AuditTrail:
    """一条不可变的治理操作审计记录"""

    def __init__(
        self,
        action: GovernanceAction,
        project_id: str,
        operator: str = "memory-admin",
    ):
        self.action = action
        self.project_id = project_id
        self.operator = operator
        self.timestamp = datetime.now(timezone.utc)
        self.audit_id = self._gen_id()

        # 审计字段
        self.input_ids: list[str] = []       # 操作前的记录 ID
        self.input_summary: str = ""          # 操作前状态摘要
        self.output_ids: list[str] = []       # 操作后的记录 ID
        self.output_summary: str = ""          # 操作后状态摘要
        self.reason: str = ""                  # 操作理由
        self.diff: str = ""                    # 变更详情

    def _gen_id(self) -> str:
        raw = f"{self.action}-{self.project_id}-{self.timestamp.isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_markdown(self) -> str:
        """生成人类可读的审计记录"""
        return f"""---
audit_id: {self.audit_id}
action: {self.action}
operator: {self.operator}
project_id: {self.project_id}
timestamp: {self.timestamp.isoformat()}
input_ids: {json.dumps(self.input_ids)}
output_ids: {json.dumps(self.output_ids)}
---

# 治理审计记录

- **操作类型**: {self.action}
- **执行人**: {self.operator}
- **时间**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
- **项目**: {self.project_id}

## 操作前状态
{self.input_summary}

## 操作理由
{self.reason}

## 变更详情
{self.diff}

## 操作后状态
{self.output_summary}

## 回滚信息
- 输入记录: {', '.join(self.input_ids[:5])}...（共{len(self.input_ids)}条）
- 输出记录: {', '.join(self.output_ids)}
- 回滚方式: 删除输出记录即可还原（输入记录未被修改/删除）
"""

    def to_agent_case_payload(self) -> dict:
        """转为 EverOS /add API 的 payload"""
        content = self.to_markdown()
        return {
            "app_id": "default",
            "project_id": self.project_id,
            "session_id": f"governance-audit-{self.audit_id}",
            "sender_id": self.operator,
            "sender_name": "记忆管理员",
            "messages": [
                {
                    "role": "user",
                    "content": f"执行治理操作: {self.action} (审计ID: {self.audit_id})"
                },
                {
                    "role": "assistant",
                    "content": content,
                },
            ],
        }


async def write_audit_to_everos(audit: AuditTrail, everos_url: str = "http://127.0.0.1:8000") -> dict:
    """将审计记录写入 EverOS agent 轨"""
    payload = audit.to_agent_case_payload()
    async with httpx.AsyncClient(timeout=30) as c:
        resp = await c.post(f"{everos_url}/api/v1/memory/add", json=payload)
        add_data = resp.json()
        sid = add_data.get("session_id", payload["session_id"])

        resp2 = await c.post(f"{everos_url}/api/v1/memory/flush", json={
            "session_id": sid,
            "app_id": "default",
            "project_id": audit.project_id,
        })
        flush_data = resp2.json()
        return {
            "audit_id": audit.audit_id,
            "session_id": sid,
            "flush_status": flush_data.get("data", {}).get("status", "queued"),
        }


def write_audit_to_md(audit: AuditTrail, memory_root: Path) -> Path:
    """将审计记录写入 memory-admin 的 .cases 目录（兜底，确保一定落盘）。

    project_id 到目录名的映射：'default' → 'default_project'，其他不变。
    """
    # 目录名映射
    dir_name = "default_project" if audit.project_id == "default" else audit.project_id
    cases_dir = memory_root / dir_name / "agents" / "memory-admin" / ".cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    filename = f"audit-{audit.action}-{audit.audit_id}.md"
    filepath = cases_dir / filename
    filepath.write_text(audit.to_markdown(), encoding="utf-8")
    return filepath


def build_merge_audit(
    topic: str,
    input_cases: list[dict],
    output_insight_path: str,
    project_id: str,
) -> AuditTrail:
    """为合并操作构建审计记录"""
    audit = AuditTrail("MERGE", project_id)

    # 输入
    audit.input_ids = [c["id"] for c in input_cases]
    audit.input_summary = f"""主题: {topic}
原始记录: {len(input_cases)} 条 agent_case
涉及 agent: {list(set(c['agent_id'] for c in input_cases))}
平均质量: {sum(c['quality_score'] for c in input_cases) / len(input_cases):.2f}
"""

    # 输出
    audit.output_ids = [output_insight_path]
    audit.output_summary = f"""产出: 1 个 project_insight
文件: {output_insight_path}
原始 case 已保留，仅标记为已合并。
"""

    # 理由
    overlap_keywords = set()
    for c in input_cases:
        for w in c.get("task_intent", "").split():
            overlap_keywords.add(w.lower())
    audit.reason = f"""主题聚类发现 {len(input_cases)} 条 agent_case 涉及同一主题"{topic}"。
关键词重叠度高，且关键洞察（key_insight）可互补。合并后新 agent 可直接查阅合并经验，无需遍历所有原始 case。"""

    # 变更
    audit.diff = f"""### 输入 → 输出
- {len(input_cases)} 条 agent_case → 1 个 project_insight
- 原始 case 状态: 保留（不可变）
- 合并后: 新增 project_insight，source_case_ids 记录来源
- 无数据删除，无覆盖写入
"""

    return audit
