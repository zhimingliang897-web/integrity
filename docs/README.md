# Integrity Lab - 项目文档

**GitHub Pages 托管的 AI 工具集合平台**

这是 Integrity Lab 的前端界面，展示 14 个 AI 工具项目，并提供在线使用功能。

---

## 🌐 访问地址

- **生产环境**：https://zhimingliang897-web.github.io/integrity/
- **后端 API**：https://api.liangyiren.top/
- **演示页面**：https://zhimingliang897-web.github.io/integrity/demos/

---

## 📋 项目结构

```
docs/
├── index.html                      # 首页
├── news.html                       # AI 热点页面
├── tools.html                      # 工具库页面
├── style.css                       # 全局样式
│
├── demos/                          # 演示页面目录
│   ├── index.html                 # 演示页面索引
│   ├── video-maker.html           # 分镜视频生成器
│   ├── dialogue-learning.html     # 台词学习工具
│   └── [更多演示页面...]
│
├── demos-assets/                   # 演示资源
│   ├── images/                    # 示例图片
│   ├── videos/                    # 示例视频
│   └── data/                      # 示例数据
│
├── tools-modules/                  # 工具模块
│   ├── demos-common.js            # 演示页面通用脚本
│   ├── tools-auth.js              # 认证模块
│   ├── tools-demo.js              # 演示功能
│   ├── tools-pdf.js               # PDF 工具
│   └── tools-styles.css           # 工具样式
│
├── data/                           # 数据文件
│   └── news.json                  # AI 热点数据
│
├── server/                         # 后端代码（本地备份）
│   ├── app/
│   │   ├── main.py                # API 主入口
│   │   └── tools/                 # 工具模块
│   └── data/
│       └── users.db               # 用户数据库
│
└── documentation/                  # 文档中心
    ├── AUTH_SYSTEM.md             # 认证系统说明
    ├── DEMO_QUICK_START.md        # 演示页面开发指南
    ├── PROJECT_PROGRESS_REPORT.md # 项目进度报告
    └── [更多文档...]
```

---

## 🎨 页面说明

### 1. 首页 (index.html)
- 项目介绍和理念
- AI 辩论赛演示
- 项目统计数据（14 个项目）
- 快速导航

### 2. AI 热点 (news.html)
- 每日 AI 资讯聚合
- 自动评级和摘要
- 数据来源：GitHub Actions 定时任务
- 无需登录即可查看

### 3. 工具库 (tools.html)
**演示区**（游客可见）：
- 图文互转演示
- 多模型对比演示
- Token 计算器演示

**在线工具区**（登录后可用）：
- PDF 工具集（7 个功能）
- 更多工具即将上线

**源码浏览区**（游客可见）：
- 14 个项目的源码链接
- 技术栈说明
- 项目描述

### 4. 演示页面 (demos/)
每个项目都有独立的演示页面：
- 功能演示和在线使用
- 详细的使用说明
- 示例展示
- 技术栈说明

**已完成的演示页面**：
- ✅ 分镜视频生成器
- ✅ 台词学习工具
- 🔄 更多演示页面开发中...

---

## 🔐 认证系统

### 快速开始

**测试账号**：
```
用户名：test
密码：123456
```

**注册新账号**：
1. 访问 https://zhimingliang897-web.github.io/integrity/tools.html
2. 点击"登录"按钮
3. 点击"注册"链接
4. 输入用户名、密码和邀请码

**有效邀请码**：
```
demo2026      # 演示账号专用
test2026      # 测试账号专用
friend2026    # 朋友分享专用
```

### 注册规则

**用户名**：
- 长度：3-20 个字符
- 允许：字母、数字、下划线
- 唯一性：不能重复

**密码**：
- 最小长度：6 位
- 建议：8 位以上，包含字母和数字

**邀请码**：
- 必须提供有效的邀请码
- 区分大小写
- 可重复使用

### 登录流程

1. 用户点击"登录"按钮
2. 输入用户名和密码
3. 前端发送请求到 API
4. 后端返回 JWT Token（有效期 7 天）
5. Token 存储在 `localStorage`
6. 后续请求在 Header 中携带 Token

### Token 管理

```javascript
// 存储 Token
localStorage.setItem('token', data.token);
localStorage.setItem('username', data.username);

// 使用 Token
const token = localStorage.getItem('token');
fetch(API_BASE + '/api/tools/pdf/merge', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + token },
    body: formData
});

// 退出登录
localStorage.removeItem('token');
localStorage.removeItem('username');
```

### 访问控制

**游客可访问**（无需登录）：
- ✅ 首页、AI 热点、工具库页面
- ✅ 演示区域（前端模拟）
- ✅ 源码浏览

**需要登录**：
- 🔒 所有在线工具
- 🔒 所有演示页面的实际功能
- 🔒 文件上传和处理
- 🔒 API 调用

> **详细说明**：查看 [AUTH_SYSTEM.md](AUTH_SYSTEM.md)

---

## 🛠️ 工具使用说明

### PDF 工具集

所有 PDF 工具都需要登录后使用。

**1. 图片转 PDF**
- 上传多张图片（支持 JPG、PNG 等）
- 可选：强制横向排列
- 下载生成的 PDF

**2. 合并 PDF**
- 上传至少 2 个 PDF 文件
- 按上传顺序合并
- 下载合并后的 PDF

**3. 删除页面**
- 上传 PDF
- 输入要删除的页码（如：1,3,5-8）
- 下载处理后的 PDF

**4. 插入 PDF**
- 上传主文档和要插入的文档
- 选择插入位置（最前/最后/指定页之前/之后）
- 下载处理后的 PDF

**5. 页面重排**
- 上传 PDF
- 自动将竖版页面移到横版页面前面
- 下载重排后的 PDF

**6. 统一尺寸**
- 上传 PDF
- 自动将所有横向页面统一为相同尺寸
- 下载处理后的 PDF

**7. PDF 转图片**
- 上传 PDF
- 设置页码范围、DPI、格式等
- 可选：合并为长图
- 下载图片（ZIP 或单张长图）

### Token 计算器

无需登录即可使用。

**功能**：
- 计算不同语言（中文/英文/带图）的 Token 消耗
- 对比不同模型的成本
- 帮助优化 Prompt 成本

---

## 🚀 本地开发

### 1. 启动本地服务器

由于使用了 `fetch` API，需要通过 HTTP 服务器访问：

```bash
# 方式一：Python
cd docs
python3 -m http.server 8000

# 方式二：Node.js
npx http-server docs -p 8000

# 方式三：VS Code Live Server 插件
# 右键 index.html -> Open with Live Server
```

### 2. 访问页面

打开浏览器访问：
- http://localhost:8000/index.html
- http://localhost:8000/news.html
- http://localhost:8000/tools.html
- http://localhost:8000/demos/index.html

### 3. 测试登录

使用测试账号：
- 用户名：test
- 密码：123456

或注册新账号（邀请码：demo2026）

---

## 🎯 API 配置

前端通过以下常量配置 API 地址：

```javascript
const API_BASE = 'https://api.liangyiren.top';
```

如需修改 API 地址，在各 HTML 文件的 `<script>` 标签中修改此常量。

### API 端点

**认证相关**：
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/verify` - Token 验证

**工具相关**：
- `POST /api/tools/pdf/*` - PDF 工具（需要登录）
- `POST /api/tools/token-calc` - Token 计算器（无需登录）

---

## 📝 开发指南

### 添加新的演示页面

1. **复制模板**
```bash
cp docs/demos/_template.html docs/demos/your-demo.html
```

2. **修改内容**
- 更新页面标题和描述
- 添加功能演示区
- 添加使用说明
- 添加示例展示

3. **使用通用工具函数**
```javascript
// 检查登录状态
const { token, isLoggedIn } = DemoUtils.checkAuth();

// 显示消息
DemoUtils.showMessage('操作成功', 'success');

// 上传文件
const result = await DemoUtils.uploadFile(file, '/api/endpoint');
```

4. **测试功能**
```bash
cd docs && python3 -m http.server 8000
open http://localhost:8000/demos/your-demo.html
```

> **详细指南**：查看 [DEMO_QUICK_START.md](DEMO_QUICK_START.md)

### 添加新工具

1. **在 tools.html 中添加 UI**
2. **编写 JavaScript 逻辑**
3. **后端实现对应 API**
4. **测试功能**

### 修改样式

全局样式在 `style.css` 中定义，使用 CSS 变量：

```css
:root {
    --bg-body: #0a0a0f;        /* 页面背景 */
    --bg-card: #13131a;        /* 卡片背景 */
    --border: #2a2a35;         /* 边框颜色 */
    --primary: #3b82f6;        /* 主色调 */
    --secondary: #8b5cf6;      /* 辅助色 */
    --text-primary: #ffffff;   /* 主文字 */
    --text-muted: #9ca3af;     /* 次要文字 */
}
```

---

## 🐛 常见问题

### 1. CORS 错误

**原因**：后端 API 未配置正确的 CORS 策略

**解决方案**：
```python
CORS(app, origins=[
    'https://zhimingliang897-web.github.io',
    'http://localhost:*'
])
```

### 2. Token 过期

**现象**：API 请求返回 401 错误

**解决方案**：
- Token 有效期为 7 天
- 过期后需要重新登录
- 检查 localStorage 中的 token

### 3. 文件上传失败

**可能原因**：
- 文件大小超过限制（100MB）
- 文件格式不支持
- 网络连接问题
- Token 无效或过期

**解决方案**：
- 检查文件大小和格式
- 查看浏览器控制台错误信息
- 确认已登录且 Token 有效

### 4. 演示功能不工作

**原因**：演示功能是前端模拟，不需要后端 API

**解决方案**：
- 检查浏览器控制台是否有 JavaScript 错误
- 确认 JavaScript 文件已正确加载
- 尝试刷新页面

### 5. 页面样式错误

**可能原因**：
- CSS 文件路径错误
- 浏览器缓存问题

**解决方案**：
- 检查 CSS 文件路径
- 清除浏览器缓存
- 强制刷新（Ctrl+F5 或 Cmd+Shift+R）

---

## 📚 相关文档

- **[AUTH_SYSTEM.md](AUTH_SYSTEM.md)** - 认证系统详细说明
- **[DEMO_QUICK_START.md](DEMO_QUICK_START.md)** - 演示页面开发指南
- **[PROJECT_PROGRESS_REPORT.md](PROJECT_PROGRESS_REPORT.md)** - 项目进度报告
- **[PROJECT_COMPLETION_PLAN.md](PROJECT_COMPLETION_PLAN.md)** - 项目补全计划
- **[NEXT_SESSION_TODO.md](NEXT_SESSION_TODO.md)** - 下次会话 TODO

---

## 📊 项目统计

- **项目总数**：14 个
- **已完成演示页面**：2 个（14%）
- **待完成演示页面**：12 个（86%）
- **在线工具**：PDF 工具集（7 个功能）
- **代码行数**：约 5000+ 行

---

## 🎯 未来计划

### 短期计划（1-2 周）
- ✅ 完成基础设施搭建
- ✅ 完成 2 个高优先级演示页面
- 🔄 完成剩余 3 个高优先级演示页面
- 🔄 完成 5 个中优先级演示页面

### 中期计划（1 个月）
- 完成所有 14 个演示页面
- 优化用户体验
- 添加更多在线工具
- 完善文档

### 长期计划（3 个月）
- 实现 Token 自动刷新
- 添加密码找回功能
- 添加个人资料编辑
- 添加使用统计功能
- 优化性能和安全性

---

## 📞 联系方式

- **GitHub**：https://github.com/zhimingliang897-web/integrity
- **问题反馈**：提交 GitHub Issue
- **功能建议**：提交 Pull Request

---

## 📄 许可证

本项目开源，仅供学习使用。

---

**文档版本**：v2.0  
**最后更新**：2026-03-12  
**维护者**：Integrity Lab Team
