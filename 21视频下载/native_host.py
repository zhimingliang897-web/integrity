#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Native Messaging Host - 21视频下载器
Chrome 插件通过 Native Messaging 直接调用此脚本触发 yt-dlp 下载
无需启动任何服务器！
"""

import sys
import json
import struct
import os
import subprocess
import threading
import logging

# 日志写到文件（不能用 stdout，那是给 Chrome 用的）
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'native_host.log')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# 项目根目录（脚本在 21视频下载/ 下）
ROOT = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(ROOT, 'downloads')
COOKIES_FILE = os.path.join(ROOT, 'cookies.txt')

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ── Chrome Native Messaging 协议 ──────────────────
def read_message():
    """从 stdin 读取一条 Native Message（4字节长度 + JSON body）"""
    raw_len = sys.stdin.buffer.read(4)
    if not raw_len or len(raw_len) < 4:
        return None
    msg_len = struct.unpack('<I', raw_len)[0]
    raw_msg = sys.stdin.buffer.read(msg_len)
    return json.loads(raw_msg.decode('utf-8'))


def send_message(data):
    """向 stdout 写一条 Native Message"""
    encoded = json.dumps(data, ensure_ascii=False).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('<I', len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


# ── 下载逻辑 ──────────────────────────────────────
def build_cmd(url):
    """构建 yt-dlp 命令"""
    cmd = [
        'yt-dlp',
        '-P', DOWNLOAD_DIR,
        '-f', 'bestvideo+bestaudio/best',
        '--merge-output-format', 'mp4',
        '--no-playlist',
        '-o', '%(title)s.%(ext)s',
    ]
    if os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 50:
        cmd += ['--cookies', COOKIES_FILE]
    cmd.append(url)
    return cmd


def download_async(url):
    """后台线程执行下载，立即返回不阻塞"""
    def run():
        cmd = build_cmd(url)
        logging.info(f'下载开始: {url}')
        logging.info(f'命令: {" ".join(cmd)}')
        try:
            # Windows 上用 CREATE_NO_WINDOW 避免弹黑框
            flags = 0
            if sys.platform == 'win32':
                flags = subprocess.CREATE_NO_WINDOW
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=flags
            )
            out, _ = proc.communicate()
            if proc.returncode == 0:
                logging.info(f'下载成功: {url}')
            else:
                logging.error(f'下载失败 (code={proc.returncode}): {out.decode("utf-8", errors="ignore")[-500:]}')
        except Exception as e:
            logging.exception(f'下载异常: {e}')

    t = threading.Thread(target=run, daemon=True)
    t.start()


# ── 主循环 ────────────────────────────────────────
def main():
    logging.info('Native Host 启动')
    while True:
        msg = read_message()
        if msg is None:
            logging.info('stdin 关闭，退出')
            break

        logging.debug(f'收到消息: {json.dumps(msg)[:200]}')

        # ping 测试
        if msg.get('url') == '__ping__':
            send_message({'ok': True, 'version': '2.0'})
            continue

        # 检查 cookies.txt 是否存在
        if msg.get('checkCookies'):
            has = os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 50
            send_message({'ok': True, 'hasCookies': has})
            continue

        # 保存 cookies
        if 'saveCookies' in msg:
            try:
                with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                    f.write(msg['saveCookies'])
                send_message({'ok': True, 'message': 'cookies 已保存'})
            except Exception as e:
                send_message({'ok': False, 'error': str(e)})
            continue

        # 触发下载
        url = msg.get('url', '').strip()
        if url and url.startswith('http'):
            download_async(url)
            send_message({
                'ok': True,
                'message': f'下载已开始',
                'downloadDir': DOWNLOAD_DIR
            })
        else:
            send_message({'ok': False, 'error': '无效的 URL'})


if __name__ == '__main__':
    main()
