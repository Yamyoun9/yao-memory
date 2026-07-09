"""
项目总览查询 — 用户端感知 memory-admin 的入口。

用法：
  python project_status.py risk-monitor        # 查看风险监控项目总览
  python project_status.py default              # 查看默认项目总览
  python project_status.py risk-monitor --full  # 详细报告
"""

import httpx, asyncio, argparse, json, sys
from datetime import datetime


async def project_overview(project_id: str, everos_url: str = "http://127.0.0.1:8000", full: bool = False):
    """查询项目概览：agent 列表、记忆统计、最近的治理报告"""
    async with httpx.AsyncClient(timeout=30) as c:
        # 1. 搜索治理报告（user 轨）
        r = await c.post(f"{everos_url}/api/v1/memory/search", json={
            "user_id": "5unny",
            "project_id": project_id,
            "query": "记忆治理报告",
            "top_k": 3,
            "method": "keyword",
        })
        episodes = r.json().get("data", {}).get("episodes", [])

        # 2. 统计 agent_case（admin 全局视角搜）
        r2 = await c.post(f"{everos_url}/api/v1/memory/search", json={
            "agent_id": "memory-admin",
            "project_id": project_id,
            "query": "",  # keyword 模式不能空 query，用通配
            "top_k": 50,
            "method": "keyword",
        })
        cases = r2.json().get("data", {}).get("agent_cases", [])
        skills = r2.json().get("data", {}).get("agent_skills", [])

        return {
            "project_id": project_id,
            "reports": episodes,
            "agent_case_count": len(cases),
            "agent_skill_count": len(skills),
            "agents_seen": list(set(c.get("agent_id", "unknown") for c in cases)),
        }


def print_overview(data: dict, full: bool = False):
    """格式化输出项目总览"""
    print("=" * 60)
    print(f"  项目记忆总览 — {data['project_id']}")
    print("=" * 60)
    print(f"  查询时间: {datetime.now().isoformat()[:19]}")
    print()

    print("【项目记忆统计】")
    print(f"  agent_case: {data['agent_case_count']} 条")
    print(f"  agent_skill: {data['agent_skill_count']} 条")
    if data['agents_seen']:
        print(f"  活跃 agent: {', '.join(data['agents_seen'])}")
    print()

    reports = data["reports"]
    if not reports:
        print("【治理报告】暂无 — memory-admin 尚未执行巡检")
        print()
        print("  💡 memory-admin 负责：")
        print("    - 跨 agent 去重")
        print("    - 记忆质量检查")
        print("    - 升级为项目共享知识")
        print()
        print("  你可以通过以下方式交互：")
        print(f"    1. 搜索: POST /search project_id={data['project_id']} query='记忆治理报告'")
        print(f"    2. 手动触发巡检: 让 memory-admin 执行巡检任务")
        print(f"    3. 查看管理员规则: AGENTS.md")
        return

    # 有治理报告
    latest = reports[0]
    print(f"【最新治理报告】{len(reports)} 份")
    print(f"  时间: {latest.get('timestamp', '')[:19]}")
    subject = latest.get("subject", "")
    if subject:
        print(f"  主题: {subject[:80]}")
    episode_text = latest.get("episode", "")[:600]
    if episode_text:
        for line in episode_text.split("\n"):
            if line.strip():
                print(f"  {line[:100]}")
        if len(latest.get("episode", "")) > 600:
            print(f"  ... (共 {len(latest.get('episode', ''))} 字符，用 --full 查看完整)")
    print()

    if full:
        print("【完整治理报告】")
        full_text = latest.get("episode", "")
        print(full_text)
        print()

    print("【交互方式】")
    print(f"  搜索治理报告: POST /search user_id=5unny project_id={data['project_id']} query='记忆治理报告'")
    print(f"  搜索特定 agent 记忆: POST /search agent_id=<agent> project_id={data['project_id']}")
    print(f"  写入治理操作: python project_governance.py")
    print(f"  管理员规则: {data['project_id']}/agents/memory-admin/AGENTS.md")


async def main():
    parser = argparse.ArgumentParser(description="项目记忆总览")
    parser.add_argument("project", default="default", nargs="?", help="项目 ID")
    parser.add_argument("--full", action="store_true", help="显示完整治理报告")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="EverOS URL")
    args = parser.parse_args()

    data = await project_overview(args.project, args.url, args.full)
    print_overview(data, args.full)


if __name__ == "__main__":
    asyncio.run(main())
