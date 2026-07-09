#!/usr/bin/env python3
"""
EverOS Memory Admin — 一键安装向导。

引导你完成：
  1. 检查 EverOS 服务状态
  2. 初始化默认项目空间
  3. 创建 memory-admin agent
  4. 授权全局视角
  5. 生成第一个业务 agent 模板

每一步都有中文说明，出错自动提示修复方案。
"""

import sys, os, json, time
import httpx, asyncio

EVEROS_URL = "http://127.0.0.1:8000"
MEMORY_ROOT = os.path.expanduser("~/.everos")


def print_step(n: int, title: str):
    print(f"\n{'='*50}")
    print(f"  步骤 {n}: {title}")
    print(f"{'='*50}")


async def check_everos() -> bool:
    """检查 EverOS 是否在运行"""
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{EVEROS_URL}/health")
            if r.status_code == 200:
                print("  ✅ EverOS 服务运行中")
                return True
            else:
                print(f"  ❌ EverOS 返回异常状态码: {r.status_code}")
                return False
    except Exception:
        print("  ❌ 无法连接 EverOS 服务")
        print()
        print("  请先启动 EverOS：")
        print("    cd everos && everos server start")
        print()
        print("  或安装 EverOS：")
        print("    pip install everos")
        return False


async def init_default_project() -> bool:
    """初始化默认项目目录结构"""
    print_step(1, "初始化项目空间")
    root = os.path.join(MEMORY_ROOT, "default_app", "default_project")

    dirs = [
        f"{root}/agents",
        f"{root}/users/default_user/episodes",
        f"{root}/users/default_user/.atomic_facts",
        f"{root}/users/default_user/.foresights",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    print(f"  ✅ 项目空间已创建: {root}")
    print(f"     agents/ — agent 记忆目录")
    print(f"     users/  — 用户记忆目录")
    return True


async def setup_memory_admin() -> bool:
    """创建 memory-admin agent"""
    print_step(2, "创建记忆管理员 (memory-admin)")
    root = os.path.join(MEMORY_ROOT, "default_app", "default_project")

    admin_dir = f"{root}/agents/memory-admin"
    dirs = [
        f"{admin_dir}/.cases",
        f"{admin_dir}/.skills",
        f"{admin_dir}/.atomic_facts",
        f"{admin_dir}/.foresights",
        f"{admin_dir}/governance/audit-trail",
        f"{admin_dir}/governance/project-insights",
        f"{admin_dir}/governance/巡检报告",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 从模板复制 AGENTS.md
    template = os.path.join(
        os.path.dirname(__file__), "agents", "memory-admin", "AGENTS.md"
    )
    if os.path.exists(template):
        with open(template, encoding="utf-8") as f:
            agents_md = f.read()
        with open(f"{admin_dir}/AGENTS.md", "w", encoding="utf-8") as f:
            f.write(agents_md)
        print("  ✅ AGENTS.md 已写入")
    else:
        print("  ⚠️  AGENTS.md 模板未找到，将使用默认配置")

    # 授权全局视角
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.put(
            f"{EVEROS_URL}/api/v1/admin/agents/memory-admin/permissions",
            json={"global_view": True},
        )
        if r.status_code == 200:
            print("  ✅ 全局视角已开启")
        else:
            print(f"  ⚠️  授权失败: {r.json()}")

    print()
    print("  memory-admin 职责：")
    print("    • 自动巡检所有 agent 的记忆")
    print("    • 发现重复/互补 → 合并去重")
    print("    • 升级为项目共享知识")
    print("    • 产出治理报告 + 审计追溯")
    return True


async def grant_all_agents() -> bool:
    """给现有 agent 授权全局视角"""
    print_step(3, "授权 Agent 全局视野")
    print("  这允许所有 agent 在搜索时看到 memory-admin 的共享知识。")

    async with httpx.AsyncClient(timeout=30) as c:
        # 列出已有 agent
        r = await c.get(f"{EVEROS_URL}/api/v1/admin/agents/permissions")
        existing = r.json().get("agents", {})

        agents_to_grant = []
        root = os.path.join(MEMORY_ROOT, "default_app", "default_project", "agents")
        if os.path.exists(root):
            agents_to_grant = [
                d
                for d in os.listdir(root)
                if os.path.isdir(os.path.join(root, d)) and d != "memory-admin"
            ]

        if not agents_to_grant:
            print("  ℹ️  暂无其他 agent，跳过")
            return True

        for aid in agents_to_grant:
            r = await c.put(
                f"{EVEROS_URL}/api/v1/admin/agents/{aid}/permissions",
                json={"global_view": True},
            )
            status = "✅" if r.status_code == 200 else "⚠️"
            print(f"  {status} {aid}")

    return True


async def create_first_agent() -> bool:
    """交互式创建第一个业务 agent"""
    print_step(4, "创建你的第一个 Agent")
    print("  我们帮你创建一个业务 Agent，填入你想要的名称和用途。\n")

    name = input("  Agent 名称 (如 codex-exec-hello): ").strip()
    if not name:
        print("  ⏭  跳过")
        return True

    desc = input("  用途描述 (如 前端开发): ").strip()

    root = os.path.join(MEMORY_ROOT, "default_app", "default_project", "agents", name)
    for d in [".cases", ".skills", ".atomic_facts", ".foresights"]:
        os.makedirs(os.path.join(root, d), exist_ok=True)

    # 从模板写 AGENTS.md
    template_path = os.path.join(
        os.path.dirname(__file__), "agents", "agent-template", "AGENTS.md.template"
    )
    if os.path.exists(template_path):
        with open(template_path, encoding="utf-8") as f:
            content = f.read()
        content = content.replace("{{AGENT_NAME}}", name)
        content = content.replace("{{AGENT_DESC}}", desc or "通用任务执行")
        with open(os.path.join(root, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write(content)

    # 自动授权
    async with httpx.AsyncClient(timeout=10) as c:
        await c.put(
            f"{EVEROS_URL}/api/v1/admin/agents/{name}/permissions",
            json={"global_view": True},
        )

    print(f"\n  ✅ Agent '{name}' 创建完成")
    print(f"     AGENTS.md — 角色 + 工作规则")
    print(f"     .cases/  — 任务执行记录")
    print(f"     .skills/ — 技能积累")
    print(f"     全局视角 — 已开启")
    return True


async def test_everything() -> bool:
    """端到端验证"""
    print_step(5, "验证系统")

    async with httpx.AsyncClient(timeout=20) as c:
        # 1. 搜索测试
        r = await c.post(f"{EVEROS_URL}/api/v1/memory/search", json={
            "user_id": "default_user",
            "query": "测试",
            "top_k": 1,
            "method": "keyword",
        })
        if r.status_code == 200:
            print("  ✅ 搜索 API 正常")
        else:
            print(f"  ⚠️  搜索 API 异常: {r.json()}")
            return False

        # 2. 权限检查
        r2 = await c.get(f"{EVEROS_URL}/api/v1/admin/agents/memory-admin/permissions")
        if r2.status_code == 200:
            print("  ✅ memory-admin 权限正常")

    print()
    return True


async def main():
    print("""
╔══════════════════════════════════════════════╗
║     EverOS Memory Admin — 一键安装向导       ║
║     让 AI Agent 拥有记忆、协作、治理能力      ║
╚══════════════════════════════════════════════╝
""")

    # 步骤 0：检查 EverOS
    print_step(0, "检查 EverOS 服务")
    if not await check_everos():
        return

    # 执行安装
    steps = [
        init_default_project,
        setup_memory_admin,
        grant_all_agents,
        create_first_agent,
        test_everything,
    ]

    for step in steps:
        if not await step():
            print(f"\n❌ 安装中断")
            return
        time.sleep(0.5)

    print("""
╔══════════════════════════════════════════════╗
║          🎉 安装完成！                       ║
╠══════════════════════════════════════════════╣
║  下一步：                                    ║
║  1. 查看项目总览:                             ║
║     python scripts/project_status.py         ║
║                                              ║
║  2. 执行记忆治理:                             ║
║     python scripts/governance_exec.py        ║
║                                              ║
║  3. 新建项目:                                 ║
║     python scripts/project_setup.py          ║
║                                              ║
║  4. 在 Codex 中安装 Skill:                    ║
║     将 agents/memory-admin/SKILL.md          ║
║     复制到你的 Agent Skill 目录              ║
╚══════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    asyncio.run(main())
