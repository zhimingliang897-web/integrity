import smtplib
import os
import json
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.utils import formataddr


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def encode_filename(filename):
    """Encode filename for email attachment header (handle Chinese characters)."""
    try:
        filename.encode('ascii')
        # Pure ASCII, can use directly
        return f'"{filename}"'
    except UnicodeEncodeError:
        # Contains non-ASCII, use RFC 2231 encoding
        encoded = Header(filename, 'utf-8').encode()
        return encoded


def is_valid_email(email):
    """Basic email format validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def send_file_email(recipient, filepaths, message=""):
    """
    Send files as email attachments.

    Args:
        recipient: recipient email address
        filepaths: list of absolute file paths to attach
        message: optional message body

    Returns:
        (success: bool, info: str)
    """
    # Validate recipient
    if not recipient or not is_valid_email(recipient):
        return False, "收件邮箱地址格式不正确，请检查后重试"

    config = load_config()
    email_cfg = config.get("email", {})

    smtp_server = email_cfg.get("smtp_server", "smtp.qq.com")
    smtp_port = email_cfg.get("smtp_port", 465)
    sender = email_cfg.get("sender", "")
    password = email_cfg.get("password", "")

    if not sender or not password or password == "FILL_IN_QQ_SMTP_AUTH_CODE_HERE":
        return False, "邮件未配置：请先在 config.json 中填写 QQ 邮箱的 SMTP 授权码（不是登录密码）"

    # Check file sizes
    MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024  # 20MB total
    valid_files = []
    skipped = []
    total_size = 0

    for fp in filepaths:
        if not fp or not isinstance(fp, str):
            continue
        if not os.path.isfile(fp):
            skipped.append(f"{os.path.basename(fp) if fp else '未知文件'}（不存在）")
            continue
        try:
            size = os.path.getsize(fp)
            if total_size + size > MAX_ATTACHMENT_SIZE:
                skipped.append(f"{os.path.basename(fp)}（超出20MB限制）")
            else:
                valid_files.append(fp)
                total_size += size
        except OSError:
            skipped.append(f"{os.path.basename(fp)}（无法读取）")

    if not valid_files:
        return False, "没有可发送的文件（文件不存在或超出大小限制）"

    # Build email
    msg = MIMEMultipart()
    msg["From"] = formataddr(("文件助手", sender))
    msg["To"] = recipient

    # Subject with file count
    if len(valid_files) == 1:
        subject = f"文件助手：{os.path.basename(valid_files[0])}"
    else:
        subject = f"文件助手：{len(valid_files)} 个文件"
    msg["Subject"] = Header(subject, "utf-8")

    # Body
    filenames_list = "\n".join([f"  • {os.path.basename(f)}" for f in valid_files])
    if message:
        body = f"{message}\n\n附件文件：\n{filenames_list}"
    else:
        body = f"你好，\n\n以下是你请求的文件：\n{filenames_list}\n\n此邮件由文件助手自动发送。"

    if skipped:
        body += f"\n\n⚠️ 以下文件未能发送：\n" + "\n".join([f"  • {s}" for s in skipped])

    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Attach files
    for fp in valid_files:
        try:
            with open(fp, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)

            filename = os.path.basename(fp)
            # Use RFC 2231 for non-ASCII filenames
            try:
                filename.encode('ascii')
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=filename
                )
            except UnicodeEncodeError:
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=("utf-8", "", filename)
                )
            msg.attach(part)
        except Exception as e:
            skipped.append(f"{os.path.basename(fp)}（读取失败）")

    # Send with timeout
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())

        result = f"✅ 已成功发送 {len(valid_files)} 个文件到 {recipient}"
        if skipped:
            result += f"\n⚠️ 跳过：{', '.join(skipped)}"
        return True, result

    except smtplib.SMTPAuthenticationError:
        return False, "❌ 邮箱认证失败：请检查 config.json 中的 SMTP 授权码是否正确"
    except smtplib.SMTPRecipientsRefused:
        return False, f"❌ 收件地址被拒绝：{recipient} 可能不存在或无法接收邮件"
    except smtplib.SMTPException as e:
        return False, f"❌ 邮件发送失败：{str(e)[:100]}"
    except TimeoutError:
        return False, "❌ 连接超时：请检查网络连接"
    except Exception as e:
        return False, f"❌ 发送失败：{str(e)[:100]}"
