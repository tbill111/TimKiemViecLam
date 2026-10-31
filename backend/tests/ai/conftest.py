"""Test router AI khi `app/deps.py` của Thái Anh chưa có: dựng bản thay thế tối thiểu trong bộ nhớ.

Khi `app.deps` thật đã được merge, import thành công và stub này không được dùng.
Hợp đồng mà router yêu cầu: `get_current_user()` trả đối tượng có `.id`, `.role`, `.company_id`;
`require_role(*roles)` trả dependency kiểm tra vai trò (403) và trả lại user.
"""
from __future__ import annotations

import sys
import types

from fastapi import Depends, HTTPException

try:  # noqa: SIM105
    import app.deps  # type: ignore  # noqa: F401
except ImportError:
    stub = types.ModuleType("app.deps")

    def get_current_user():
        raise HTTPException(401, detail="not_authenticated")

    def require_role(*roles: str):
        def dep(user=Depends(get_current_user)):
            if user.role not in roles:
                raise HTTPException(403, detail="forbidden")
            return user

        return dep

    stub.get_current_user = get_current_user  # type: ignore[attr-defined]
    stub.require_role = require_role  # type: ignore[attr-defined]
    sys.modules["app.deps"] = stub
