from flask import Flask, request, jsonify, render_template
import os
import json
from agent import FileAgent

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Load config
_config_path = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(_config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)
except Exception as e:
    print(f"[警告] 无法加载 config.json: {e}")
    _config = {"web_port": 5000, "web_host": "0.0.0.0"}

# One agent per session (simple: single global agent, OK for personal use)
agent = FileAgent()

# Get allowed search roots for path validation
_allowed_roots = [os.path.normpath(p).lower() for p in _config.get("search_roots", ["C:\\Users"])]


def is_path_allowed(filepath):
    """
    Check if a file path is within allowed search roots (security check).
    Allows any local drive root (A-Z) to support full-disk browsing.
    """
    try:
        normalized = os.path.normpath(os.path.abspath(filepath)).lower()
        # Allow configured search roots
        if any(normalized.startswith(root) for root in _allowed_roots):
            return True
        # Also allow any local drive letter (e.g. D:\, E:\)
        import string
        for letter in string.ascii_lowercase:
            if normalized.startswith(f"{letter}:\\") or normalized.startswith(f"{letter}:/"):
                return True
        return False
    except Exception:
        return False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request"}), 400

        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        # Limit message length
        if len(user_message) > 1000:
            user_message = user_message[:1000]

        result = agent.chat(user_message)
        return jsonify(result)
    except Exception as e:
        # Reset progress on error
        from agent import global_search_progress
        global_search_progress["status"] = "idle"
        return jsonify({
            "reply": "服务暂时出错，请稍后重试",
            "action": "chat",
            "files": [],
            "email_result": None
        })


@app.route("/progress")
def progress():
    def generate():
        import time
        from agent import global_search_progress
        last_msg = ""
        last_count = -1
        
        while True:
            current_status = global_search_progress["status"]
            current_msg = global_search_progress["message"]
            current_count = global_search_progress["found_count"]
            
            # 只有状态改变或每秒强制发送一次心跳
            if current_status != "idle" or last_msg != current_msg or last_count != current_count:
                yield f"data: {json.dumps({'status': current_status, 'message': current_msg, 'found_count': current_count})}\n\n"
                last_msg = current_msg
                last_count = current_count
            
            if current_status == "idle" and last_msg != "":
                # 搜索结束，发送最终闲置状态然后退出流
                yield f"data: {json.dumps({'status': 'idle', 'message': '', 'found_count': 0})}\n\n"
                break
                
            time.sleep(0.5)

    return app.response_class(generate(), mimetype='text/event-stream')


@app.route("/send-email", methods=["POST"])
def send_email():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "info": "无效的请求"}), 400

        recipient = data.get("recipient", "").strip()
        file_paths = data.get("file_paths", [])
        message = data.get("message", "")

        if not recipient:
            return jsonify({"success": False, "info": "请提供收件邮箱地址"}), 400
        if not file_paths or not isinstance(file_paths, list):
            return jsonify({"success": False, "info": "没有选择要发送的文件"}), 400

        # Validate file paths are within allowed roots
        validated_paths = []
        for fp in file_paths:
            if isinstance(fp, str) and is_path_allowed(fp):
                validated_paths.append(fp)

        if not validated_paths:
            return jsonify({"success": False, "info": "选择的文件不在允许的目录范围内"}), 400

        from email_sender import send_file_email
        success, info = send_file_email(recipient, validated_paths, message[:500])
        return jsonify({"success": success, "info": info})
    except Exception as e:
        return jsonify({"success": False, "info": "发送邮件时出错，请稍后重试"})


@app.route("/preview")
def preview():
    """Preview a text file's content."""
    filepath = request.args.get("path", "")

    if not filepath:
        return jsonify({"error": "No path provided"}), 400

    # Security check: only allow files within search roots
    if not is_path_allowed(filepath):
        return jsonify({"error": "Access denied"}), 403

    if not os.path.isfile(filepath):
        return jsonify({"error": "File not found"}), 404

    ext = os.path.splitext(filepath)[1].lower()
    text_exts = [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".log", ".xml", ".csv"]

    if ext in text_exts:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)
            return jsonify({"content": content, "type": "text"})
        except Exception as e:
            return jsonify({"error": "Cannot read file"}), 500
    else:
        return jsonify({"content": "（暂不支持预览此类型文件）", "type": "binary"})


@app.route("/reset", methods=["POST"])
def reset():
    """Reset conversation history."""
    agent.reset()
    return jsonify({"ok": True})


@app.route("/health")
def health():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "ok"})


@app.route("/settings")
def settings_page():
    return render_template("settings.html")

@app.route("/api/config", methods=["GET", "POST"])
def manage_config():
    if request.method == "GET":
        try:
            with open(_config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # 隐藏敏感信息如只需要展示配置
            return jsonify({
                "dashscope_api_key": cfg.get("dashscope_api_key", ""),
                "natapp_token": cfg.get("natapp_token", ""),
                "email_sender": cfg.get("email", {}).get("sender", ""),
                "email_password": cfg.get("email", {}).get("password", "")
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    elif request.method == "POST":
        try:
            data = request.get_json()
            with open(_config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                
            # Update specific fields
            if "dashscope_api_key" in data:
                cfg["dashscope_api_key"] = data["dashscope_api_key"]
            if "natapp_token" in data:
                cfg["natapp_token"] = data["natapp_token"]
            
            email_cfg = cfg.get("email", {})
            if "email_sender" in data:
                email_cfg["sender"] = data["email_sender"]
            if "email_password" in data:
                email_cfg["password"] = data["email_password"]
            cfg["email"] = email_cfg
            
            with open(_config_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
                
            return jsonify({"status": "ok", "message": "配置已保存！需要重启 start.bat 才能使某些配置完全生效。"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = _config.get("web_port", 5000)
    host = _config.get("web_host", "0.0.0.0")

    # Get local IP for display
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "你的IP"

    print(f"\n{'='*50}")
    print(f"  文件助手 Agent 已启动！")
    print(f"  本机访问：  http://localhost:{port}")
    print(f"  局域网访问：http://{local_ip}:{port}")
    print(f"{'='*50}\n")
    app.run(host=host, port=port, debug=False, threaded=True)
