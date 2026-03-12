# 前端模块化重构 Skill - 快速使用指南

## 📋 快速开始

### 1. 准备阶段（5分钟）

```bash
# 查看项目结构
ls -la

# 阅读关键文档
cat docs/*PROGRESS.md
cat docs/*SUMMARY.md
cat docs/DEPLOY_LOG.md
```

### 2. 创建任务清单（2分钟）

使用 `todowrite` 创建任务：

```javascript
[
  {"content": "了解项目现状", "priority": "high", "status": "in_progress"},
  {"content": "补全演示区", "priority": "high", "status": "pending"},
  {"content": "补全工具区", "priority": "high", "status": "pending"},
  {"content": "补全源码区", "priority": "high", "status": "pending"},
  {"content": "添加 Footer", "priority": "high", "status": "pending"},
  {"content": "测试功能", "priority": "medium", "status": "pending"}
]
```

### 3. 补全内容（30-60分钟）

```bash
# 读取备份文件
read(filePath="backup.html", offset=50, limit=150)

# 补全目标文件
edit(filePath="target.html", oldString="...", newString="...")

# 每完成一个区域，更新 todo 状态
todowrite([...])
```

### 4. 测试验证（10分钟）

```bash
# 启动本地服务器
python3 -m http.server 8000 &

# 测试 API
curl http://api-server:5000/
curl -X POST http://api-server:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'

# 验证结构
grep -c "tab-content" target.html
grep -c "card-class" target.html
wc -l target.html
```

### 5. 提交部署（5分钟）

```bash
# 查看状态
git status

# 添加文件
git add docs/target.html docs/*.js docs/*.css

# 提交
git commit -m "完成前端模块化重构

- 补全演示区：3个卡片
- 补全工具区：7个面板
- 补全源码区：12个卡片
- 添加 Footer 和模块引入"

# 推送
git push origin main
```

## 🎯 核心模式

### Tab 导航

```html
<!-- HTML -->
<div class="tab-nav">
    <button class="tab-btn active" onclick="switchTab('demo')">演示</button>
    <button class="tab-btn" onclick="switchTab('tools')">工具</button>
</div>

<div id="tab-demo" class="tab-content active">演示内容</div>
<div id="tab-tools" class="tab-content">工具内容</div>
```

```javascript
// JavaScript
function switchTab(name) {
    document.querySelectorAll('.tab-content').forEach(t => {
        t.classList.remove('active');
    });
    document.getElementById('tab-' + name).classList.add('active');
    
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('active');
    });
    event.target.classList.add('active');
}
```

### 卡片网格

```html
<div class="card-grid">
    <div class="card">
        <div class="icon">🎨</div>
        <h3>标题</h3>
        <p class="desc">描述文字</p>
        <div class="tech-tags">
            <span class="tech-tag">技术1</span>
            <span class="tech-tag">技术2</span>
        </div>
        <a href="#" class="link">查看详情 →</a>
    </div>
</div>
```

### API 调用

```javascript
// 带认证的 API 调用
async function callAPI(endpoint, data) {
    const token = localStorage.getItem('token');
    
    try {
        const res = await fetch(API_BASE + endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify(data)
        });
        
        if (!res.ok) throw new Error('请求失败');
        return await res.json();
    } catch (err) {
        console.error('API 错误:', err);
        alert('操作失败：' + err.message);
        throw err;
    }
}
```

### 登录状态检查

```javascript
function checkAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    
    if (token && username) {
        // 已登录
        document.getElementById('auth-btn').textContent = username;
        document.getElementById('auth-btn').classList.add('logged-in');
        document.getElementById('login-prompt').style.display = 'none';
        document.getElementById('online-tools').style.display = 'block';
    } else {
        // 未登录
        document.getElementById('auth-btn').textContent = '登录';
        document.getElementById('login-prompt').style.display = 'block';
        document.getElementById('online-tools').style.display = 'none';
    }
}

// 页面加载时检查
window.addEventListener('DOMContentLoaded', checkAuth);
```

## ✅ 验证清单

### 结构验证
```bash
# 检查 Tab 数量（应该是 3）
grep -c "tab-content" target.html

# 检查卡片数量
grep -c "demo-card" target.html    # 演示卡片
grep -c "source-card" target.html  # 源码卡片

# 检查面板数量
grep -c "pdf-panel" target.html    # PDF 面板

# 检查文件行数
wc -l target.html
```

### 功能测试
- [ ] Tab 切换正常
- [ ] 登录/注册功能
- [ ] 演示功能可用
- [ ] 在线工具需要登录
- [ ] API 调用成功
- [ ] 错误提示友好

### 样式测试
- [ ] 卡片布局正确
- [ ] 响应式布局
- [ ] 悬停动画
- [ ] 按钮状态

## 🔧 常见问题

### CORS 错误
```python
# 后端添加 CORS 配置
from flask_cors import CORS
CORS(app, origins=['https://your-domain.github.io', 'http://localhost:*'])
```

### Token 过期
```javascript
// 添加 Token 验证
async function verifyToken() {
    const token = localStorage.getItem('token');
    if (!token) return false;
    
    try {
        const res = await fetch(API_BASE + '/api/auth/verify', {
            headers: {'Authorization': 'Bearer ' + token}
        });
        return res.ok;
    } catch {
        return false;
    }
}
```

### 文件上传限制
```javascript
// 前端验证
const maxSize = 100 * 1024 * 1024; // 100MB
if (file.size > maxSize) {
    alert('文件大小不能超过 100MB');
    return;
}
```

## 📊 实际案例

**项目**：Integrity Lab Tools 页面重构

**原始状态**：
- tools.html.backup: 1125 行
- 单文件包含所有代码
- 难以维护

**重构后**：
- tools.html: 537 行
- tools-styles.css: 9.8KB
- tools-auth.js: 3.8KB
- tools-demo.js: 6.2KB
- tools-pdf.js: 6.8KB

**改进**：
- 代码量减少 50%+
- 模块化，易于维护
- 所有功能正常
- 2 小时完成

## 💡 最佳实践

1. **先读文档**：了解项目现状和进度
2. **创建清单**：使用 todowrite 跟踪任务
3. **分步完成**：每完成一个区域就更新状态
4. **及时测试**：补全后立即验证
5. **详细提交**：commit message 要清晰
6. **更新文档**：记录完成情况

## 📚 相关文档

- 详细文档：`SKILL_FRONTEND_REFACTOR.md`
- JSON 配置：`skill-frontend-refactor.json`
- 进度跟踪：`TOOLS_REFACTOR_PROGRESS.md`
- 文件清单：`FILES_SUMMARY.md`

---

**版本**：1.0  
**创建日期**：2026-03-12  
**适用场景**：前端模块化重构、内容补全、多页面整合
