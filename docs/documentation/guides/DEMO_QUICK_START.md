# 演示页面开发快速指南

## 📁 项目结构

```
docs/
├── demos/                          # 演示页面目录
│   ├── index.html                 # 演示页面索引（已完成）
│   ├── _template.html             # 页面模板（已完成）
│   ├── video-maker.html           # 分镜视频生成器（已完成）
│   ├── dialogue-learning.html     # 台词学习工具（已完成）
│   └── [其他演示页面...]          # 待创建
│
├── demos-assets/                   # 演示资源
│   ├── images/                    # 示例图片
│   ├── videos/                    # 示例视频
│   └── data/                      # 示例数据
│
└── tools-modules/                  # 工具模块
    ├── demos-common.js            # 演示页面通用脚本（已完成）
    ├── tools-auth.js              # 认证模块
    ├── tools-demo.js              # 演示功能
    ├── tools-pdf.js               # PDF 工具
    └── tools-styles.css           # 工具样式
```

## 🚀 快速开始

### 1. 创建新的演示页面

复制模板文件：
```bash
cp docs/demos/_template.html docs/demos/your-demo.html
```

### 2. 修改页面内容

编辑 `your-demo.html`，修改以下部分：

#### 页面标题和描述
```html
<div class="page-header">
    <h1>🎯 你的项目名称</h1>
    <p>项目简介描述</p>
</div>
```

#### 功能演示区
```html
<section class="demo-section">
    <h2>功能演示</h2>
    <div class="demo-card">
        <div class="demo-body">
            <!-- 添加你的演示内容 -->
        </div>
    </div>
</section>
```

#### 使用说明
```html
<section class="guide-section">
    <h2>使用说明</h2>
    <div class="guide-steps">
        <div class="step">
            <div class="step-number">1</div>
            <div class="step-content">
                <h3>第一步</h3>
                <p>步骤说明</p>
            </div>
        </div>
        <!-- 添加更多步骤 -->
    </div>
</section>
```

### 3. 使用通用工具函数

`demos-common.js` 提供了以下工具函数：

#### 检查登录状态
```javascript
const { token, username, isLoggedIn } = DemoUtils.checkAuth();
if (!isLoggedIn) {
    DemoUtils.showMessage('请先登录', 'error');
    return;
}
```

#### 显示消息提示
```javascript
DemoUtils.showMessage('操作成功', 'success');  // 成功消息
DemoUtils.showMessage('操作失败', 'error');    // 错误消息
DemoUtils.showMessage('提示信息', 'info');     // 普通消息
```

#### 显示/隐藏加载状态
```javascript
const button = document.getElementById('submit-btn');
DemoUtils.showLoading(button, '处理中...');
// 处理完成后
DemoUtils.hideLoading(button);
```

#### 上传文件
```javascript
const file = document.getElementById('file-input').files[0];
const result = await DemoUtils.uploadFile(file, '/api/tools/your-endpoint', {
    param1: 'value1',
    param2: 'value2'
});
```

#### 下载文件
```javascript
const blob = await response.blob();
DemoUtils.downloadFile(blob, 'filename.pdf');
```

#### 格式化文件大小
```javascript
const size = DemoUtils.formatFileSize(1024000);  // "1000 KB"
```

#### 验证文件类型
```javascript
const file = document.getElementById('file-input').files[0];
const isValid = DemoUtils.validateFileType(file, ['.pdf', '.doc', 'image/*']);
```

### 4. API 调用示例

#### GET 请求
```javascript
const { token } = DemoUtils.checkAuth();
const response = await fetch(API_BASE + '/api/tools/your-endpoint', {
    headers: {
        'Authorization': 'Bearer ' + token
    }
});
const data = await response.json();
```

#### POST 请求（JSON）
```javascript
const { token } = DemoUtils.checkAuth();
const response = await fetch(API_BASE + '/api/tools/your-endpoint', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        param1: 'value1',
        param2: 'value2'
    })
});
const data = await response.json();
```

#### POST 请求（FormData）
```javascript
const { token } = DemoUtils.checkAuth();
const formData = new FormData();
formData.append('file', file);
formData.append('param1', 'value1');

const response = await fetch(API_BASE + '/api/tools/your-endpoint', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token
    },
    body: formData
});
const data = await response.json();
```

### 5. 常用样式类

#### 表单组
```html
<div class="form-group">
    <label for="input-id">标签</label>
    <input type="text" id="input-id" placeholder="提示文字">
</div>
```

#### 按钮
```html
<button class="btn-primary" onclick="handleClick()">
    按钮文字
</button>
```

#### 功能列表
```html
<ul class="feature-list">
    <li>功能特性 1</li>
    <li>功能特性 2</li>
    <li>功能特性 3</li>
</ul>
```

#### 示例网格
```html
<div class="example-grid">
    <div class="example-card">
        <h4>示例标题</h4>
        <p>示例描述</p>
    </div>
    <!-- 更多示例卡片 -->
</div>
```

## 📝 开发流程

### 1. 调研阶段（30 分钟）
- 阅读项目的 README.md
- 运行项目代码，了解功能
- 查看现有的文档和示例
- 确定演示的核心功能

### 2. 设计阶段（30 分钟）
- 设计演示页面的布局
- 确定需要展示的功能点
- 准备示例数据和资源
- 规划用户交互流程

### 3. 开发阶段（2-4 小时）
- 复制模板创建演示页面
- 编写页面内容和样式
- 编写交互脚本
- 集成后端 API（如需要）
- 添加示例和说明

### 4. 测试阶段（30 分钟）
- 功能测试
- 样式测试
- 响应式测试
- 浏览器兼容性测试

### 5. 文档阶段（30 分钟）
- 完善项目 README.md
- 添加使用说明
- 添加示例截图
- 更新索引页面

## 🎨 设计规范

### 颜色变量
```css
--bg-body: #0a0a0f;        /* 页面背景 */
--bg-card: #13131a;        /* 卡片背景 */
--border: #2a2a35;         /* 边框颜色 */
--primary: #3b82f6;        /* 主色调 */
--secondary: #8b5cf6;      /* 辅助色 */
--text-primary: #ffffff;   /* 主文字 */
--text-muted: #9ca3af;     /* 次要文字 */
```

### 间距规范
- 小间距：8px, 12px
- 中间距：16px, 20px, 24px
- 大间距：32px, 40px, 60px

### 圆角规范
- 小圆角：6px
- 中圆角：8px, 12px
- 大圆角：16px

### 字体大小
- 标题：48px, 32px, 24px
- 正文：16px, 14px
- 小字：12px

## 🔧 调试技巧

### 1. 本地测试
```bash
# 启动本地服务器
cd docs
python3 -m http.server 8000

# 访问页面
open http://localhost:8000/demos/your-demo.html
```

### 2. 查看控制台
打开浏览器开发者工具（F12），查看：
- Console：JavaScript 错误和日志
- Network：API 请求和响应
- Elements：HTML 结构和样式

### 3. 常见问题

**问题：API 请求失败**
- 检查 token 是否有效
- 检查 API 地址是否正确
- 检查请求参数是否正确
- 查看 Network 面板的错误信息

**问题：样式不生效**
- 检查 CSS 文件路径是否正确
- 检查 CSS 选择器是否正确
- 使用浏览器开发者工具检查样式

**问题：文件上传失败**
- 检查文件大小是否超限
- 检查文件类型是否支持
- 检查 FormData 是否正确构建

## 📚 参考资源

### 已完成的示例
- `demos/video-maker.html` - 分镜视频生成器
- `demos/dialogue-learning.html` - 台词学习工具
- `demos/index.html` - 演示页面索引

### 文档
- `PROJECT_COMPLETION_PLAN.md` - 完整的补全计划
- `PROJECT_PROGRESS_REPORT.md` - 进度报告
- `documentation/SKILL_FRONTEND_REFACTOR.md` - 开发流程

### 工具
- `tools-modules/demos-common.js` - 通用工具函数
- `tools-modules/tools-auth.js` - 认证模块
- `style.css` - 全局样式
- `tools-modules/tools-styles.css` - 工具样式

## 🎯 下一步

1. 选择一个待完成的项目
2. 按照开发流程创建演示页面
3. 测试功能和样式
4. 更新索引页面
5. 提交代码

---

**创建日期**：2026-03-12  
**最后更新**：2026-03-12  
**维护者**：Integrity Lab Team
