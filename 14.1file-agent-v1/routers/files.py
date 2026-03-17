from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import shutil
import zipfile
import tempfile
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.utils import formataddr
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.config import settings
from services.file_service import FileService
from services.upload_service import UploadService
from services.trash_service import TrashService

router = APIRouter(prefix="/api/files", tags=["文件管理"])


@router.get("")
async def list_files(
    path: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    sort_by: str = Query(default="name"),
    sort_order: str = Query(default="asc"),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_service = FileService(db)
    files, total, current_path = file_service.list_files(
        path=path,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    breadcrumb = file_service.get_breadcrumb(current_path)
    
    return {
        "files": files,
        "total": total,
        "path": current_path,
        "breadcrumb": breadcrumb,
        "page": page,
        "page_size": page_size
    }


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    target_path: Optional[str] = Form(default=None),
    # 与每个文件对应的相对路径，用于还原文件夹结构（顺序需与 files 对应）
    relative_paths: Optional[List[str]] = Form(default=None),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    upload_service = UploadService(db)
    result = await upload_service.upload_files(files, target_path, relative_paths)
    return result


@router.post("/folder")
async def create_folder(
    name: str = Form(...),
    parent_path: str = Form(default=""),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_service = FileService(db)
    
    try:
        result = file_service.create_folder(name, parent_path)
        return {"success": True, "folder": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/download")
async def download_files(
    paths: str = Query(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_service = FileService(db)
    path_list = paths.split(",")

    for p in path_list:
        if not file_service._is_path_allowed(p):
            raise HTTPException(status_code=403, detail="路径不允许访问")

    # 单个路径且为普通文件时，直接返回文件
    if len(path_list) == 1:
        file_path = Path(path_list[0])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        if file_path.is_file():
            return FileResponse(
                path=str(file_path),
                filename=file_path.name
            )
        # 如果是目录，则按目录打包 ZIP 返回，行为与多选保持一致

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_file.close()

    try:
        with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for path in path_list:
                file_path = Path(path)
                if file_path.exists():
                    if file_path.is_file():
                        zf.write(str(file_path), file_path.name)
                    else:
                        for root, dirs, files in os.walk(file_path):
                            for file in files:
                                file_full_path = Path(root) / file
                                arcname = str(file_full_path.relative_to(file_path.parent))
                                zf.write(str(file_full_path), arcname)

        return FileResponse(
            path=temp_file.name,
            filename="files.zip",
            media_type="application/zip"
        )
    except Exception as e:
        os.unlink(temp_file.name)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("")
async def delete_files(
    paths: str = Query(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    path_list = paths.split(",")
    trash_service = TrashService(db)
    result = trash_service.move_to_trash(path_list)
    return result


@router.post("/move")
async def move_files(
    paths: str = Query(...),
    target: str = Query(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    path_list = paths.split(",")
    file_service = FileService(db)
    
    try:
        result = file_service.move(path_list, target)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/copy")
async def copy_files(
    paths: str = Query(...),
    target: str = Query(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    path_list = paths.split(",")
    file_service = FileService(db)
    
    try:
        result = file_service.copy(path_list, target)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/rename")
async def rename_file(
    path: str = Query(...),
    new_name: str = Query(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_service = FileService(db)
    
    try:
        result = file_service.rename(None, path, new_name)
        return {"success": True, "file": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/info")
async def get_file_info(
    path: str = Query(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_service = FileService(db)
    
    try:
        info = file_service.get_file_info(path)
        return info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
async def get_stats(
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_service = FileService(db)
    return file_service.get_stats()


@router.get("/folders")
async def get_folders(
    path: str = Query(default=""),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_service = FileService(db)
    folders = file_service.get_folders_tree(path)
    return {"folders": folders}


@router.post("/star")
async def star_file(
    path: str = Form(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.database import File
    file_record = db.query(File).filter(File.path == path).first()
    if not file_record:
        file_record = File(path=path, name=Path(path).name, is_starred=True)
        db.add(file_record)
    else:
        file_record.is_starred = True
    db.commit()
    return {"success": True, "message": "已收藏"}


@router.delete("/star")
async def unstar_file(
    path: str = Query(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.database import File
    file_record = db.query(File).filter(File.path == path).first()
    if file_record:
        file_record.is_starred = False
        db.commit()
    return {"success": True, "message": "已取消收藏"}


@router.get("/starred")
async def get_starred_files(
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.database import File
    starred = db.query(File).filter(File.is_starred == True).all()
    files = []
    for f in starred:
        file_path = Path(f.path)
        if file_path.exists():
            files.append({
                "name": f.name,
                "path": f.path,
                "is_dir": f.is_dir,
                "size": f.size or (file_path.stat().st_size if file_path.is_file() else 0),
                "ext": f.ext,
                "modified_at": f.modified_at.isoformat() if f.modified_at else None
            })
    return {"files": files}


@router.post("/email")
async def send_file_email(
    paths: str = Form(...),
    recipient: str = Form(...),
    user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.config import settings as s
    
    if not s.email_sender or not s.email_password:
        raise HTTPException(status_code=400, detail="邮箱未配置，请先在设置中配置发件邮箱")
    
    path_list = paths.split(",")
    file_service = FileService(db)
    
    valid_paths = []
    for p in path_list:
        if file_service._is_path_allowed(p) and Path(p).exists():
            valid_paths.append(p)
    
    MAX_SIZE = 100 * 1024 * 1024
    checked_paths = []
    skipped = []
    total_size = 0
    for p in valid_paths:
        try:
            size = os.path.getsize(p)
            if total_size + size > MAX_SIZE:
                skipped.append(f"{Path(p).name}（超出20MB总限制）")
            else:
                checked_paths.append(p)
                total_size += size
        except OSError:
            skipped.append(f"{Path(p).name}（无法读取）")

    if not checked_paths:
        raise HTTPException(status_code=400, detail="没有可发送的文件（文件不存在或超出100MB大小限制）")

    try:
        msg = MIMEMultipart()
        msg["From"] = formataddr(("文件助手", s.email_sender))
        msg["To"] = recipient
        if len(checked_paths) == 1:
            subject = f"文件助手：{Path(checked_paths[0]).name}"
        else:
            subject = f"文件助手：{len(checked_paths)} 个文件"
        msg["Subject"] = Header(subject, "utf-8")

        filenames_list = "\n".join([f"  • {Path(p).name}" for p in checked_paths])
        body = f"你好，\n\n以下是你请求的文件：\n{filenames_list}\n\n此邮件由文件助手自动发送。"
        if skipped:
            body += f"\n\n⚠️ 以下文件未能发送：\n" + "\n".join([f"  • {s}" for s in skipped])
        msg.attach(MIMEText(body, "plain", "utf-8"))

        for p in checked_paths:
            file_path = Path(p)
            if file_path.is_file():
                with open(file_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                filename = file_path.name
                try:
                    filename.encode("ascii")
                    part.add_header("Content-Disposition", "attachment", filename=filename)
                except UnicodeEncodeError:
                    part.add_header("Content-Disposition", "attachment", filename=("utf-8", "", filename))
                msg.attach(part)

        with smtplib.SMTP_SSL(s.email_smtp_server, s.email_smtp_port, timeout=30) as server:
            server.login(s.email_sender, s.email_password)
            server.sendmail(s.email_sender, recipient, msg.as_string())

        result_msg = f"✅ 已成功发送 {len(checked_paths)} 个文件到 {recipient}"
        if skipped:
            result_msg += f"，跳过：{', '.join(skipped)}"
        return {"success": True, "message": result_msg}

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=500, detail="❌ 邮箱认证失败：请检查 SMTP 授权码（QQ邮箱需16位授权码，不是登录密码）")
    except smtplib.SMTPRecipientsRefused:
        raise HTTPException(status_code=500, detail=f"❌ 收件地址被拒绝：{recipient} 可能不存在")
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"❌ 邮件发送失败：{str(e)[:120]}")
    except TimeoutError:
        raise HTTPException(status_code=500, detail="❌ 连接超时：请检查网络连接")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ 发送失败：{str(e)[:120]}")


class TestEmailRequest(BaseModel):
    recipient: str


@router.post("/email/test")
async def test_email(
    req: TestEmailRequest,
    user: str = Depends(get_current_user)
):
    from app.config import settings as s

    if not s.email_sender or not s.email_password:
        raise HTTPException(status_code=400, detail="邮箱未配置，请先在设置中填写发件邮箱和授权码")

    try:
        msg = MIMEMultipart()
        msg["From"] = formataddr(("文件助手", s.email_sender))
        msg["To"] = req.recipient
        msg["Subject"] = Header("文件助手 - 邮箱连接测试", "utf-8")
        body = "这是一封测试邮件，说明你的邮箱配置正确，文件助手可以正常发送邮件。"
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP_SSL(s.email_smtp_server, s.email_smtp_port, timeout=30) as server:
            server.login(s.email_sender, s.email_password)
            server.sendmail(s.email_sender, req.recipient, msg.as_string())

        return {"success": True, "message": f"✅ 测试邮件已发送到 {req.recipient}，请查收"}

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=500, detail="❌ 认证失败：SMTP 授权码不正确")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ 发送失败：{str(e)[:120]}")