import json
import os
import re
import httpx
from openai import OpenAI
from file_search import search_files, list_directory, get_all_drives

# Load config
_config_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(_config_path, "r", encoding="utf-8") as f:
    _config = json.load(f)

# API 配置
_api_config = _config.get("api_settings", {})
_timeout = _api_config.get("timeout", 30)
_max_retries = _api_config.get("max_retries", 2)

client = OpenAI(
    api_key=_config["dashscope_api_key"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    timeout=httpx.Timeout(_timeout, connect=10),
    max_retries=_max_retries
)
MODEL = _config.get("model", "qwen-turbo")

SYSTEM_PROMPT = """你是本地文件助手，帮用户搜索、浏览电脑文件并发邮件。只输出JSON（不要输出任何其他内容）：

搜索文件：
{"action":"search","search_params":{"keywords":["关键词1"],"file_types":[".pdf"],"max_results":20}}

浏览目录（查看某个文件夹里有什么）：
{"action":"browse","browse_params":{"path":"C:\\\\Users"}}

发邮件：
{"action":"email","email_params":{"recipient":"xx@qq.com","file_indices":[0,1]}}

普通聊天：
{"action":"chat","reply":"回复内容"}

规则：
- 用户说"帮我找简历"→search，keywords:["简历","resume","cv"]（多同义词提高命中），max_results默认为20
- 用户说"找毕业论文"→search，keywords:["毕业","论文","thesis"]
- 用户说"找照片/图片"→search，keywords:["照片","photo","img","picture"]，file_types:[".jpg",".png",".jpeg",".gif",".webp"]
- **重要**：如果用户的搜索范围很泛（例如"找所有mp4"），你可以把 max_results 设大一点（比如100或更大）。如果有很多，你也可以先用chat询问用户"需要找多少个？还是全部？"
- 用户说"看看C盘有什么" / "D盘里有什么" / "打开某个文件夹" / "打开目录 X:\\路径"→browse，path对应的盘或目录
- 用户说"看看我的电脑" / "我有哪些盘" / "看看磁盘"→browse，path:"/"
- 用户说"我的文档" "桌面"这类→browse，path指向对应系统路径
- 用户说"发给xxx@qq.com"→email
- file_types为空则搜索所有类型
- 图片:[".jpg",".png",".jpeg",".gif",".webp",".bmp"]  Excel:[".xlsx",".xls"]  Word:[".docx",".doc"]  PDF:[".pdf"]
- 只输出JSON，不要说任何其他内容"""


# 用于存储全站搜索进度（简单实现：单实例）
global_search_progress = {
    "status": "idle",
    "message": "",
    "found_count": 0
}

class FileAgent:
    def __init__(self):
        self.last_results = []  # 上次搜索结果，供发邮件引用
        self.current_dir = None  # 当前浏览的目录

    def chat(self, user_message):
        """处理用户消息，返回 agent 响应。"""
        global global_search_progress
        
        # 重置进度状态为分析中
        global_search_progress["status"] = "analyzing"
        global_search_progress["message"] = "正在理解您的需求..."
        global_search_progress["found_count"] = 0

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 附加上下文（上次结果摘要，省 token）
        if self.last_results:
            file_list = ", ".join([f"[{i}]{r['name']}" for i, r in enumerate(self.last_results[:10])])
            messages.append({
                "role": "user",
                "content": f"[上次搜索到的文件: {file_list}]\n\n{user_message}"
            })
        else:
            messages.append({"role": "user", "content": user_message})

        # 调用 LLM
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=300
            )
            raw = response.choices[0].message.content.strip()
        except Exception as e:
            global_search_progress["status"] = "idle"
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                return {"reply": "API Key 错误，请检查 config.json", "action": "chat", "files": [], "email_result": None}
            return {"reply": f"AI 服务暂时不可用: {error_msg[:80]}", "action": "chat", "files": [], "email_result": None}

        # 解析 JSON 响应
        parsed = self._parse_response(raw)
        action = parsed.get("action", "chat")
        ai_reply = parsed.get("reply", "")
        files = []
        email_result = None
        browse_result = None

        # -------- search --------
        if action == "search":
            params = parsed.get("search_params", {}) or {}
            keywords = params.get("keywords") or []
            file_types = params.get("file_types") or None
            
            # 获取请求或配置的 max_results
            requested_max = params.get("max_results")
            default_max = _config.get("max_results", 20)
            max_results = int(requested_max) if requested_max else default_max

            # 从 config 取搜索根目录（支持全盘）
            search_roots = _config.get("search_roots", ["C:\\Users"])

            global_search_progress["status"] = "searching"
            global_search_progress["message"] = f"正在全盘搜索: {'、'.join(keywords) if keywords else '所有文件'}..."

            def on_progress(msg, count):
                global_search_progress["message"] = msg
                global_search_progress["found_count"] = count

            files = search_files(
                keywords=keywords,
                file_types=file_types,
                max_results=max_results,
                timeout_seconds=300,       # 提高到5分钟
                search_roots=search_roots,
                progress_callback=on_progress
            )
            self.last_results = files
            global_search_progress["status"] = "idle"

            if files:
                reply = f"找到 {len(files)} 个文件（请求上限 {max_results} 个），点击选中后可发送到邮箱："
            else:
                kw_str = "、".join(keywords) if keywords else "全部"
                reply = f"没找到文件（关键词: {kw_str}），换个词试试？"

        # -------- browse --------
        elif action == "browse":
            params = parsed.get("browse_params", {}) or {}
            path = params.get("path", None)

            # 处理 "/" 或 "我的电脑" → 列出所有磁盘
            if path in (None, "/", "\\", "我的电脑", "计算机", "this pc"):
                path = None

            browse_result = list_directory(path)
            self.current_dir = browse_result.get("path", path)

            if browse_result.get("error"):
                reply = f"无法浏览目录: {browse_result['error']}"
            else:
                dir_count = len(browse_result.get("dirs", []))
                file_count = len(browse_result.get("files", []))
                reply = f"📁 {browse_result['path']} — {dir_count} 个文件夹，{file_count} 个文件"

        # -------- email --------
        elif action == "email":
            params = parsed.get("email_params", {}) or {}
            recipient = params.get("recipient")
            file_indices = params.get("file_indices", [])

            file_paths = []
            if file_indices and self.last_results:
                for idx in file_indices:
                    if isinstance(idx, int) and 0 <= idx < len(self.last_results):
                        file_paths.append(self.last_results[idx]["path"])

            if not recipient:
                reply = "请告诉我收件邮箱，例如：发到 xxx@qq.com"
            elif not self.last_results:
                reply = "请先搜索文件，再发送。"
            else:
                if not file_paths:
                    file_paths = [r["path"] for r in self.last_results[:5]]
                from email_sender import send_file_email
                success, info = send_file_email(recipient, file_paths, "")
                email_result = {"success": success, "info": info}
                reply = info

        # -------- chat --------
        else:
            reply = ai_reply or "我可以帮你搜索或浏览电脑里的文件，找到后发到邮箱。\n示例：\n• 帮我找简历\n• 看看D盘有什么\n• 找所有PDF文件"

        return {
            "reply": reply,
            "action": action,
            "files": files,
            "email_result": email_result,
            "browse_result": browse_result
        }

    def _parse_response(self, raw):
        """从模型响应中提取 JSON。"""
        raw = raw.strip()

        # 去掉 markdown 代码块
        if raw.startswith("```"):
            lines = raw.split("\n")
            if len(lines) > 2:
                raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            raw = raw.strip()

        # 直接解析
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # 用大括号匹配提取 JSON
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
            json_str = raw[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        return {"action": "chat", "reply": raw if raw else "抱歉，我没理解你的意思，可以再说一遍吗？"}

    def reset(self):
        self.last_results = []
        self.current_dir = None
