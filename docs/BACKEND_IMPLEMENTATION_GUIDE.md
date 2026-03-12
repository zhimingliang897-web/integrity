# Integrity Lab 后端实现指南

本文档说明已有的 PDF 工具后端实现方式，以及需要实现后端 API 的 Demo 功能列表和实现计划。

---

## 一、PDF 工具实现架构分析

### 1.1 整体架构

```
前端页面 (tools.html + tools-pdf.js)
        ↓ HTTP 请求
后端服务 (Flask + Blueprint)
        ↓
PDF 处理 (pypdf, PyMuPDF, Pillow)
        ↓
文件下载 (临时文件 + 随机文件名)
```

### 1.2 后端核心文件

| 文件 | 作用 |
|------|------|
| `docs/server/app/main.py` | Flask 主入口，注册蓝图，用户认证 |
| `docs/server/app/tools/pdf.py` | PDF 工具蓝图，包含所有 PDF 处理 API |

### 1.3 认证机制

```python
# JWT Token 认证装饰器
def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': '请先登录'}), 401
        try:
            jwt.decode(token, secret, algorithms=['HS256'])
        except Exception:
            return jsonify({'error': 'Token 无效或已过期'}), 401
        return f(*args, **kwargs)
    return decorated
```

### 1.4 API 设计模式

每个 PDF 功能遵循统一模式：

```python
@pdf_bp.route('/endpoint', methods=['POST'])
@require_token
def api_function():
    # 1. 从 request.files 获取上传文件
    # 2. 从 request.form 获取参数
    # 3. 保存到临时目录处理
    # 4. 生成随机文件名的输出文件
    # 5. 返回 JSON: {success, message, download_url}
```

### 1.5 关键实现细节

| 要点 | 实现 |
|------|------|
| 临时文件目录 | `tempfile.gettempdir() + 'integrity_pdf'` |
| 安全文件名 | `os.urandom(4).hex() + secure_filename(原文件名)` |
| 文件下载 | `/api/tools/pdf/download/<filename>` 公开接口 |
| 路径安全 | `Path.resolve()` 检查防止目录穿越 |

### 1.6 前端调用示例

```javascript
async function pdfOp(op) {
    const token = localStorage.getItem('token');
    const fd = new FormData();
    fd.append('pdf', file);
    fd.append('pages', pagesInput.value);

    const res = await fetch(API_BASE + '/api/tools/pdf/' + op, {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token },
        body: fd
    });

    const data = await res.json();
    if (data.success) {
        // 显示下载链接: API_BASE + data.download_url
    }
}
```

---

## 二、需要后端实现的 Demo 列表

根据分析，以下 Demo 页面目前是**纯前端模拟**，需要实现真正的后端 API：

### 优先级 P0（核心功能，建议优先实现）

| Demo | 页面 | 后端功能 | 难度 |
|------|------|----------|------|
| **多模型对比** | `ai-compare.html` | 并发调用多个 AI 模型 API，返回各模型响应 | ⭐⭐⭐ |
| **AI 辩论赛** | `ai-debate.html` | SSE 流式输出，多模型轮流对话 | ⭐⭐⭐⭐ |
| **图文互转** | `image-prompt.html` | 图片→提示词（Qwen VL）、提示词→图片（文生图 API） | ⭐⭐⭐ |
| **分镜视频生成** | `video-maker.html` | AI 生成剧本 + 文生图 + TTS + FFmpeg 合成 | ⭐⭐⭐⭐⭐ |

### 优先级 P1（有价值功能）

| Demo | 页面 | 后端功能 | 难度 |
|------|------|----------|------|
| **台词学习** | `dialogue-learning.html` | PDF 解析 + 台词网站爬取 + AI 整理 + TTS | ⭐⭐⭐⭐ |
| **Token 对比** | `token-compare.html` | 已有部分，需扩展多模型实际测试 | ⭐⭐ |

### 优先级 P2（独立运行项目，可选在线化）

| Demo | 页面 | 说明 |
|------|------|------|
| **小红书内容生成** | `redbook-generator.html` | 本地 Python 脚本，Playwright 控制浏览器，不适合纯 API |
| **小红书图片生成** | `xhs-image-generator.html` | 本地 Python 脚本，可提取图片生成部分做成 API |
| **CourseDigest** | `course-digest.html` | 本地运行，Whisper 转录占用大，不建议云端 |
| **文件助手 Agent** | `file-agent.html` | 本地运行，访问本机文件系统 |
| **EasyApply 插件** | `easyapply.html` | 浏览器扩展，无需后端 |
| **大麦抢票** | `ticket-helper.html` | 本地运行，控制手机，私有项目 |

---

## 三、后端实现计划

### 3.1 多模型对比 (`/api/tools/ai-compare`)

**功能描述**：同时调用多个 AI 模型，对比同一问题的回答。

**API 设计**：

```python
@bp.route('/api/tools/ai-compare', methods=['POST'])
@require_token
def ai_compare():
    """
    请求体:
    {
        "question": "什么是机器学习？",
        "systemPrompt": "你是一个专业技术顾问",
        "temperature": 0.7,
        "provider": "Qwen",
        "model": "qwen-turbo"
    }

    响应:
    {
        "content": "机器学习是...",
        "provider": "Qwen",
        "model": "qwen-turbo"
    }
    """
```

**依赖**：
- `openai` SDK（兼容 OpenAI 格式的各家 API）
- 各厂商 API Key（通义、豆包、DeepSeek、Kimi、OpenAI）

**实现要点**：
1. 统一使用 OpenAI SDK 格式调用各家 API
2. 前端并发发起多个请求，后端单个请求处理单个模型
3. 记录响应时间用于对比

---

### 3.2 AI 辩论赛 (`/api/tools/ai-debate`)

**功能描述**：多个 AI 模型按辩论赛制轮流发言，SSE 流式输出。

**API 设计**：

```python
@bp.route('/api/tools/ai-debate/start', methods=['POST'])
@require_token
def start_debate():
    """
    请求体:
    {
        "topic": "人工智能的发展利大于弊",
        "rounds": 4
    }

    响应: SSE 流
    event: stage
    data: {"stage": "开篇立论", "desc": "双方一辩阐述观点"}

    event: message
    data: {"speaker": "千问·论道", "role": "正方一辩", "side": "pro", "content": "..."}

    event: result
    data: {"winner": "正方", "comment": "..."}
    """
```

**依赖**：
- Flask SSE 支持
- 多个 AI 模型 API

**实现要点**：
1. 使用 `flask.Response` + `text/event-stream` 实现 SSE
2. 每个辩手使用不同模型，传入不同的 system prompt 设定人设
3. 上下文传递：每轮发言都包含之前所有发言记录

---

### 3.3 图文互转 (`/api/tools/image-prompt`)

**功能描述**：
- 图片→提示词：上传图片，AI 分析生成描述
- 提示词→图片：输入文字，AI 生成图片

**API 设计**：

```python
# 图片转提示词
@bp.route('/api/tools/image-prompt/analyze', methods=['POST'])
@require_token
def analyze_image():
    """
    请求: FormData with 'image' file, 'style' (dalle/sd)
    响应: {"prompt": "A beautiful sunset..."}
    """

# 提示词转图片
@bp.route('/api/tools/image-prompt/generate', methods=['POST'])
@require_token
def generate_image():
    """
    请求: {"prompt": "...", "size": "1024x1024", "count": 1}
    响应: {"images": ["url1", "url2"]}
    """
```

**依赖**：
- Qwen VL API（图片分析）
- 通义万相 / Volcengine / DALL-E API（图片生成）

---

### 3.4 分镜视频生成 (`/api/tools/video-maker`)

**功能描述**：输入场景描述，AI 生成剧本→分镜插图→配音→字幕→视频。

**API 设计**：

```python
@bp.route('/api/tools/video-maker/generate', methods=['POST'])
@require_token
def generate_video():
    """
    请求:
    {
        "project_name": "咖啡店点单",
        "scene_description": "在咖啡店点一杯拿铁",
        "video_type": "multi"  # multi / grid
    }

    响应:
    {
        "task_id": "xxx",
        "status": "processing"
    }
    """

@bp.route('/api/tools/video-maker/status/<task_id>')
@require_token
def video_status(task_id):
    """
    响应:
    {
        "status": "completed",
        "progress": 100,
        "video_url": "/api/tools/video-maker/download/xxx.mp4"
    }
    """
```

**依赖**：
- Qwen Plus（剧本生成）
- 通义万相（分镜图片）
- Edge TTS（配音）
- FFmpeg（视频合成）
- Pillow（图片处理）

**实现要点**：
1. 异步任务处理（Celery 或简单的线程池）
2. 任务状态轮询
3. 临时文件管理

---

### 3.5 台词学习 (`/api/tools/dialogue-learning`)

**功能描述**：上传扇贝单词 PDF，提取单词，查询影视台词例句。

**API 设计**：

```python
@bp.route('/api/tools/dialogue-learning/process', methods=['POST'])
@require_token
def process_pdf():
    """
    请求: FormData with 'file' (PDF)
    响应: {"task_id": "xxx"}
    """

@bp.route('/api/tools/dialogue-learning/status/<task_id>')
@require_token
def task_status(task_id):
    """
    响应:
    {
        "status": "completed",
        "progress": 100,
        "results": {
            "words": [
                {
                    "word": "serendipity",
                    "phonetic": "/ˌserənˈdɪpəti/",
                    "audio_url": "...",
                    "quotes": [
                        {"source": "老友记 S01E01", "text": "...", "translation": "..."}
                    ]
                }
            ]
        }
    }
    """
```

**依赖**：
- pdfplumber（PDF 解析）
- BeautifulSoup（台词网站爬取）
- Qwen Plus（AI 整理）
- Edge TTS（语音合成）
- Free Dictionary API（音标查询）

---

## 四、新增后端工具的标准流程

### 4.1 创建工具蓝图

在 `docs/server/app/tools/` 下创建新文件，如 `ai_compare.py`：

```python
from flask import Blueprint, request, jsonify
from functools import wraps
import jwt

bp = Blueprint('ai_compare', __name__, url_prefix='/api/tools/ai-compare')

def require_token(f):
    # 复用认证装饰器
    ...

@bp.route('/query', methods=['POST'])
@require_token
def query():
    # 实现逻辑
    ...
```

### 4.2 注册蓝图

在 `main.py` 中添加：

```python
from app.tools.ai_compare import bp as ai_compare_bp
app.register_blueprint(ai_compare_bp)
```

### 4.3 前端调用

在对应的 demo 页面中：

```javascript
const API_BASE = 'https://api.liangyiren.top';

async function callAPI() {
    const token = localStorage.getItem('token');
    const res = await fetch(API_BASE + '/api/tools/ai-compare/query', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: '...' })
    });
    const data = await res.json();
}
```

---

## 五、技术栈汇总

| 类型 | 技术 |
|------|------|
| 后端框架 | Flask + Flask-CORS + Flask-SQLAlchemy |
| 认证 | JWT (PyJWT) |
| 数据库 | SQLite |
| 文件处理 | pypdf, PyMuPDF (fitz), Pillow |
| AI 模型 | OpenAI SDK (兼容各家 API) |
| 语音合成 | edge-tts |
| 视频处理 | FFmpeg |
| 任务队列 | Celery (可选) / 线程池 |

---

## 六、实现顺序建议

1. **第一阶段**：`ai-compare`（多模型对比）
   - 最常用功能，实现简单
   - 验证 OpenAI 兼容 API 调用方式

2. **第二阶段**：`image-prompt`（图文互转）
   - 视觉冲击力强，用户感知明显
   - 验证文生图 API 集成

3. **第三阶段**：`ai-debate`（AI 辩论）
   - SSE 流式输出，体验好
   - 复用 ai-compare 的模型调用逻辑

4. **第四阶段**：`dialogue-learning`（台词学习）
   - 涉及多个外部依赖，较复杂

5. **第五阶段**：`video-maker`（视频生成）
   - 最复杂，依赖 FFmpeg，需要异步任务

---

*文档最后更新：2026-03-13*
