import os
import shutil
import uuid
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import OperationLog


class UploadService:
    def __init__(self, db: Session):
        self.db = db
        self.uploads_path = Path(settings.uploads_path)
        self.root_path = Path(settings.root_path)
        self.max_size = settings.max_upload_size_mb * 1024 * 1024
        self.uploads_path.mkdir(parents=True, exist_ok=True)

        # 允许上传的根目录：主目录 + 所有挂载点
        self.allowed_roots = [self.root_path.resolve()]
        for mount in settings.mounts:
            mount_path = mount.get("path")
            if mount_path:
                try:
                    p = Path(mount_path)
                    if p.exists():
                        self.allowed_roots.append(p.resolve())
                except Exception:
                    continue
    
    def _is_path_allowed(self, path: str) -> bool:
        """检查上传目标是否在允许的根目录（主目录或挂载目录）下。"""
        try:
            abs_path = Path(path).resolve()
            for root in self.allowed_roots:
                if str(abs_path).startswith(str(root)):
                    return True
            return False
        except Exception:
            return False

    async def upload_file(
        self,
        file: UploadFile,
        target_path: Optional[str] = None,
        relative_path: Optional[str] = None,
    ) -> dict:
        """
        上传单个文件。
        - target_path: 目标根目录
        - relative_path: 相对 target_path 的子路径（用于还原文件夹层级）
        """
        if target_path:
            target_dir = Path(target_path)
        else:
            target_dir = self.uploads_path

        if not self._is_path_allowed(str(target_dir)):
            target_dir = self.uploads_path

        # 计算最终落盘路径：支持带层级的 relative_path
        if relative_path:
            rel = Path(relative_path)
            # 只保留安全的相对路径片段，防止 .. 等逃逸
            safe_parts = [p for p in rel.parts if p not in ("", ".", "..")]
            if safe_parts:
                file_path = target_dir.joinpath(*safe_parts)
            else:
                file_path = target_dir / file.filename
        else:
            file_path = target_dir / file.filename

        # 确保父目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 文件名冲突处理（在同一目录下加 (1)、(2)...）
        if file_path.exists():
            base = file_path.stem
            ext = file_path.suffix
            parent = file_path.parent
            counter = 1
            candidate = file_path
            while candidate.exists():
                candidate = parent / f"{base} ({counter}){ext}"
                counter += 1
            file_path = candidate

        total_size = 0
        async with aiofiles.open(file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)

                if total_size > self.max_size:
                    await f.close()
                    file_path.unlink()
                    raise ValueError(f"文件大小超过限制 ({settings.max_upload_size_mb}MB)")

                await f.write(chunk)

        stat = file_path.stat()

        self._log_operation("upload", str(file_path), f"size: {total_size}")

        return {
            "name": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

    async def upload_files(
        self,
        files: List[UploadFile],
        target_path: Optional[str] = None,
        relative_paths: Optional[List[str]] = None,
    ) -> dict:
        uploaded = []
        failed = []
        
        for idx, file in enumerate(files):
            try:
                rel_path = None
                if relative_paths and idx < len(relative_paths):
                    rel_path = relative_paths[idx]
                result = await self.upload_file(file, target_path, rel_path)
                uploaded.append(result)
            except Exception as e:
                failed.append({
                    "name": file.filename,
                    "error": str(e)
                })
        
        return {
            "uploaded": uploaded,
            "failed": failed,
            "total": len(files),
            "success_count": len(uploaded),
            "failed_count": len(failed)
        }
    
    def _log_operation(self, action: str, file_path: str, details: str = None):
        log = OperationLog(
            action=action,
            file_path=file_path,
            details=details
        )
        self.db.add(log)
        self.db.commit()