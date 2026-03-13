# Integrity Lab 项目部署进度文档

**最后更新时间：** 2026-03-13 17:25  
**文档版本：** v1.0

---

## 📊 项目总览

### 目标
部署8个典型项目的完整功能（Demo演示 + 在线工具 + 源码介绍）

### 目标项目列表
1. ✅ **18tokens** - Token消耗对比工具
2. ⏳ **20AIer-xhs** - 小红书图文生成器
3. ⏳ **源码浏览页面** - 包含所有integrity项目

---

## ✅ 已完成工作

### 阶段1：18tokens Token消耗对比工具

**完成时间：** 2026-03-13  
**状态：** ✅ 已部署上线

#### 1.1 开发内容

**后端API：**
- 文件：`docs/server/app/tools/token_compare.py`
- 端点：`POST /api/tools/token-compare/analyze`
- 功能：
  - 支持中英文文本、图片三种输入模式
  - 支持7个模型：qwen-turbo/plus/max/vl-plus, gpt-4o/4o-mini/4-turbo
  - 返回token消耗明细和预估费用
  - 使用tiktoken库精确计算token数量

**前端Demo页面：**
- 文件：`docs/demos/token-compare.html`
- 功能：
  - 三种输入方式切换（中文/英文/图片）
  - 模型多选
  - 实时计算并展示结果
  - 响应式设计

**路由注册：**
- 文件：`docs/server/app/main.py`
- 修改：添加token_compare_bp蓝图注册

#### 1.2 技术栈
- Python 3.13
- Flask + Blueprint
- tiktoken 0.12.0（token计算）
- Vanilla JavaScript（前端）

#### 1.3 测试结果

**本地测试：**
```bash
cd docs/server/app/tools
python token_compare.py
# 输出：
# qwen-turbo: 18 tokens
# qwen-plus: 18 tokens
# gpt-4o: 14 tokens
```

**服务器测试：**
```bash
curl -X POST http://8.138.164.133:5000/api/tools/token-compare/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"hello","language":"zh","models":["qwen-turbo"]}'

# 响应：
{
  "success": true,
  "results": [{
    "model": "qwen-turbo",
    "prompt_tokens": 1,
    "completion_tokens": 12,
    "total_tokens": 13,
    "estimated_cost": 0.000007
  }]
}
```

#### 1.4 部署过程

**步骤：**
1. ✅ 本地开发完成
2. ✅ 提交到GitHub：`git commit -m "feat: add 18tokens token comparison tool"`
3. ✅ 服务器同步代码：`cd /root/integrity-github && git pull`
4. ✅ 安装依赖：`pip install tiktoken`
5. ✅ **关键步骤**：复制文件到API服务目录
   ```bash
   cp /root/integrity-github/docs/server/app/tools/token_compare.py \
      /root/integrity-api/server/app/tools/
   cp /root/integrity-github/docs/server/app/main.py \
      /root/integrity-api/server/app/main.py
   ```
6. ✅ 重启服务：`pkill gunicorn && gunicorn ...`

#### 1.5 访问地址
- Demo页面：https://zhimingliang897-web.github.io/integrity/demos/token-compare.html
- API端点：http://8.138.164.133:5000/api/tools/token-compare/analyze

---

## ⚠️ 遇到的问题与解决方案

### 问题1：API一直返回404

**原因：**
- 服务器上有两个integrity相关目录：
  - `/root/integrity-github` - GitHub仓库，仅用于代码同步
  - `/root/integrity-api/server` - 实际运行的API服务
- 新文件只同步到了GitHub仓库，没有复制到API服务目录

**解决方案：**
```bash
# 手动复制文件
cp /root/integrity-github/docs/server/app/tools/token_compare.py \
   /root/integrity-api/server/app/tools/
cp /root/integrity-github/docs/server/app/main.py \
   /root/integrity-api/server/app/main.py
```

**教训：**
- `git pull` 只更新GitHub仓库，不等于服务部署
- 需要额外的文件复制步骤
- 建议创建自动化部署脚本

### 问题2：服务器Worker超时

**现象：**
```
[CRITICAL] WORKER TIMEOUT (pid:1582450)
[ERROR] Worker (pid:1582450) exited with code 1
```

**原因：**
- Worker进程超时（默认30秒）
- 可能是请求处理时间过长

**解决方案：**
- 暂时通过重启服务解决
- 后续需要优化性能或增加超时时间

---

## ⏳ 待完成工作

### 阶段2：20AIer-xhs 小红书图文生成器

**预计工作量：** 2天  
**优先级：** 高

#### 2.1 需求分析

**功能：**
- 输入：普通文章文本
- 输出：
  - 1张封面图（1080×1440 px）
  - 4-6张内容图（毒舌风格）
  - 评论区文案（3条建议 + 5个标签）

**技术方案：**
- LLM：阿里云Qwen（生成毒舌文案）
- 图片渲染：Pillow
- 字体：自动检测系统中文字体
- 存储：服务器临时目录，定期清理

#### 2.2 开发任务

**后端API：**
- [ ] 创建 `docs/server/app/tools/xhs_generator.py`
- [ ] 实现LLM文案生成
- [ ] 实现Pillow图片渲染
- [ ] 创建输出目录 `/root/integrity-api/server/outputs/xhs/`
- [ ] 添加静态文件服务路由
- [ ] 注册蓝图

**前端Demo：**
- [ ] 更新 `docs/demos/xhs-image-generator.html`
- [ ] 添加实时预览
- [ ] 添加下载功能

**部署：**
- [ ] 复制依赖文件（字体、毒舌skill.md）
- [ ] 测试API
- [ ] 更新文档

#### 2.3 配置要点
- 图片存储策略：临时存储，每周清理
- 文件命名：`{uuid}_slide_{index}.png`
- 最大图片数：6张

---

### 阶段3：源码浏览页面

**预计工作量：** 1天  
**优先级：** 高

#### 3.1 需求分析

**页面：** `docs/tools.html` 第三个Tab

**展示内容：**
- 包含integrity所有项目（18+个）
- 每个项目显示：
  - 项目名称
  - 简短描述
  - 部署状态（✅已部署 / 🔵本地工具 / 🟡部署中）
  - Demo链接（如有）
  - GitHub源码链接

#### 3.2 开发任务

- [ ] 收集所有项目信息
- [ ] 设计卡片样式
- [ ] 更新tools.html
- [ ] 测试所有链接
- [ ] 提交到GitHub

#### 3.3 项目数据示例

| 项目 | 状态 | Demo链接 | GitHub链接 |
|------|------|---------|-----------|
| 1分镜 - 视频生成器 | ✅ 已部署 | demos/video-maker.html | tree/main/1分镜 |
| 18tokens - Token对比 | ✅ 已部署 | demos/token-compare.html | tree/main/18tokens |
| 20AIer-xhs - 小红书图文 | 🟡 部署中 | demos/xhs-image-generator.html | tree/main/20AIer-xhs |

---

## 📋 部署检查清单

### 新功能部署流程

#### 开发阶段
- [ ] 本地开发完成
- [ ] 本地测试通过
- [ ] 代码提交到GitHub

#### 部署阶段
- [ ] SSH连接服务器
- [ ] 拉取最新代码：`cd /root/integrity-github && git pull`
- [ ] **关键：复制文件到API目录**
  ```bash
  cp /root/integrity-github/docs/server/app/tools/[新文件].py \
     /root/integrity-api/server/app/tools/
  ```
- [ ] 安装新依赖（如有）
- [ ] 重启服务
- [ ] 测试API
- [ ] 更新文档

#### 回滚方案
```bash
# 如果出现问题
cd /root/integrity-api/server/app/tools
rm [新文件].py
cd /root/integrity-api/server/app
git checkout main.py
pkill gunicorn && gunicorn ...
```

---

## 🗂️ 服务器目录结构

```
/root/
├── integrity-github/          # GitHub仓库（只读）
│   └── docs/server/
│       └── app/tools/
│           ├── token_compare.py
│           └── ...
│
└── integrity-api/             # 实际运行的API服务
    └── server/
        ├── app/
        │   ├── main.py
        │   └── tools/
        │       ├── token_compare.py  ← 需要复制
        │       └── ...
        └── outputs/           # 输出文件目录
            └── xhs/           # 小红书图片（待创建）
```

---

## 🔧 常用命令

### 服务器管理

```bash
# SSH连接
ssh root@8.138.164.133

# 查看服务状态
ps aux | grep gunicorn

# 重启服务
cd /root/integrity-api
pkill gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 app.main:app --daemon \
  --chdir /root/integrity-api/server \
  --env SECRET_KEY=integrity-lab-secret-2026 \
  --env DASHSCOPE_API_KEY=sk-xxx \
  --env INVITE_CODES=demo2026,friend2026,test2026

# 查看日志
tail -f /root/integrity-api/server/gunicorn.error.log

# 测试API
curl -X POST http://localhost:5000/api/tools/[端点] \
  -H "Content-Type: application/json" \
  -d '{"key":"value"}'
```

### Git操作

```bash
# 提交代码
git add .
git commit -m "feat: xxx"
git push origin main

# 查看状态
git status
git log --oneline -5
```

---

## 📊 进度追踪

### 总体进度

| 阶段 | 任务 | 状态 | 完成时间 |
|------|------|------|---------|
| 阶段1 | 18tokens工具 | ✅ 完成 | 2026-03-13 |
| 阶段2 | 20AIer-xhs工具 | ⏳ 进行中 | - |
| 阶段3 | 源码浏览页面 | ⏳ 待开始 | - |

### 统计数据

- **已部署项目：** 7个（原6个 + 18tokens）
- **待部署项目：** 2个
- **总代码行数：** 约800行（18tokens）
- **总耗时：** 约3小时（含排查问题）

---

## 📝 注意事项

### 部署注意事项

1. **文件路径混淆**
   - GitHub仓库 ≠ API服务目录
   - 必须手动复制文件

2. **服务重启**
   - 修改代码后必须重启gunicorn
   - 使用`pkill gunicorn`确保完全停止

3. **依赖管理**
   - 新Python库需要pip install
   - 建议在requirements.txt中记录

4. **测试验证**
   - 本地测试 → 服务器API测试 → 前端集成测试
   - 记录所有测试用例

### 开发注意事项

1. **代码风格**
   - 遵循现有代码规范
   - 添加适当的错误处理
   - 编写清晰的文档字符串

2. **性能优化**
   - 控制并发请求数
   - 添加超时控制
   - 优化大文件处理

3. **安全考虑**
   - 不在代码中硬编码密钥
   - 使用环境变量
   - 验证用户输入

---

## 🎯 下一步计划

### 近期任务（本周）
1. ✅ 完成18tokens部署
2. ⏳ 开始20AIer-xhs开发
3. ⏳ 准备项目数据收集

### 中期任务（下周）
1. ⏳ 完成20AIer-xhs部署
2. ⏳ 开发源码浏览页面
3. ⏳ 创建自动化部署脚本

### 长期优化
1. 创建CI/CD流程
2. 添加监控告警
3. 优化服务器性能
4. 编写用户文档

---

## 📞 联系方式

- **GitHub：** https://github.com/zhimingliang897-web/integrity
- **服务器：** 8.138.164.133:5000
- **在线地址：** https://zhimingliang897-web.github.io/integrity/

---

## 📄 变更日志

### v1.0 (2026-03-13)
- 完成18tokens工具部署
- 发现并解决部署路径问题
- 创建部署文档
- 规划后续任务

---

**文档维护者：** Claude  
**文档状态：** 活跃更新中