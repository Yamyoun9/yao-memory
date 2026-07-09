"""
Agent 权限治理存储层。

每个 agent 可以拥有独立权限。当前支持的权限：
  - global_view: 跨所有 agent 检索记忆（突破 owner_id 隔离）

存储格式：``<memory_root>/agent_permissions.json``
按 ``agent_id`` 为 key，权限对象为 value。
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import TypedDict

from everos.core.persistence import MemoryRoot


class AgentPermission(TypedDict, total=False):
    """单个 agent 的权限配置"""
    global_view: bool
    """是否允许跨 agent 检索（默认 False）"""


class PermissionsStore:
    """Agent 权限的 JSON 文件读写封装，线程安全的单例。

    存储路径：``<memory_root>/agent_permissions.json``
    """

    _instance: PermissionsStore | None = None
    _lock = threading.Lock()

    def __init__(self, root: MemoryRoot | None = None) -> None:
        self._root = root or MemoryRoot.default()
        self._path = self._root.root / "agent_permissions.json"
        self._cache: dict[str, AgentPermission] = {}
        self._loaded = False

    @classmethod
    def default(cls) -> PermissionsStore:
        """获取线程安全的单例实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── I/O ─────────────────────────────────────────────────

    def _load(self) -> dict[str, AgentPermission]:
        """从 JSON 文件加载权限数据"""
        if not self._path.exists():
            return {}
        try:
            text = self._path.read_text(encoding="utf-8")
            return json.loads(text)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data: dict[str, AgentPermission]) -> None:
        """原子写入 JSON 文件（先写临时文件再 rename）"""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self._path)

    def _ensure_loaded(self) -> None:
        """懒加载存储"""
        if not self._loaded:
            self._cache = self._load()
            self._loaded = True

    # ── 公共 API ────────────────────────────────────────────

    def get(self, agent_id: str) -> AgentPermission:
        """获取单个 agent 的权限配置"""
        self._ensure_loaded()
        return self._cache.get(agent_id, {})

    def has_global_view(self, agent_id: str) -> bool:
        """检查 agent 是否有全局视角权限"""
        perms = self.get(agent_id)
        return perms.get("global_view", False)

    def set(self, agent_id: str, permission: AgentPermission) -> None:
        """设置/更新 agent 的权限"""
        self._ensure_loaded()
        self._cache[agent_id] = permission
        self._save(self._cache)

    def remove(self, agent_id: str) -> None:
        """移除 agent 的所有权限配置"""
        self._ensure_loaded()
        self._cache.pop(agent_id, None)
        self._save(self._cache)

    def list_all(self) -> dict[str, AgentPermission]:
        """列出所有 agent 的权限"""
        self._ensure_loaded()
        return dict(self._cache)

    def grant_global_view(self, agent_id: str) -> None:
        """快捷方法：给 agent 开启全局视角"""
        perms = dict(self.get(agent_id))
        perms["global_view"] = True
        self.set(agent_id, perms)

    def revoke_global_view(self, agent_id: str) -> None:
        """快捷方法：关闭 agent 的全局视角"""
        perms = dict(self.get(agent_id))
        if "global_view" in perms:
            del perms["global_view"]
            self.set(agent_id, perms)

    def invalidate(self) -> None:
        """清除缓存，强制下次读取时重新加载文件"""
        self._loaded = False
