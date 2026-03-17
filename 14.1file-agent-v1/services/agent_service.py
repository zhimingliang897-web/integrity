import json
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.utils import formataddr
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
import httpx
from openai import OpenAI

from app.config import settings


global_search_progress = {
    "status": "idle",
    "message": "",
    "found_count": 0
}

# 按用户持久化上次搜索结果，解决跨请求丢失问题
_last_results_by_user: Dict[str, List[dict]] = {}

MAX_EMAIL_ATTACHMENT_SIZE = 100 * 1024 * 1024  # 100MB total


def _build_system_prompt() -> str:
    """动态生成 SYSTEM_PROMPT，包含实际挂载目录信息。"""
    mounts = settings.mounts
    root = settings.root_path

    mount_lines = [f"- 主目录 {root}：可读可写"]
    for m in mounts:
        name = m.get("name", "未命名")
        path = m.get("path", "")
        readonly = m.get("readonly", True)
        perm = "只读" if readonly else "可读可写"
        mount_lines.append(f"- {name} ({path})：{perm}")
    mounts_section = "\n".join(mount_lines)

    return f"""你是私人文件系统的智能助手，帮助用户管理文件。请用JSON格式输出，不要输出其他内容。

支持的文件操作：
1. 搜索文件：{{"action":"search","search_params":{{"keyword":"搜索词","file_types":[".pdf"],"max_results":20,"search_all":true}}}}
2. 浏览目录：{{"action":"browse","browse_params":{{"path":"F:\\\\\\\\MyFiles"}}}}
3. 删除文件：{{"action":"delete","delete_params":{{"paths":["路径1","路径2"]}}}}
4. 移动文件：{{"action":"move","move_params":{{"paths":["路径1"],"target":"目标路径"}}}}
5. 重命名：{{"action":"rename","rename_params":{{"path":"原路径","new_name":"新名称"}}}}
6. 新建文件夹：{{"action":"create_folder","folder_params":{{"name":"文件夹名","parent_path":"父路径"}}}}
7. 发邮件：{{"action":"email","email_params":{{"recipient":"xxx@qq.com","paths":["文件路径"]}}}}
8. 普通聊天：{{"action":"chat","reply":"回复内容"}}

当前挂载目录：
{mounts_section}

规则：
- 搜索时使用多同义词提高命中率，如"简历"->["简历","resume","cv"]
- search_all为true时搜索所有挂载点
- 图片类型：[".jpg",".png",".jpeg",".gif",".webp",".bmp"]
- 文档类型：[".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".txt",".md"]
- 视频类型：[".mp4",".avi",".mov",".mkv",".webm"]
- 音频类型：[".mp3",".wav",".flac",".aac"]
- 路径使用双反斜杠转义，如 "F:\\\\\\\\MyFiles\\\\\\\\文档"
- 只输出JSON，不要任何其他内容"""


class AgentService:
    def __init__(self, db: Session, user: str = "default"):
        self.db = db
        self.user = user
        self.root_path = Path(settings.root_path)
        self.last_results: List[dict] = _last_results_by_user.get(user, [])
        
        if settings.llm_api_key:
            self.client = OpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                timeout=httpx.Timeout(60, connect=10)
            )
        else:
            self.client = None
    
    def chat(self, user_message: str, context: Optional[dict] = None) -> dict:
        global global_search_progress
        
        if not self.client:
            return {
                "reply": "LLM API 未配置，请在设置中配置 API Key",
                "action": "chat",
                "files": [],
                "result": None
            }
        
        global_search_progress["status"] = "analyzing"
        global_search_progress["message"] = "正在理解您的需求..."
        global_search_progress["found_count"] = 0
        
        messages = [{"role": "system", "content": _build_system_prompt()}]
        
        context_msg = ""
        if self.last_results:
            file_list = ", ".join([f"[{i}]{r['name']}" for i, r in enumerate(self.last_results[:5])])
            context_msg = f"[上次搜索结果: {file_list}]\n\n"
        
        if context and context.get("current_path"):
            context_msg += f"[当前目录: {context['current_path']}]\n\n"
        
        messages.append({"role": "user", "content": context_msg + user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=0.1,
                max_tokens=1024
            )
            raw = response.choices[0].message.content.strip()
        except Exception as e:
            global_search_progress["status"] = "idle"
            return {
                "reply": f"AI 服务暂时不可用: {str(e)[:200]}",
                "action": "chat",
                "files": [],
                "result": None
            }
        
        parsed = self._parse_response(raw)
        action = parsed.get("action", "chat")
        
        result = None
        files = []
        reply = ""
        
        if action == "search":
            files, reply = self._execute_search(parsed.get("search_params", {}))
            self.last_results = files
            _last_results_by_user[self.user] = files
        elif action == "browse":
            result, reply = self._execute_browse(parsed.get("browse_params", {}))
        elif action == "delete":
            result, reply = self._execute_delete(parsed.get("delete_params", {}))
        elif action == "move":
            result, reply = self._execute_move(parsed.get("move_params", {}))
        elif action == "rename":
            result, reply = self._execute_rename(parsed.get("rename_params", {}))
        elif action == "create_folder":
            result, reply = self._execute_create_folder(parsed.get("folder_params", {}))
        elif action == "email":
            result, reply = self._execute_email(parsed.get("email_params", {}), context)
        else:
            reply = parsed.get("reply", "我可以帮你管理文件，比如搜索、移动、删除等操作。")
        
        global_search_progress["status"] = "idle"
        
        return {
            "reply": reply,
            "action": action,
            "files": files,
            "result": result
        }
    
    def _parse_response(self, raw: str) -> dict:
        raw = raw.strip()
        
        if raw.startswith("```"):
            lines = raw.split("\n")
            if len(lines) > 2:
                raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            raw = raw.strip()
        
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        
        start = raw.find("{")
        if start != -1:
            depth = 0
            end = start
            for i, c in enumerate(raw[start:], start):
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
        
        return {"action": "chat", "reply": raw if raw else "抱歉，我没理解您的意思"}
    
    def _execute_search(self, params: dict) -> tuple:
        from services.search_service import SearchService
        
        keyword = params.get("keyword", "")
        file_types = params.get("file_types")
        max_results = params.get("max_results", 20)
        search_all = params.get("search_all", False)
        
        search_service = SearchService(self.db)
        
        global_search_progress["status"] = "searching"
        global_search_progress["message"] = f"正在搜索: {keyword or '全部文件'}..."
        
        def on_progress(msg, count):
            global_search_progress["message"] = msg
            global_search_progress["found_count"] = count
        
        files = search_service.search(
            keyword=keyword,
            file_types=file_types,
            max_results=max_results,
            progress_callback=on_progress,
            search_all_mounts=search_all
        )
        
        if files:
            reply = f"找到 {len(files)} 个文件"
        else:
            reply = f"没有找到匹配的文件"
        
        return files, reply
    
    def _execute_browse(self, params: dict) -> tuple:
        from services.file_service import FileService
        
        path = params.get("path", "")
        
        file_service = FileService(self.db)
        
        if not path:
            path = str(self.root_path)
        
        files, total, current_path = file_service.list_files(path=path)
        
        result = {
            "path": current_path,
            "files": files,
            "total": total
        }
        
        dirs_count = sum(1 for f in files if f["is_dir"])
        files_count = len(files) - dirs_count
        
        reply = f"📁 {current_path}\n{dirs_count} 个文件夹，{files_count} 个文件"
        
        return result, reply
    
    def _execute_delete(self, params: dict) -> tuple:
        from services.trash_service import TrashService
        
        paths = params.get("paths", [])
        
        if not paths:
            return None, "请指定要删除的文件"
        
        trash_service = TrashService(self.db)
        result = trash_service.move_to_trash(paths)
        
        if result["success_count"] > 0:
            reply = f"已将 {result['success_count']} 个文件移入回收站"
        else:
            reply = "删除失败，请检查文件是否存在"
        
        return result, reply
    
    def _execute_move(self, params: dict) -> tuple:
        from services.file_service import FileService
        
        paths = params.get("paths", [])
        target = params.get("target", "")
        
        if not paths or not target:
            return None, "请指定要移动的文件和目标路径"
        
        file_service = FileService(self.db)
        result = file_service.move(paths, target)
        
        if result["count"] > 0:
            reply = f"已移动 {result['count']} 个文件到 {target}"
        else:
            reply = "移动失败，请检查路径是否正确"
        
        return result, reply
    
    def _execute_rename(self, params: dict) -> tuple:
        from services.file_service import FileService
        
        path = params.get("path", "")
        new_name = params.get("new_name", "")
        
        if not path or not new_name:
            return None, "请指定原文件路径和新名称"
        
        file_service = FileService(self.db)
        
        try:
            result = file_service.rename(None, path, new_name)
            reply = f"已重命名为: {new_name}"
        except Exception as e:
            result = None
            reply = f"重命名失败: {str(e)}"
        
        return result, reply
    
    def _execute_create_folder(self, params: dict) -> tuple:
        from services.file_service import FileService
        
        name = params.get("name", "")
        parent_path = params.get("parent_path", str(self.root_path))
        
        if not name:
            return None, "请指定文件夹名称"
        
        file_service = FileService(self.db)
        
        try:
            result = file_service.create_folder(name, parent_path)
            reply = f"已创建文件夹: {name}"
        except Exception as e:
            result = None
            reply = f"创建失败: {str(e)}"
        
        return result, reply
    
    def _execute_email(self, params: dict, context: Optional[dict] = None) -> tuple:
        recipient = params.get("recipient", "")
        paths = params.get("paths", [])

        if not recipient:
            return None, "请指定收件人邮箱"

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', recipient):
            return None, f"收件人邮箱格式不正确：{recipient}"

        if not paths and context:
            paths = context.get("selected_files") or []
        if not paths and context:
            last_files = context.get("last_files") or []
            if last_files:
                paths = [f["path"] if isinstance(f, dict) else f for f in last_files[:5]]
        if not paths and self.last_results:
            paths = [f["path"] for f in self.last_results[:5]]

        if not paths:
            return None, "请指定要发送的文件，或先搜索文件再发送"

        if not settings.email_sender or not settings.email_password:
            return None, "邮箱未配置，请在设置页面填写发件邮箱和 SMTP 授权码"

        success, info = self._send_email(recipient, paths)
        return {"success": success, "info": info}, info

    def _send_email(self, recipient: str, file_paths: List[str]) -> tuple:
        valid_files = []
        skipped = []
        total_size = 0

        for fp in file_paths:
            if not fp or not os.path.isfile(fp):
                skipped.append(f"{os.path.basename(fp) if fp else '未知文件'}（不存在）")
                continue
            try:
                size = os.path.getsize(fp)
                if total_size + size > MAX_EMAIL_ATTACHMENT_SIZE:
                    skipped.append(f"{os.path.basename(fp)}（超出100MB总限制）")
                else:
                    valid_files.append(fp)
                    total_size += size
            except OSError:
                skipped.append(f"{os.path.basename(fp)}（无法读取）")

        if not valid_files:
            return False, "没有可发送的文件（文件不存在或超出100MB大小限制）"

        msg = MIMEMultipart()
        msg["From"] = formataddr(("文件助手", settings.email_sender))
        msg["To"] = recipient

        if len(valid_files) == 1:
            subject = f"文件助手：{os.path.basename(valid_files[0])}"
        else:
            subject = f"文件助手：{len(valid_files)} 个文件"
        msg["Subject"] = Header(subject, "utf-8")

        filenames_list = "\n".join([f"  • {os.path.basename(f)}" for f in valid_files])
        body = f"你好，\n\n以下是你请求的文件：\n{filenames_list}\n\n此邮件由文件助手自动发送。"
        if skipped:
            body += f"\n\n⚠️ 以下文件未能发送：\n" + "\n".join([f"  • {s}" for s in skipped])
        msg.attach(MIMEText(body, "plain", "utf-8"))

        for fp in valid_files:
            try:
                with open(fp, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                filename = os.path.basename(fp)
                try:
                    filename.encode("ascii")
                    part.add_header("Content-Disposition", "attachment", filename=filename)
                except UnicodeEncodeError:
                    part.add_header("Content-Disposition", "attachment", filename=("utf-8", "", filename))
                msg.attach(part)
            except Exception as e:
                skipped.append(f"{os.path.basename(fp)}（读取失败）")

        try:
            with smtplib.SMTP_SSL(settings.email_smtp_server, settings.email_smtp_port, timeout=30) as server:
                server.login(settings.email_sender, settings.email_password)
                server.sendmail(settings.email_sender, recipient, msg.as_string())

            result = f"✅ 已成功发送 {len(valid_files)} 个文件到 {recipient}"
            if skipped:
                result += f"\n⚠️ 跳过：{', '.join(skipped)}"
            return True, result

        except smtplib.SMTPAuthenticationError:
            return False, "❌ 邮箱认证失败：请检查 SMTP 授权码是否正确（QQ邮箱需要16位授权码，不是登录密码）"
        except smtplib.SMTPRecipientsRefused:
            return False, f"❌ 收件地址被拒绝：{recipient} 可能不存在或无法接收邮件"
        except smtplib.SMTPException as e:
            return False, f"❌ 邮件发送失败：{str(e)[:120]}"
        except TimeoutError:
            return False, "❌ 连接超时：请检查网络连接"
        except Exception as e:
            return False, f"❌ 发送失败：{str(e)[:120]}"
    
    def get_progress(self) -> dict:
        return global_search_progress.copy()