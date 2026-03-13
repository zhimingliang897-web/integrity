# 私人文件系统 v1

一个智能的私人文件管理系统，支持文件上传、下载、搜索、预览，并集成了 LLM Agent，可以用自然语言操作文件。

## 功能特性

- **文件管理**: 上传、下载、删除、移动、重命名、新建文件夹
- **文件预览**: 支持图片、视频、音频、PDF、文本等格式在线预览
- **智能搜索**: 关键词搜索、类型筛选、高级搜索
- **AI Agent**: 用自然语言操作文件（如"找上周的合同"、"把所有PDF整理到文档文件夹"）
- **回收站**: 删除文件移入回收站，支持恢复和彻底删除
- **批量操作**: 批量删除、下载、移动
- **密码保护**: 简单安全的单密码认证
- **内网穿透**: 支持 natapp 内网穿透，随时随地访问
- **邮件发送**: 支持将文件直接发送到邮箱

## 项目结构

```
14.1file-agent-v1/
├── app.py                 # FastAPI 主入口
├── config.json            # 配置文件（需自行配置）
├── config.example.json    # 配置示例
├── requirements.txt       # Python 依赖
├── start.bat              # Windows 启动脚本
├── natapp.exe             # 内网穿透工具
│
├── app/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── security.py        # 认证安全
│   └── deps.py            # 依赖注入
│
├── models/                # 数据模型
├── services/              # 业务逻辑
├── routers/               # API 路由
├── templates/             # 前端页面
├── static/                # 静态资源
└── data/                  # SQLite 数据库
```

## 存储目录结构

```
F:\MyFiles\                # 根目录（可在配置中修改）
├── 多媒体\                # 多媒体文件
├── 文档\                  # 文档文件
├── uploads\               # 上传文件临时目录
└── .trash\                # 回收站
```

## 安装步骤

### 1. 创建 Conda 环境

```bash
conda create -n file-agent python=3.11 -y
conda activate file-agent
```

### 2. 进入项目目录

```bash
cd 14.1file-agent-v1
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置文件

复制配置模板并修改：

```bash
copy config.example.json config.json
```

**需补充的隐私/本地配置（未随仓库提交）**  
- 文件名：**config.json**（对他人：复制 `config.example.json` 为 `config.json` 后编辑；样式：JSON，含 storage、auth、llm、natapp、smtp 等）。  
- 自己使用：从 **`_secrets/14.1file-agent-v1/config.json`** 拷贝到本目录（文件名不变）即可。

编辑 `config.json` 填入你的配置：

```json
{
  "storage": {
    "root": "F:\\MyFiles",
    "uploads": "F:\\MyFiles\\uploads",
    "trash": "F:\\MyFiles\\.trash"
  },
  "auth": {
    "password": "your_password",
    "session_secret": "random-string-for-encryption",
    "session_expire_hours": 24
  },
  "llm": {
    "api_key": "your-dashscope-api-key",
    "model": "qwen-plus",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
  },
  "natapp": {
    "token": "your-natapp-token",
    "enabled": true
  },
  "email": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "sender": "your-email@qq.com",
    "password": "your-email-auth-code"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

### 5. 启动服务

**方式一：使用启动脚本（推荐）**

```bash
start.bat
```

**方式二：手动启动**

```bash
conda activate file-agent
python app.py
```

### 6. 访问系统

- **本地访问**: http://localhost:5000
- **局域网访问**: http://你的IP:5000
- **外网访问**: 启动 natapp 后控制台会显示外网地址
- **API 文档**: http://localhost:5000/docs

## 配置说明

### 必需配置

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| `auth.password` | 登录密码 | 自定义 |
| `llm.api_key` | 阿里百炼 API Key | [阿里云百炼控制台](https://bailian.console.aliyun.com/) |
| `natapp.token` | Natapp 穿透 Token | [Natapp 官网](https://natapp.cn/) |

### 可选配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `server.port` | 服务端口 | 5000 |
| `upload.max_size_mb` | 最大上传大小 | 2048 (2GB) |
| `llm.model` | 使用的模型 | qwen-plus |
| `email.*` | 邮件发送配置 | 无 |

### 阿里百炼 API Key 获取

1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 开通服务（有免费额度）
3. 点击左侧「API-KEY 管理」
4. 创建新的 API Key

### Natapp 内网穿透配置

1. 访问 [Natapp 官网](https://natapp.cn/) 注册账号
2. 点击「购买隧道」→「免费隧道」（或付费获得固定域名）
3. 获取 Authtoken
4. 填入配置文件的 `natapp.token`

### QQ 邮箱配置（用于发送文件）

1. 登录 [QQ 邮箱](https://mail.qq.com/)
2. 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
3. 开启 SMTP 服务
4. 发送短信获取 16 位授权码
5. 填入配置文件的 `email.password`

## 使用指南

### 登录

- 默认密码：`admin123`（可在配置中修改）

### 文件操作

- **上传**: 点击「上传」按钮，支持拖拽和多文件
- **下载**: 点击文件行的下载按钮，支持批量下载
- **删除**: 点击删除按钮，文件移入回收站
- **预览**: 点击文件名，支持图片/视频/音频/PDF/文本预览
- **新建文件夹**: 点击「新建文件夹」按钮

### AI 助手使用

点击左侧「AI助手」，输入自然语言指令：

**示例指令**：

- "帮我找所有PDF文件"
- "搜索包含'合同'的文档"
- "看看D盘有什么"
- "把前两个文件发到 xxx@qq.com"

### 快捷分类

左侧边栏提供快捷分类：

- 图片：`.jpg` `.png` `.gif` `.webp` 等
- 视频：`.mp4` `.avi` `.mov` 等
- 文档：`.pdf` `.doc` `.docx` `.xls` `.xlsx` 等
- 音频：`.mp3` `.wav` `.flac` 等

## API 文档

启动后访问 http://localhost:5000/docs 查看 Swagger API 文档

### 主要 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录认证 |
| POST | `/api/auth/logout` | 退出登录 |
| GET | `/api/files` | 列出文件列表 |
| POST | `/api/files/upload` | 上传文件 |
| GET | `/api/files/download` | 下载文件 |
| DELETE | `/api/files` | 删除文件（移入回收站） |
| POST | `/api/files/move` | 移动文件 |
| PUT | `/api/files/rename` | 重命名文件 |
| POST | `/api/files/folder` | 新建文件夹 |
| GET | `/api/search` | 搜索文件 |
| GET | `/api/preview` | 预览文件 |
| GET | `/api/trash` | 查看回收站 |
| POST | `/api/trash/restore` | 恢复文件 |
| DELETE | `/api/trash` | 彻底删除 |
| POST | `/api/agent/chat` | AI 对话 |

## 常见问题

### Q: 启动失败，提示端口被占用？

修改 `config.json` 中的 `server.port` 为其他端口。

### Q: AI 助手不工作？

检查 `llm.api_key` 是否正确配置，确保阿里百炼服务已开通。

### Q: 内网穿透不工作？

1. 检查 `natapp.token` 是否正确
2. 确保 `natapp.exe` 存在于项目目录
3. 检查 Natapp 账户是否有有效隧道

### Q: 邮件发送失败？

1. 检查邮箱配置是否正确
2. 确保使用的是邮箱授权码而非登录密码
3. 检查 SMTP 服务器地址和端口

### Q: 无法上传大文件？

默认限制 2GB，可在配置中修改 `upload.max_size_mb`。

## 技术栈

- **后端**: Python 3.11 + FastAPI + SQLAlchemy
- **数据库**: SQLite
- **前端**: 原生 HTML/CSS/JavaScript
- **LLM**: 阿里云百炼 (qwen-plus)
- **内网穿透**: Natapp

## 注意事项

1. **安全**: 首次使用请修改默认密码
2. **文件安全**: 删除的文件会进入回收站，可恢复
3. **隐私**: API Key 等敏感信息请妥善保管
4. **备份**: 重要数据请定期备份

## License

MIT