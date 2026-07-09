"""Agent 权限管理 API 路由。

   GET  /api/v1/admin/agents/permissions          — 列出所有 agent 的权限
   GET  /api/v1/admin/agents/{agent_id}/permissions — 查看单个 agent 权限
   PUT  /api/v1/admin/agents/{agent_id}/permissions — 设置单个 agent 权限
   DELETE /api/v1/admin/agents/{agent_id}/permissions — 移除单个 agent 权限

   请求体（PUT）：
       {"global_view": true}
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from everos.memory.admin.permissions import PermissionsStore

router = APIRouter(prefix="/api/v1/admin/agents", tags=["admin"])


# ── 列出所有 agent 权限 ──────────────────────────────────────

@router.get("/permissions")
async def list_permissions() -> dict[str, Any]:
    """列出所有已配置权限的 agent"""
    store = PermissionsStore.default()
    all_perms = store.list_all()
    return {
        "agents": {
            agent_id: {
                "global_view": perms.get("global_view", False),
            }
            for agent_id, perms in all_perms.items()
        },
        "total": len(all_perms),
    }


# ── 查看单个 agent 权限 ──────────────────────────────────────

@router.get("/{agent_id}/permissions")
async def get_permission(agent_id: str) -> dict[str, Any]:
    """查看单个 agent 的完整权限配置"""
    store = PermissionsStore.default()
    perms = store.get(agent_id)
    return {
        "agent_id": agent_id,
        "global_view": perms.get("global_view", False),
    }


# ── 设置单个 agent 权限 ──────────────────────────────────────

@router.put("/{agent_id}/permissions")
async def set_permission(
    agent_id: str, body: dict[str, bool]
) -> dict[str, Any]:
    """设置或更新单个 agent 的权限。

    请求体示例：
        {"global_view": true}
    """
    if "global_view" not in body:
        raise HTTPException(
            status_code=422,
            detail="Body must contain 'global_view' field (boolean)",
        )
    gv = body["global_view"]
    if not isinstance(gv, bool):
        raise HTTPException(
            status_code=422,
            detail="'global_view' must be a boolean",
        )

    store = PermissionsStore.default()
    if gv:
        store.grant_global_view(agent_id)
    else:
        store.revoke_global_view(agent_id)

    return {
        "agent_id": agent_id,
        "global_view": gv,
        "updated": True,
    }


# ── 移除 agent 权限 ──────────────────────────────────────────

@router.delete("/{agent_id}/permissions")
async def delete_permission(agent_id: str) -> dict[str, Any]:
    """移除 agent 的全部权限配置（恢复默认：全部关闭）"""
    store = PermissionsStore.default()
    store.remove(agent_id)
    return {
        "agent_id": agent_id,
        "global_view": False,
        "removed": True,
    }
