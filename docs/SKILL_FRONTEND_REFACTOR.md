# Skill: 前端模块化重构与补全

## 技能描述

这个 Skill 用于完成前端页面的模块化重构和内容补全工作。适用于需要将大型单文件 HTML 拆分为模块化结构，并补全缺失内容的场景。

## 适用场景

- 大型单文件 HTML 需要模块化拆分
- 前端页面内容不完整，需要补全
- 需要创建可维护的模块化前端架构
- 需要整合多个功能模块到统一页面

## 工作流程

### 第一步：了解项目现状

1. **查看参考配置**
   - 检查 `.mcp.json` 了解服务器配置
   - 查看项目目录结构
   - 了解现有的技术栈

2. **阅读进度文档**
   - `TOOLS_REFACTOR_PROGRESS.md` - 重构进度
   - `FILES_SUMMARY.md` - 文件清单
   - `DEPLOY_LOG.md` - 部署日志
   - `README.md` - 项目说明

3. **分析现有文件**
   - 查看备份文件（如 `tools.html.backup`）
   - 检查已创建的模块文件（CSS、JS）
   - 确认缺失的内容部分

### 第二步：创建任务清单

使用 `todowrite` 工具创建详细的任务清单：

```javascript
[
  {"content": "查看参考文件，了解项目现状", "priority": "high", "status": "in_progress"},
  {"content": "补全页面区域 A", "priority": "high", "status": "pending"},
  {"content": "补全页面区域 B", "priority": "high", "status": "pending"},
  {"content": "补全页面区域 C", "priority": "high", "status": "pending"},
  {"content": "添加 Footer 和引入模块", "priority": "high", "status": "pending"},
  {"content": "测试功能", "priority": "medium", "status": "pending"},
  {"content": "验证完整性", "priority": "medium", "status": "pending"}
]
```

### 第三步：模块化补全

#### 3.1 读取备份文件内容

使用 `read` 工具分段读取备份文件，提取需要的 HTML 结构：

```bash
# 读取特定行范围
read(filePath="/path/to/backup.html", offset=50, limit=150)
```

#### 3.2 补全页面内容

使用 `edit` 工具将内容添加到目标文件：

**关键点**：
- 保持原有的缩进和格式
- 确保 ID 和 class 名称与 CSS/JS 模块匹配
- 按照逻辑顺序补全（从上到下）

**示例**：
```html
<!-- 演示体验区 -->
<div id="tab-demo" class="tab-content active">
    <div class="section-title">体验 AI 工具的核心功能</div>
    <div class="demo-grid">
        <!-- 卡片内容 -->
    </div>
</div>
```

#### 3.3 验证文件结构

使用 bash 命令验证：

```bash
# 检查行数
wc -l target.html

# 检查特定元素数量
grep -c "class-name" target.html

# 检查文件是否存在
ls -lh *.js *.css
```

### 第四步：功能测试

#### 4.1 启动本地服务器

```bash
cd /path/to/docs
python3 -m http.server 8000 &
```

#### 4.2 测试后端 API

```bash
# 健康检查
curl http://api-server:5000/

# 测试登录
curl -X POST http://api-server:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'

# 测试其他 API
curl -X POST http://api-server:5000/api/tools/token-calc \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-plus","lang":"zh","chars":100}'
```

#### 4.3 验证完整性

```bash
# 验证 tab 数量
grep -c "tab-content" target.html

# 验证卡片数量
grep -c "card-class" target.html

# 验证面板数量
grep -c "panel-class" target.html
```

### 第五步：提交和部署

#### 5.1 查看 Git 状态

```bash
git status
```

#### 5.2 添加文件

```bash
git add docs/target.html docs/*.js docs/*.css docs/*PROGRESS.md
```

#### 5.3 提交代码

```bash
git commit -m "完成前端模块化重构

- 补全区域 A：功能描述
- 补全区域 B：功能描述
- 补全区域 C：功能描述
- 添加 Footer 和引入模块
- 新增模块化文件：列出文件
- 更新进度文档"
```

#### 5.4 推送到远程

```bash
git push origin main
```

### 第六步：更新文档

更新进度文档，记录完成情况：

```markdown
## 🎉 [日期] 更新

### 所有任务已完成！

#### 完成内容：
1. ✅ 目标文件已完整补全（行数）
   - 区域 A：描述
   - 区域 B：描述
   - 区域 C：描述

2. ✅ 后端 API 测试通过
   - 服务器地址：URL
   - 各项功能测试结果

3. ✅ 文件结构验证
   - 验证项 1 ✓
   - 验证项 2 ✓

#### 下一步建议：
1. 浏览器完整测试
2. 功能测试清单
3. 响应式测试
4. 部署验证
```

## 关键技术点

### 1. 模块化架构

**CSS 模块**：
- 全局样式（style.css）
- 页面专用样式（page-styles.css）
- 使用 CSS 变量保持一致性

**JavaScript 模块**：
- 认证模块（auth.js）
- 功能模块（demo.js, tools.js）
- 按功能拆分，便于维护

### 2. HTML 结构设计

**Tab 导航模式**：
```html
<div class="tab-nav">
    <button class="tab-btn active" onclick="switchTab('tab1')">Tab 1</button>
    <button class="tab-btn" onclick="switchTab('tab2')">Tab 2</button>
</div>

<div id="tab1" class="tab-content active">内容 1</div>
<div id="tab2" class="tab-content">内容 2</div>
```

**卡片网格布局**：
```html
<div class="card-grid">
    <div class="card">
        <div class="card-header">标题</div>
        <div class="card-body">内容</div>
    </div>
</div>
```

### 3. API 集成

**认证流程**：
```javascript
// 登录
const response = await fetch(API_BASE + '/api/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
});

// 存储 Token
localStorage.setItem('token', data.token);

// 使用 Token
headers: {'Authorization': 'Bearer ' + token}
```

**错误处理**：
```javascript
try {
    const res = await fetch(url, options);
    if (!res.ok) throw new Error('请求失败');
    const data = await res.json();
    // 处理数据
} catch (err) {
    console.error(err);
    alert('操作失败：' + err.message);
}
```

### 4. 状态管理

**登录状态**：
```javascript
function checkAuth() {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    
    if (token && username) {
        // 更新 UI 为已登录状态
        document.getElementById('auth-btn').textContent = username;
        document.getElementById('login-prompt').style.display = 'none';
        document.getElementById('online-tools-content').style.display = 'block';
    }
}

// 页面加载时检查
window.addEventListener('DOMContentLoaded', checkAuth);
```

**Tab 切换**：
```javascript
function switchTab(tabName) {
    // 隐藏所有 tab
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 显示目标 tab
    document.getElementById('tab-' + tabName).classList.add('active');
    
    // 更新按钮状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}
```

## 常见问题和解决方案

### 问题 1：CORS 错误

**原因**：前端和后端不在同一域名

**解决**：
```python
# 后端配置 CORS
from flask_cors import CORS

CORS(app, origins=[
    'https://your-domain.github.io',
    'http://localhost:*'
])
```

### 问题 2：Token 过期

**原因**：JWT Token 有有效期

**解决**：
```javascript
// 检查 Token 是否有效
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

### 问题 3：文件上传失败

**原因**：文件大小超限或格式不支持

**解决**：
```javascript
// 前端验证
const file = input.files[0];
const maxSize = 100 * 1024 * 1024; // 100MB

if (file.size > maxSize) {
    alert('文件大小不能超过 100MB');
    return;
}

if (!file.type.includes('pdf')) {
    alert('只支持 PDF 文件');
    return;
}
```

### 问题 4：响应式布局问题

**原因**：CSS 媒体查询不完善

**解决**：
```css
/* 桌面端 */
.card-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}

/* 平板 */
@media (max-width: 1200px) {
    .card-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* 手机 */
@media (max-width: 768px) {
    .card-grid {
        grid-template-columns: 1fr;
    }
}
```

## 验证清单

### 功能测试
- [ ] Tab 切换是否正常
- [ ] 登录/注册功能
- [ ] 演示功能是否可用
- [ ] 在线工具是否需要登录
- [ ] API 调用是否成功
- [ ] 文件上传/下载是否正常
- [ ] 错误提示是否友好

### 样式测试
- [ ] 卡片布局是否正确
- [ ] 响应式布局（移动端）
- [ ] 悬停动画效果
- [ ] Tab 激活状态
- [ ] 按钮样式统一
- [ ] 颜色主题一致

### 浏览器测试
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge
- [ ] 移动端浏览器

### 性能测试
- [ ] 页面加载速度
- [ ] API 响应时间
- [ ] 文件上传速度
- [ ] 内存占用

## 最佳实践

### 1. 代码组织

```
project/
├── docs/
│   ├── index.html          # 首页
│   ├── tools.html          # 工具页
│   ├── style.css           # 全局样式
│   ├── tools-styles.css    # 工具页样式
│   ├── tools-auth.js       # 认证模块
│   ├── tools-demo.js       # 演示模块
│   ├── tools-pdf.js        # PDF 工具模块
│   └── data/               # 数据文件
```

### 2. 命名规范

**CSS 类名**：
- 使用 kebab-case：`demo-card`, `tab-content`
- 语义化命名：`login-prompt`, `pdf-panel`
- 状态类：`active`, `disabled`, `loading`

**JavaScript 函数**：
- 使用 camelCase：`switchTab`, `handleAuth`
- 动词开头：`get`, `set`, `show`, `hide`
- 清晰描述功能：`getPdfInfo`, `autoFillEndPage`

**ID 命名**：
- 唯一且描述性：`auth-modal`, `pdf-tools`
- 避免通用名称：不要用 `modal`, `content`

### 3. 注释规范

```javascript
/**
 * 切换 Tab 页面
 * @param {string} tabName - Tab 名称（demo/online/source）
 */
function switchTab(tabName) {
    // 实现代码
}
```

```html
<!-- 演示体验区 -->
<div id="tab-demo" class="tab-content active">
    <!-- 图文互转卡片 -->
    <div class="demo-card">
        ...
    </div>
</div>
```

### 4. 错误处理

```javascript
// 统一的错误处理函数
function handleError(error, context) {
    console.error(`[${context}] 错误:`, error);
    
    // 用户友好的错误提示
    const message = error.message || '操作失败，请重试';
    showNotification(message, 'error');
}

// 使用示例
try {
    await someOperation();
} catch (err) {
    handleError(err, 'PDF 处理');
}
```

### 5. 性能优化

```javascript
// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// 使用示例
const searchInput = document.getElementById('search');
searchInput.addEventListener('input', debounce(handleSearch, 300));
```

## 工具和资源

### 开发工具
- VS Code + Live Server 插件
- Chrome DevTools
- Postman（API 测试）

### 测试工具
- curl（命令行 API 测试）
- Python http.server（本地服务器）
- Browser DevTools（前端调试）

### 文档工具
- Markdown 编辑器
- 截图工具
- Git 版本控制

## 总结

这个 Skill 的核心是：

1. **系统化**：按照固定流程完成任务
2. **模块化**：将大文件拆分为可维护的模块
3. **可验证**：每一步都有明确的验证方法
4. **可复用**：流程和代码模式可以应用到其他项目

通过遵循这个 Skill，可以高效地完成前端模块化重构和补全工作，确保代码质量和可维护性。

## 实际案例

### 案例：Integrity Lab Tools 页面重构

**背景**：
- 原始文件：tools.html.backup (1125 行)
- 目标：拆分为模块化结构，补全缺失内容

**执行步骤**：
1. 创建 4 个模块文件（CSS + 3 个 JS）
2. 补全 3 个主要区域（演示、在线工具、源码浏览）
3. 测试后端 API 连接
4. 验证完整性（537 行，包含所有功能）
5. 提交并推送到 GitHub

**结果**：
- 代码量减少 50%+（通过模块化）
- 可维护性大幅提升
- 所有功能正常工作
- 成功部署到 GitHub Pages

**时间**：约 2 小时完成全部工作

---

**创建日期**：2026-03-12  
**最后更新**：2026-03-12  
**版本**：1.0
