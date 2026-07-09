#!/usr/bin/env python3
"""
项目脚手架 — 一键创建新的项目记忆空间。

用法：
  python project_setup.py my-project        # 创建新项目
  python project_setup.py my-project --user 5unny  # 指定用户

自动完成：
  - 创建项目目录结构（agents/ + users/ + governance/）
  - 初始化 memory-admin agent
  - 授权全局视角
  - 输出项目模板引导
"""

import sys, os
import httpx, asyncio

EVEROS_URL = "http://127.0.0.1:8000"
MEMORY_ROOT = os.path.expanduser("~/.everos")


async def setup_project(project_id: str, user_id: str = "default_user"):
    """创建新项目空间"""
    base = os.path.join(MEMORY_ROOT, "default_app", project_id)

    # 目录结构
    dirs = [
        f"{base}/agents",
        f"{base}/users/{user_id}/episodes",
        f"{base}/users/{user_id}/.atomic_facts",
        f"{base}/users/{user_id}/.foresights",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # memory-admin
    admin_dir = f"{base}/agents/memory-admin"
    admin_dirs = [
        f"{admin_dir}/.cases",
        f"{admin_dir}/.skills",
        f"{admin_dir}/.atomic_facts",
        f"{admin_dir}/.foresights",
        f"{admin_dir}/governance/audit-trail",
        f"{admin_dir}/governance/project-insights",
        f"{admin_dir}/governance/巡检报告",
    ]
    for d in admin_dirs:
        os.makedirs(d, exist_ok=True)

    # 写入 AGENTS.md 模板
    template = os.path.join(
        os.path.dirname(__file__), "..", "agents", "memory-admin", "AGENTS.md"
    )
    if os.path.exists(template):
        with open(template, encoding="utf-8") as f:
            content = f.read()
        content = content.replace("default", project_id)
        with open(f"{admin_dir}/AGENTS.md", "w", encoding="utf-8") as f:
            f.write(content)

    # 授权
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.put(
            f"{EVEROS_URL}/api/v1/admin/agents/memory-admin/permissions",
            json={"global_view": True},
        )
        if r.status_code == 200:
            print(f"  ✅ memory-admin 已授权")

    # 输出
    print(f"""
{'='*50}
  项目 '{project_id}' 创建完成！
{'='*50}

目录结构:
  {base}/
  ├── agents/
  │   └── memory-admin/    ← 记忆管理员（已授权全局视角）
  │       ├── AGENTS.md     ← 角色 + 工作规则
  │       ├── .cases/       ← agent 轨记忆
  │       └── governance/   ← 治理产物
  │           ├── audit-trail/
  │           ├── project-insights/
  │           └── 巡检报告/
  └── users/{user_id}/
      └── episodes/         ← user 轨记忆

下一步:
  1. 新建 agent:   python install.py 并选择 "创建 Agent"
  2. 执行治理:      python scripts/governance_exec.py
  3. 查看总览:      python scripts/project_status.py {project_id}
  4. 写入对话:      POST /api/v1/memory/add + /flush
""")


async def main():
    if len(sys.argv) < 2:
        print("用法: python project_setup.py <项目ID> [--user <用户ID>]")
        print("示例: python project_setup.py my-app --user 5unny")
        return

    project_id = sys.argv[1]
    user_id = "default_user"
    for i, arg in enumerate(sys.argv):
        if arg == "--user" and i + 1 < len(sys.argv):
            user_id = sys.argv[i + 1]

    # 检查 EverOS
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            await c.get(f"{EVEROS_URL}/health")
    except Exception:
        print("⚠️  EverOS 未运行，仅创建目录结构")
        print("   启动后执行 python install.py 完成授权\n")

    await setup_project(project_id, user_id)


if __name__ == "__main__":
    asyncio.run(main())
