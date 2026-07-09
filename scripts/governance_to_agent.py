"""
将 project_insight 写入 memory-admin 的 agent 轨 agent_case 格式，
使其被 cascade 索引后，所有开 global_view 的 agent 都可检索。
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def write_insight_as_agent_case(insight_file: str | Path) -> bool:
    """
    把 project_insight markdown 转化为 memory-admin 的 agent_case entry，
    写入 .cases/agent_case-YYYY-MM-DD.md。
    """
    fpath = Path(insight_file)
    if not fpath.exists():
        print(f"  ❌ 文件不存在: {fpath}")
        return False

    raw = fpath.read_text(encoding="utf-8")

    # 解析 frontmatter
    frontmatter = {}
    body_start = 0
    in_fm = False
    for i, line in enumerate(raw.split("\n")):
        if line.strip() == "---":
            if i == 0:
                in_fm = True
                continue
            elif in_fm:
                body_start = i + 1
                break
        if in_fm and ":" in line:
            k, _, v = line.partition(":")
            frontmatter[k.strip()] = v.strip().strip('"')

    body = "\n".join(raw.split("\n")[body_start:]) if body_start else raw
    topic = frontmatter.get("topic", "项目共享知识")
    source_ids = frontmatter.get("source_case_ids", "[]")
    case_count = frontmatter.get("case_count", "1")
    avg_quality = frontmatter.get("avg_quality", "1.0")

    try:
        source_list = json.loads(source_ids) if isinstance(source_ids, str) else source_ids
    except (json.JSONDecodeError, TypeError):
        source_list = []

    # 构建 agent_case entry
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    ts = now.isoformat()
    seq = now.strftime("%Y%m%d_%H%M%S")

    # 目标文件
    cases_dir = Path(
        "E:/Users/86132/Desktop/OneDrive/同步知识库/EverOS"
        "/default_app/default_project/agents/memory-admin/.cases"
    )
    cases_dir.mkdir(parents=True, exist_ok=True)
    case_file = cases_dir / f"agent_case-{today}.md"

    entry_id = f"ac_{today.replace('-', '')}_pi{seq[-4:]}"

    # 构建每条 insight 的简短 Approach（因为是合并产物，不是执行过程）
    approach_lines = [f"治理操作：将 {case_count} 条 agent_case 合并为项目共享知识。"]
    approach_lines.append(f"来源 case: {', '.join(source_list[:5])}")
    if len(source_list) > 5:
        approach_lines.append(f"  ... 共 {len(source_list)} 条")
    approach_lines.append("")
    approach_lines.append("合并策略：主题聚类 → 关键洞察提取 → 合并 → 审计留痕")
    approach_lines.append(f"审计记录：audit-MERGE-*.md（存放在 governance/audit-trail/）")
    approach_lines.append(f"回滚方式：删除本 agent_case 及对应 project_insight 文件即可还原")
    approach = "\n".join(approach_lines)

    # TaskIntent：说清楚这不是原始任务执行，是治理合并
    task_intent = f"[项目共享记忆] {topic} — 来自 {case_count} 条 agent_case 的合并精华"

    # 提取关键洞察
    body_lines = body.split("\n")
    insights_found = []
    in_insight_section = False
    for line in body_lines:
        if "合并后经验" in line or "### 合并后" in line:
            in_insight_section = True
            continue
        if in_insight_section and line.strip().startswith("#"):
            break
        if in_insight_section and line.strip().startswith("- ") and len(line) > 5:
            insights_found.append(line.strip()[2:])

    key_insight = "；".join(insights_found[:3]) if insights_found else f"项目共享知识：{topic}（合并 {case_count} 条原始经验）"

    # 文件 frontmatter
    if not case_file.exists():
        with open(case_file, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f"id: agent_case_log_memory-admin_{today}\n")
            f.write("type: agent_case_daily\n")
            f.write("file_type: agent_case_daily\n")
            f.write("schema_version: 1\n")
            f.write("agent_id: memory-admin\n")
            f.write("track: agent\n")
            f.write(f"date: '{today}'\n")
            f.write("entry_count: 0\n")
            f.write(f"last_appended_at: '{ts}'\n")
            f.write("---\n\n")

    # 追加 entry
    entry_text = f"""<!-- entry:{entry_id} -->
## {entry_id}

**owner_id**: memory-admin
**session_id**: governance-{entry_id}
**timestamp**: {ts}
**parent_type**: project_insight
**parent_id**: {entry_id}
**quality_score**: {avg_quality}

### TaskIntent
{task_intent}

### Approach
{approach}

### KeyInsight
{key_insight}
<!-- /entry:{entry_id} -->

"""
    with open(case_file, "a", encoding="utf-8") as f:
        f.write(entry_text)

    # 更新 entry_count
    content = case_file.read_text(encoding="utf-8")
    count = content.count("<!-- entry:")
    content = content.replace("entry_count: 0", f"entry_count: {count}")
    case_file.write_text(content, encoding="utf-8")

    # touch 触发 cascade
    case_file.touch()

    return True


def main():
    insights_dir = Path(
        "E:/Users/86132/Desktop/OneDrive/同步知识库/EverOS"
        "/default_app/default_project/agents/memory-admin/governance/project-insights"
    )
    if not insights_dir.exists():
        print("insights 目录不存在")
        return

    for f in sorted(insights_dir.glob("project_insight-*.md")):
        ok = write_insight_as_agent_case(f)
        if ok:
            print(f"  ✅ {f.name} → memory-admin agent_case")


if __name__ == "__main__":
    main()
