"""
project_insight 归档管理器。

project_insight 不写入 user 轨（避免污染个人记忆），
不写入 agent 轨（它不属于任何单个 agent）。
它是项目级的独立产物，存放于 governance/project-insights/。

访问方式：
  - 文件系统：governance/project-insights/*.md
  - 追溯面板：python audit_viewer.py <project>
  - 巡检报告：<project>/巡检报告-*.md
"""

from pathlib import Path
from datetime import datetime, timezone


def get_governance_dir(project_id: str) -> Path:
    """获取项目的 governance 目录（在 memory-admin agent 下）"""
    root = Path("E:/Users/86132/Desktop/OneDrive/同步知识库/EverOS/default_app")
    dir_name = "default_project" if project_id == "default" else project_id
    return root / dir_name / "agents" / "memory-admin" / "governance"


def list_project_insights(project_id: str = "default") -> list[Path]:
    """列出项目的所有 project_insight"""
    gov_dir = get_governance_dir(project_id)
    insights_dir = gov_dir / "project-insights"
    if not insights_dir.exists():
        return []
    return sorted(insights_dir.glob("project_insight-*.md"))


def list_audit_trail(project_id: str = "default") -> list[Path]:
    """列出项目的所有审计记录"""
    gov_dir = get_governance_dir(project_id)
    audit_dir = gov_dir / "audit-trail"
    if not audit_dir.exists():
        return []
    return sorted(audit_dir.glob("audit-*.md"))


if __name__ == "__main__":
    for pid in ["default", "risk-monitor"]:
        insights = list_project_insights(pid)
        audits = list_audit_trail(pid)
        if insights or audits:
            print(f"项目 {pid}:")
            print(f"  project_insights: {len(insights)} 个")
            for f in insights:
                print(f"    {f.name}")
            print(f"  audit_trail: {len(audits)} 条")
            for f in audits:
                print(f"    {f.name}")
            print()
