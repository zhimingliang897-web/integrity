# CourseDigest - 开发日志

## 项目概述

将英文录播课视频自动转录并分析，输出中文"考试导向学习指南"。

**Pipeline：** 视频(.mp4) → faster-whisper 转录 → PPT/PDF 提取 → Groq API 分析 → Markdown 学习指南

---

## v0.1.0 — 初始构建（2026-02-21）

### 新增文件

| 文件 | 职责 |
|------|------|
| `config.py` | 全局配置（路径、模型、API Key） |
| `prompts.py` | LLM Prompt 模板管理 |
| `transcribe.py` | faster-whisper 转录 + 缓存 |
| `extract.py` | PDF/PPTX 文本提取（纯本地脚本） |
| `analyze.py` | Groq API 调用 + 分块分析逻辑 |
| `main.py` | 命令行主入口，串联全流程 |
| `README.md` | 使用说明 |
| `requirements.txt` | Python 依赖列表 |
| `input/` `cache/` `output/` | 目录结构 |

### 技术选型

- **转录**：`faster-whisper`（本地，完全免费）
- **材料提取**：`pdfplumber` + `python-pptx`（本地脚本）
- **AI 分析**：Groq API（免费额度，Llama-3.3-70B）
- **GPU 检测**：`ctranslate2`（faster-whisper 依赖，无需额外安装 torch）

---

## v0.2.0 — Bug 修复（2026-02-21）

### 修复：`ModuleNotFoundError: No module named 'torch'`

- **原因**：GPU 检测代码 `import torch` 而 torch 未安装
- **修复**：改用 `ctranslate2.get_cuda_device_count()` 检测 GPU，无需 torch

### 新增：`input/` 文件夹支持

- 新增 `input/` 目录作为视频和辅助材料的默认存放位置
- `main.py` 中 `resolve()` 函数：传入文件名时自动在 `input/` 中查找
- 用法：`python main.py 6.mp4 --ppt 4.pdf`（文件放 `input/` 里，直接写名字即可）

---

## v0.3.0 — 内存溢出修复（2026-02-21）

### 修复：`_ArrayMemoryError: Unable to allocate 3.50 GiB`

- **原因**：faster-whisper 一次性把 3 小时音频全部加载进内存做 FFT，需要 3.5GB
- **修复**：引入 `ffmpeg` 将视频按 **30 分钟** 切成临时 WAV 段，逐段处理后合并时间戳
- **峰值内存**：从 3.5GB 降至约 300MB
- **新增系统依赖**：`ffmpeg`（`conda install -c conda-forge ffmpeg`）
- **新增函数**：
  - `_get_duration()` — ffprobe 获取视频时长
  - `_extract_wav()` — ffmpeg 截取音频段为 16kHz 单声道 WAV

---

## v0.4.0 — CUDA 兼容性改进（2026-02-21）

### 修复：`RuntimeError: Library cublas64_12.dll is not found`

- **原因**：系统检测到 NVIDIA GPU，但 CUDA 12 运行库（cuBLAS/cuDNN）未安装
- **修复策略**：多级精度自动降级
  ```
  cuda/float16 → cuda/int8_float16 → cuda/int8 → cpu/float32
  ```
- 每级失败时打印具体原因，最终成功的精度会显示在日志中
- 转录循环中追加保护：运行时 CUDA 错误也会触发 CPU 降级

### 新增：`WHISPER_COMPUTE_TYPE` 配置项

- 在 `config.py` 中可手动指定精度，绕过自动检测
- `"auto"`（默认）= GPU 时 float16，CPU 时 float32

---

## 当前状态

### 已验证可用 ✅

- PDF 提取（`pdfplumber`）正常
- 视频文件自动从 `input/` 目录查找
- ffmpeg 分段处理解决内存问题
- CPU 模式转录可正常运行（慢）

### 已知问题 / 待完成 ⚠️

| 编号 | 问题 | 影响 | 解决方案 |
|------|------|------|----------|
| #1 | CUDA 12 运行库缺失（`cublas64_12.dll`） | GPU 加速不可用，转录速度慢 | `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12` 或安装 CUDA Toolkit 12 |
| #2 | Groq API Key 未配置 | AI 分析阶段无法运行 | 注册 [console.groq.com](https://console.groq.com) 获取 Key，设置环境变量 `GROQ_API_KEY` |
| #3 | 完整 Pipeline 尚未端到端测试 | 转录 → 分析 → 输出 未验证 | 等转录完成或修复 CUDA 后运行完整流程 |
| #4 | PPTX 未测试（目前只测了 PDF） | PPT 提取可能有问题 | 提供 .pptx 文件后验证 |

### 下一步操作建议

1. **修复 CUDA**（优先）
   ```bash
   pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
   # 重启终端后重跑
   ```

2. **配置 Groq API Key**
   ```bash
   set GROQ_API_KEY=your_key_here
   ```

3. **验证完整 Pipeline**
   ```bash
   python main.py 6.mp4 --ppt 4.pdf --syllabus syllabus.pdf --exams past_exams.pdf
   ```

4. **检查 `output/6_学习指南.md`** 是否符合预期
