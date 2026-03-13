from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os

from app.config import settings
from app.deps import get_current_user

router = APIRouter(prefix="/api/mounts", tags=["挂载点管理"])


class MountCreate(BaseModel):
    name: str
    path: str
    icon: Optional[str] = "📁"
    readonly: Optional[bool] = True


@router.get("")
async def get_mounts(user: str = Depends(get_current_user)):
    mounts = []
    for mount in settings.mounts:
        path = mount.get("path", "")
        exists = Path(path).exists() if path else False
        mounts.append({
            "name": mount.get("name", ""),
            "path": path,
            "icon": mount.get("icon", "📁"),
            "readonly": mount.get("readonly", True),
            "exists": exists
        })
    
    main_root = {
        "name": "MyFiles",
        "path": settings.root_path,
        "icon": "🏠",
        "readonly": False,
        "exists": Path(settings.root_path).exists()
    }
    
    return {
        "root": main_root,
        "mounts": mounts
    }


@router.post("")
async def add_mount(
    mount: MountCreate,
    user: str = Depends(get_current_user)
):
    if not Path(mount.path).exists():
        return {"success": False, "message": "路径不存在"}
    
    success = settings.add_mount(
        name=mount.name,
        path=mount.path,
        icon=mount.icon or "📁",
        readonly=mount.readonly if mount.readonly is not None else True
    )
    
    if success:
        return {"success": True, "message": "挂载点已添加"}
    else:
        return {"success": False, "message": "挂载点已存在"}


@router.delete("")
async def remove_mount(
    path: str,
    user: str = Depends(get_current_user)
):
    success = settings.remove_mount(path)
    
    if success:
        return {"success": True, "message": "挂载点已移除"}
    else:
        return {"success": False, "message": "挂载点不存在"}


@router.get("/check")
async def check_path(
    path: str,
    user: str = Depends(get_current_user)
):
    p = Path(path)
    
    if not p.exists():
        return {"exists": False, "message": "路径不存在"}
    
    is_readonly = settings.is_readonly_path(path)
    mount = settings.get_mount_by_path(path)
    
    return {
        "exists": True,
        "is_readonly": is_readonly,
        "mount_name": mount.get("name") if mount else None,
        "is_main_root": str(p.resolve()).startswith(str(Path(settings.root_path).resolve()))
    }