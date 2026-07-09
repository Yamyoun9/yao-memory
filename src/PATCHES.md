"""
EverOS core patches 说明。

将以下文件替换到你的 EverOS 源码中对应位置：

src/everos/
├── memory/admin/           ← 新增：权限治理模块
│   ├── __init__.py
│   └── permissions.py
├── memory/zh_prompt_patch.py ← 新增：中文 prompt 补丁
└── entrypoints/api/routes/admin.py ← 新增：管理 API

以下文件需手动修改（改动量小，见注释）：

### memory/search/filters.py

在 compile_filters 函数签名添加参数：
- skip_owner_filter: bool = False
- cross_project_ids: list[str] | None = None

并修改 project_id 构建逻辑为 IN 子句。

### memory/search/manager.py

在 SearchManager.search() 中添加：
- global_view 权限检查
- cross_project 自动包含 default

### entrypoints/api/app.py

在路由注册中添加 admin.router。
"""

import os

print("请参考 README.md 中的安装步骤。")
print()
print("源码 patch 文件列表：")
for root, dirs, files in os.walk(os.path.dirname(__file__)):
    for f in files:
        if f.endswith('.py'):
            rel = os.path.relpath(os.path.join(root, f), os.path.dirname(__file__))
            print(f"  src/{rel}")
