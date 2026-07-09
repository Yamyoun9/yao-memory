"""
追溯面板 — 展示 memory-admin 的所有治理操作审计链。
用法: python audit_viewer.py [project_id]
"""

import sys
from pathlib import Path
from datetime import datetime


def find_audit_files(project_id: str) -> list[Path]:
    root = Path("E:/Users/86132/Desktop/OneDrive/同步知识库/EverOS/default_app")
    dir_name = "default_project" if project_id == "default" else project_id
    gov_dir = root / dir_name / "agents" / "memory-admin" / "governance" / "audit-trail"
    if not gov_dir.exists():
        return []
    return sorted(gov_dir.glob("audit-*.md"), reverse=True)


def parse_audit(filepath: Path) -> dict:
    """解析审计文件的 frontmatter"""
    text = filepath.read_text(encoding="utf-8")
    result = {
        "file": filepath.name,
        "size": filepath.stat().st_size,
    }
    in_frontmatter = False
    for line in text.split("\n"):
        line = line.strip()
        if line == "---":
            if in_frontmatter:
                break
            in_frontmatter = True
            continue
        if in_frontmatter and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"')
            if key in ("audit_id", "action", "operator", "project_id", "timestamp",
                       "input_ids", "output_ids"):
                result[key] = val
    return result


def show_trail(project_id: str):
    audit_files = find_audit_files(project_id)
    if not audit_files:
        print(f"项目 {project_id} 暂无治理审计记录")
        return

    # 也列出 insight 文件
    root = Path("E:/Users/86132/Desktop/OneDrive/同步知识库/EverOS/default_app")
    dir_name = "default_project" if project_id == "default" else project_id
    cases_dir = root / dir_name / "agents" / "memory-admin" / ".cases"
    insight_files = sorted(cases_dir.glob("project_insight-*.md"))
    # 也查 governance/project-insights/
    gov_insights = root / dir_name / "agents" / "memory-admin" / "governance" / "project-insights"
    if gov_insights.exists():
        insight_files.extend(sorted(gov_insights.glob("*.md")))

    print("=" * 70)
    print(f"  治理追溯面板 — {project_id}")
    print(f"  查询时间: {datetime.now().isoformat()[:19]}")
    print("=" * 70)
    print()
    print(f"  审计记录: {len(audit_files)} 条")
    print(f"  合并产物: {len(insight_files)} 个 project_insight")
    print()

    # 逐条展示
    for i, af in enumerate(audit_files, 1):
        audit = parse_audit(af)
        action = audit.get("action", "?")
        audit_id = audit.get("audit_id", "?")
        ts = audit.get("timestamp", "")[:19] if audit.get("timestamp") else "?"

        print(f"── 操作 #{i} ──")
        print(f"  审计ID:  {audit_id}")
        print(f"  类型:    {action}")
        print(f"  时间:    {ts}")
        print(f"  执行人:  {audit.get('operator', '?')}")

        # 输入
        input_ids = audit.get("input_ids", "[]")
        if input_ids and input_ids != "[]":
            import json
            try:
                ids = json.loads(input_ids)
                print(f"  输入:    {len(ids)} 条 agent_case")
                for cid in ids[:3]:
                    print(f"    ↳ {cid}")
                if len(ids) > 3:
                    print(f"    ↳ ... +{len(ids)-3} 条")
            except json.JSONDecodeError:
                print(f"  输入:    {input_ids[:80]}...")

        # 输出
        output_ids = audit.get("output_ids", "[]")
        if output_ids and output_ids != "[]":
            import json
            try:
                oids = json.loads(output_ids)
                print(f"  输出:    {len(oids)} 个文件")
                for oid in oids:
                    print(f"    ↳ {oid}")
            except json.JSONDecodeError:
                print(f"  输出:    {output_ids[:80]}...")

        # 审计文件位置
        print(f"  审计文件: agents/memory-admin/governance/audit-trail/{af.name}")
        print()

    # insight 产物清单
    if insight_files:
        print("── 合并产物 ──")
        for f in insight_files:
            size_kb = f.stat().st_size / 1024
            print(f"  📄 {f.name} ({size_kb:.1f} KB)")
            # 读 frontmatter 看 source
            text = f.read_text(encoding="utf-8")
            for line in text.split("\n")[:10]:
                if "source_case_ids" in line:
                    print(f"     来源: {line.split(':',1)[1].strip()[:80]}...")

    print()
    print("=" * 70)
    print("  如何追溯")
    print("=" * 70)
    print("  1. 按审计ID搜索 → 找到对应 audit 文件")
    print("  2. 查看 input_ids → 列出所有参与合并的原始 case")
    print("  3. 查看 output_ids → 找到合并后的 project_insight")
    print("  4. 如有疑问，删除 output 文件即可回滚")
    print("  5. 原始 agent_case 在对应 agent 的 .cases 目录，未被修改")
    print()
    print(f"  审计文件目录: agents/memory-admin/governance/audit-trail/")
    print(f"  insight目录: agents/memory-admin/governance/project-insights/")
    print(f"  巡检报告: agents/memory-admin/governance/巡检报告/")


if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "default"
    show_trail(pid)
