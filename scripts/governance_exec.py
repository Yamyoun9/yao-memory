"""
memory-admin 治理执行脚本 — 巡检 + 去重 + 补充 + 升级，每步带审计留痕。
对 default 项目的 agent_case 进行：
  1. 主题聚类 → 发现重复/互补 → 合并为 project_insight
  2. 生成审计记录 → 可追溯、可回滚
  3. 更新巡检报告
"""

import httpx, asyncio, json
from datetime import datetime, timezone
from pathlib import Path
from governance_audit import AuditTrail, build_merge_audit, write_audit_to_md


async def fetch_all_cases() -> list[dict]:
    """管理员全局视角拉取所有 agent_case"""
    async with httpx.AsyncClient(timeout=60) as c:
        # 分多次拉取，覆盖不同主题
        all_cases = {}
        queries = [
            'CSA 政策 制度 文件 起草',
            'ESG 方法学 证据 标注',
            '归档 留痕 文件 管理',
            '反贿赂 反腐败 合规 净化',
            '供应商 供应链 格式化',
        ]
        for q in queries:
            r = await c.post('http://127.0.0.1:8000/api/v1/memory/search', json={
                'agent_id': 'memory-admin', 'project_id': 'default',
                'query': q, 'top_k': 20, 'method': 'keyword'
            })
            for case in r.json()['data']['agent_cases']:
                all_cases[case['id']] = case

        r2 = await c.post('http://127.0.0.1:8000/api/v1/memory/search', json={
            'agent_id': 'memory-admin', 'project_id': 'default',
            'query': 'CSA ESG 政策 制度', 'top_k': 20, 'method': 'keyword'
        })
        for skill in r2.json()['data']['agent_skills']:
            all_cases.setdefault(f"skill_{skill['id']}", skill)

        return list(all_cases.values())


def cluster_by_topic(cases: list[dict]) -> dict[str, list[dict]]:
    """按主题聚类 agent_case"""
    topics = {
        '政策文件起草与纯化': [],
        'CSA方法学对齐与证据标注': [],
        '文件归档与版本管理': [],
        '格式规范与文档生成': [],
        'ESG承诺验证与命名': [],
        '知识库结构与路径管理': [],
        '其他': [],
    }

    rules = [
        ('政策文件起草与纯化', ['反贿赂', '反腐败', '政策', 'Policy', '制度', '草案', 'revised', 'purif', '净化']),
        ('CSA方法学对齐与证据标注', ['CSA', 'Methodology', '证据', 'evidence', '方法学', '标注', 'highlight']),
        ('文件归档与版本管理', ['归档', 'archiv', '版本', 'version', 'copy', 'hash', 'SHA']),
        ('格式规范与文档生成', ['格式', 'format', '字体', 'font', 'word', 'docx', '排版', '生成']),
        ('ESG承诺验证与命名', ['ESG', '承诺', 'commitment', 'naming', '命名', '验证', '净零']),
        ('知识库结构与路径管理', ['知识库', '目录', '路径', 'path', 'Unicode', '结构']),
    ]

    for case in cases:
        if 'task_intent' not in case:
            continue  # 跳过非 agent_case（如 skill）
        text = (case['task_intent'] + case.get('approach', '')).lower()
        matched = False
        for topic, keywords in rules:
            if any(k.lower() in text for k in keywords):
                topics[topic].append(case)
                matched = True
                break
        if not matched:
            topics['其他'].append(case)

    return {k: v for k, v in topics.items() if v}


def consolidate_topic(topic: str, cases: list[dict]) -> dict:
    """将一个主题下的多条 case 合并为 project_insight"""
    agent_ids = list(set(c['agent_id'] for c in cases))
    case_ids = [c['id'] for c in cases]
    avg_quality = sum(c['quality_score'] for c in cases) / len(cases)

    # 提取所有 key_insight
    insights = [c.get('key_insight', '') for c in cases if c.get('key_insight')]
    pitfalls = []
    for c in cases:
        approach = c.get('approach', '')
        if 'failed' in approach.lower() or '错误' in approach or '坑' in approach or 'error' in approach.lower():
            pitfalls.append(approach[:200])

    # 合成 project_insight
    title = f"[项目共享] {topic}最佳实践"
    content = f"""## 项目级经验合并：{topic}

### 来源
- 涉及 agent: {', '.join(agent_ids)}
- 涉及 case: {', '.join(case_ids[-5:])}（共 {len(case_ids)} 条）
- 平均质量评分: {avg_quality:.2f}

### 合并后经验
"""
    for ins in insights:
        content += f"- {ins}\n"

    if pitfalls:
        content += "\n### 共同踩过的坑\n"
        for i, p in enumerate(pitfalls[:3], 1):
            content += f"{i}. {p[:150]}...\n"

    content += f"""
### 治理操作
- 操作类型: 合并去重
- 执行人: memory-admin
- 时间: {datetime.now(timezone.utc).isoformat()}
- 原始 case 保留（不可删除，仅标记已合并）
"""

    return {
        "title": title,
        "topic": topic,
        "case_count": len(case_ids),
        "avg_quality": avg_quality,
        "content": content,
        "source_case_ids": case_ids[-5:],
    }


async def write_insight_to_md(insight: dict):
    """将 project_insight 写入 memory-admin 的 .cases 目录"""
    from pathlib import Path
    root = Path("E:/Users/86132/Desktop/OneDrive/同步知识库/EverOS/default_app/default_project/agents/memory-admin/.cases")
    root.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    safe_topic = insight['topic'].replace('/', '-').replace(':', '-')[:30]
    filename = f"project_insight-{safe_topic}-{now.strftime('%Y%m%d-%H%M%S')}.md"
    filepath = root / filename

    content = f"""---
agent_id: memory-admin
type: project_insight
topic: {insight['topic']}
source_case_ids: {json.dumps(insight['source_case_ids'])}
case_count: {insight['case_count']}
avg_quality: {insight['avg_quality']}
created_at: {now.isoformat()}
---

# {insight['title']}

{insight['content']}
"""
    filepath.write_text(content, encoding='utf-8')
    return str(filepath)


async def main():
    print("=" * 60)
    print("  memory-admin 治理执行")
    print("=" * 60)

    # 1. 拉取数据
    print("\n[1/4] 拉取全部 agent_case...")
    cases = await fetch_all_cases()
    actual_cases = [c for c in cases if not c.get('id', '').startswith('skill_')]
    print(f"  共 {len(actual_cases)} 条 agent_case")

    # 2. 主题聚类
    print("\n[2/4] 主题聚类...")
    clusters = cluster_by_topic(cases)
    for topic, cs in clusters.items():
        print(f"  {topic}: {len(cs)} 条")

    # 3. 合并去重 → project_insight + 审计记录
    print("\n[3/4] 合并去重 + 审计留痕...")
    produced = []
    memory_root = Path("E:/Users/86132/Desktop/OneDrive/同步知识库/EverOS/default_app")
    for topic, cs in clusters.items():
        if len(cs) >= 2:  # 只有 >=2 条的才需要合并
            insight = consolidate_topic(topic, cs)
            path = await write_insight_to_md(insight)

            # 生成审计记录
            audit = build_merge_audit(topic, cs, path, "default")
            audit_path = write_audit_to_md(audit, memory_root)

            produced.append((topic, insight, path, audit))
            print(f"  ✅ {topic}: {len(cs)}条 → 1个 project_insight")
            print(f"     insight: {Path(path).name}")
            print(f"     audit:   {audit_path.name}")
        elif len(cs) == 1:
            print(f"  ⏭ {topic}: 仅1条，跳过合并")
        else:
            print(f"  ⏭ {topic}: 0条")

    # 4. 产出执行摘要
    print("\n[4/4] 执行摘要")
    print(f"  输入: {len(actual_cases)} 条 agent_case")
    print(f"  聚类: {len(clusters)} 个主题")
    print(f"  产出: {len(produced)} 个 project_insight + {len(produced)} 条审计记录")
    print()

    for topic, insight, path, audit in produced:
        print(f"  📄 {insight['title']}")
        print(f"     合并 {insight['case_count']} 条 case, 质量 {insight['avg_quality']:.2f}")
        print(f"     审计ID: {audit.audit_id} (audit-{audit.action}-{audit.audit_id}.md)")
        print(f"     回滚: 删除 {Path(path).name} 即可还原")
        print()

    # 更新巡检报告
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    report_path = Path("E:/Users/86132/Desktop/OneDrive/同步知识库/EverOS/default_app/default_project/agents/memory-admin/governance/巡检报告/巡检报告-2026-07-09.md")
    if report_path.exists():
        text = report_path.read_text(encoding='utf-8')
        text += f"""
---

## 治理执行记录（{now}）

本次执行了实际去重合并操作，每条操作均附带审计记录：

"""
        for topic, insight, path, audit in produced:
            text += f"- **{topic}**: {insight['case_count']} 条 case → 1 个 project_insight\n"
            text += f"  - 审计ID: {audit.audit_id}\n"
            text += f"  - insight: {Path(path).name}\n"
            text += f"  - 审计: audit-MERGE-{audit.audit_id}.md\n"
            text += f"  - 回滚: 删除 insight 文件即可还原（原始 case 未修改）\n"
        text += "\n所有审计记录存放在 `agents/memory-admin/.cases/audit-*.md`，可通过审计ID检索。\n"
        report_path.write_text(text, encoding='utf-8')

    print("✅ 治理执行完成。每条操作均附带审计记录，可追溯、可回滚。")


if __name__ == "__main__":
    asyncio.run(main())
