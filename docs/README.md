# Integrity Lab - 前端文档

**GitHub Pages 托管的静态网站**

这是 Integrity Lab 的前端界面，展示 AI 工具集合并提供在线使用功能。

---

## 📋 项目结构

```
docs/
├── index.html           # 首页
├── news.html            # AI 热点页面
├── tools.html           # 工具库页面
├── style.css            # 全局样式
├── data/                # 数据文件
│   └── news.json        # AI 热点数据
├── server/              # 后端代码（本地备份）
└── README.md            # 本文档
```

---

## 🌐 访问地址

- **生产环境**: https://zhimingliang897-web.github.io/integrity/
- **后端 API**: https://api.liangyiren.top/

---

## 🎨 页面说明

### 1. 首页 (index.html)
- 项目介绍和理念
- AI 辩论赛演示
- 项目统计数据
- 快速导航

### 2. AI 热点 (news.html)
- 每日 AI 资讯聚合
- 自动评级和摘要
- 数据来源：GitHub Actions 定时任务

### 3. 工具库 (tools.html)
- **演示区**（游客可见）：
  - 图文互转演示
  - 多模型对比演示
  - Token 计算器演示
  
- **在线工具区**（登录后可用）：
  - PDF 工具集（7 个功能）
  - 更多工具即将上线

---

## 🔐 认证系统

### 登录流程
1. 用户点击"登录"按钮
2. 输入用户名和密码
3. 前端发送请求到 `https://api.liangyiren.top/api/auth/login`
4. 后端返回 JWT Token
5. Token 存储在 `localStorage`
6. 后续请求在 Header 中携带 Token

### 注册流程
1. 用户点击"注册"
2. 输入用户名、密码和邀请码
3. 前端发送请求到 `https://api.liangyiren.top/api/auth/register`
4. 注册成功后自动登录

### Token 管理
```javascript
// 存储 Token
localStorage.setItem('token', data.token);
localStorage.setItem('username', data.username);

// 使用 Token
const token = localStorage.getItem('token');
fetch(API_BASE + '/api/tools/pdf/info', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + token },
    body: formData
});

// 退出登录
localStorage.removeItem('token');
localStorage.removeItem('username');
```

---

## 🛠️ 工具使用说明

### PDF 工具集

所有 PDF 工具都需要登录后使用。

**1. 图片转 PDF**
- 上传多张图片
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

---

## 🎯 API 配置

前端通过以下常量配置 API 地址：

```javascript
const API_BASE = 'https://api.liangyiren.top';
```

如需修改 API 地址，在各 HTML 文件的 `<script>` 标签中修改此常量。

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

### 3. 测试登录

使用测试账号：
- 用户名：test
- 密码：123456
- 邀请码：demo2026

---

## 📝 修改指南

### 添加新工具

1. **在 tools.html 中添加 UI**
```html
<!-- 在 online-tools-section 中添加 -->
<div class="demo-card">
    <div class="demo-header">
        <div class="demo-title">
            <span class="icon">🎨</span>
            <h3>新工具名称</h3>
        </div>
        <button onclick="myToolFunction()">开始使用</button>
    </div>
    <div class="demo-body">
        <!-- 工具界面 -->
    </div>
</div>
```

2. **添加 JavaScript 逻辑**
```javascript
async function myToolFunction() {
    const token = localStorage.getItem('token');
    if (!token) {
        alert('请先登录');
        return;
    }
    
    const formData = new FormData();
    // 添加表单数据
    
    const res = await fetch(API_BASE + '/api/tools/my-tool/process', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token },
        body: formData
    });
    
    const data = await res.json();
    // 处理响应
}
```

3. **后端实现对应 API**（参考 `server/README.md`）

### 修改样式

全局样式在 `style.css` 中定义，使用 CSS 变量：

```css
:root {
    --bg-body: #0a0a0f;
    --bg-card: #13131a;
    --border: #2a2a35;
    --primary: #3b82f6;
    --secondary: #8b5cf6;
    --text-muted: #9ca3af;
}
```

---

## 🐛 常见问题

### 1. CORS 错误
确保后端 API 配置了正确的 CORS 策略：
```python
CORS(app, origins=[
    'https://zhimingliang897-web.github.io',
    'http://localhost:*'
])
```

### 2. Token 过期
Token 有效期为 7 天，过期后需要重新登录。

### 3. 文件上传失败
- 检查文件大小（限制 100MB）
- 检查文件格式是否支持
- 查看浏览器控制台错误信息

### 4. 演示功能不工作
演示功能是前端模拟，不需要后端 API。如果不工作，检查浏览器控制台是否有 JavaScript 错误。

---

## 📞 联系方式

- **GitHub**: https://github.com/zhimingliang897-web/integrity
- **问题反馈**: 提交 GitHub Issue

---

## 📄 许可证

本项目开源，仅供学习使用。
