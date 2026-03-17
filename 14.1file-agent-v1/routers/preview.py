from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse, Response
from typing import Optional
from pathlib import Path
from urllib.parse import quote
import io
import os
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from services.preview_service import PreviewService

router = APIRouter(prefix="/api/preview", tags=["预览"])


def get_base_url(request: Request) -> str:
    return str(request.base_url).rstrip('/')


@router.get("")
async def preview_file(
    request: Request,
    path: str = Query(...),
    user: str = Depends(get_current_user)
):
    preview_service = PreviewService()
    base_url = get_base_url(request)

    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    ext = file_path.suffix.lower()
    preview_type = preview_service.get_preview_type(ext)
    encoded_path = quote(path, safe='')

    if preview_type == "text":
        content = preview_service.get_text_preview(path)
        return {
            "type": "text",
            "content": content,
            "filename": file_path.name
        }

    elif preview_type == "image":
        return {
            "type": "image",
            "url": f"/api/preview/file?path={encoded_path}",
            "filename": file_path.name
        }

    elif preview_type == "video":
        return {
            "type": "video",
            "url": f"/api/preview/file?path={encoded_path}",
            "filename": file_path.name
        }

    elif preview_type == "audio":
        return {
            "type": "audio",
            "url": f"/api/preview/file?path={encoded_path}",
            "filename": file_path.name
        }

    elif preview_type == "pdf":
        return {
            "type": "pdf",
            "url": f"/api/preview/file?path={encoded_path}",
            "filename": file_path.name
        }

    else:
        return {
            "type": "unknown",
            "message": "不支持预览此类型文件",
            "filename": file_path.name
        }


@router.get("/file")
async def get_file(
    request: Request,
    path: str = Query(...),
    user: str = Depends(get_current_user)
):
    preview_service = PreviewService()

    try:
        file_path = Path(path)
        if not preview_service._is_path_allowed(path):
            raise HTTPException(status_code=403, detail="路径不允许访问")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or "application/octet-stream"

        file_size = file_path.stat().st_size
        range_header = request.headers.get("range")

        cache_headers = {
            "Cache-Control": "private, max-age=3600",
            "Accept-Ranges": "bytes",
        }

        if range_header:
            # 解析 Range: bytes=start-end
            range_val = range_header.replace("bytes=", "")
            parts = range_val.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
            end = min(end, file_size - 1)
            chunk_size = end - start + 1

            def iter_file(start, end):
                with open(file_path, "rb") as f:
                    f.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk = f.read(min(65536, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            return StreamingResponse(
                iter_file(start, end),
                status_code=206,
                media_type=mime_type,
                headers={
                    **cache_headers,
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(chunk_size),
                },
            )
        else:
            def iter_full():
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        yield chunk

            return StreamingResponse(
                iter_full(),
                media_type=mime_type,
                headers={
                    **cache_headers,
                    "Content-Length": str(file_size),
                    "Content-Disposition": f'inline; filename="{quote(file_path.name)}"',
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thumb")
async def get_thumbnail(
    path: str = Query(...),
    user: str = Depends(get_current_user)
):
    preview_service = PreviewService()
    
    try:
        thumb_io = preview_service.get_image_thumbnail(path)
        return StreamingResponse(
            thumb_io,
            media_type="image/jpeg"
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))