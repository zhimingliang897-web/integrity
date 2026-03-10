import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
server = root / "server.js"

if not server.exists():
  print("找不到 server.js")
  sys.exit(1)

node_cmd = os.environ.get("NODE_BIN", "node")
port = os.environ.get("PORT", "").strip()
if len(sys.argv) > 1:
  port = sys.argv[1].strip()

env = os.environ.copy()
if port:
  env["PORT"] = port

try:
  subprocess.run([node_cmd, str(server)], check=True, env=env)
except FileNotFoundError:
  print("未找到 node，请先安装 Node.js 或设置 NODE_BIN")
  sys.exit(1)
except subprocess.CalledProcessError as exc:
  sys.exit(exc.returncode or 1)
