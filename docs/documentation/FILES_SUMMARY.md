# 文件清单和说明

## 📦 已创建的模块化文件

### 1. 样式文件
```
tools-styles.css (9.8KB)
```
**包含内容**:
- Tab 导航样式
- 演示卡片样式（demo-card, demo-grid）
- 源码卡片样式（source-card, source-grid）
- 在线工具样式（online-card, login-prompt）
- PDF 工具样式（pdf-tab, pdf-panel, pdf-form-row）
- 认证样式（auth-btn, modal）
- 动画效果（fadeIn, scan）

### 2. JavaScript 模块

#### tools-auth.js (3.8KB)
**功能**:
- 登录/注册/退出
- Token 管理
- 登录状态检查

**主要函数**:
- `checkAuth()` - 检查并更新登录状态
- `showAuthModal()` - 显示登录弹窗
- `hideAuthModal()` - 隐藏登录弹窗
- `toggleAuthMode()` - 切换登录/注册模式
- `handleAuth()` - 处理登录/注册请求
- `logout()` - 退出登录

#### tools-demo.js (6.2KB)
**功能**:
- 图文互转演示
- 多模型对比演示
- Token 计算器

**依赖元素 ID**:
- `start-vision-btn` - 图文互转按钮
- `vision-output` - 输出区域
- `scan-line` - 扫描线动画
- `vision-demo-img` - 演示图片
- `start-compare-btn` - 对比按钮
- `model-qwen`, `model-deepseek`, `model-gpt` - 模型输出区
- `calc-token-btn` - 计算按钮
- `token-model`, `token-lang`, `token-chars` - 输入控件
- `result-prompt`, `result-completion`, `result-cost` - 结果显示

#### tools-pdf.js (6.8KB)
**功能**:
- Tab 切换
- PDF 工具操作（7个功能）

**主要函数**:
- `switchTab(tabName)` - 切换主 Tab
- `toggleSection(id)` - 展开/收起工具
- `getPdfInfo(input, infoId)` - 获取 PDF 信息
- `autoFillEndPage(input)` - 自动填充结束页码
- `pdfOp(op)` - PDF 操作主函数

**支持的操作**:
- `img2pdf` - 图片转 PDF
- `merge` - 合并 PDF
- `remove` - 删除页面
- `insert` - 插入 PDF
- `reorder` - 页面重排
- `normalize` - 统一尺寸
- `to_images` - PDF 转图片

### 3. HTML 文件

#### tools.html (部分完成)
**已完成**:
- HTML 头部（引入 CSS）
- 导航栏
- 登录/注册弹窗
- 页面标题
- Tab 导航按钮

**需要补充**:
- 演示体验区的 3 个卡片
- 在线工具区（登录提示 + PDF 工具）
- 源码浏览区（12 个工具卡片）
- Footer
- Script 标签引入 JS 模块

## 📋 需要的 HTML 元素 ID

### 认证相关
- `auth-btn` - 登录按钮
- `auth-modal` - 登录弹窗
- `auth-title` - 弹窗标题
- `auth-username` - 用户名输入
- `auth-password` - 密码输入
- `auth-invite` - 邀请码输入
- `invite-code-wrap` - 邀请码容器
- `auth-error` - 错误提示
- `auth-submit` - 提交按钮
- `switch-text` - 切换提示文本
- `switch-link` - 切换链接

### Tab 相关
- `tab-demo` - 演示体验区容器
- `tab-online` - 在线工具区容器
- `tab-source` - 源码浏览区容器

### 在线工具相关
- `login-prompt` - 登录提示卡片
- `online-tools-content` - 在线工具内容（登录后显示）
- `pdf-tools` - PDF 工具容器
- `pdf-tools-arrow` - 展开/收起箭头
- `pdf-tabs` - PDF Tab 导航容器

### PDF 工具面板
- `p-img2pdf` - 图片转 PDF 面板
- `p-merge` - 合并 PDF 面板
- `p-remove` - 删除页面面板
- `p-insert` - 插入 PDF 面板
- `p-reorder` - 页面重排面板
- `p-normalize` - 统一尺寸面板
- `p-to-img` - PDF 转图片面板

### PDF 表单元素（每个面板内）
- `p-img2pdf-files` - 图片文件输入
- `p-img2pdf-landscape` - 横向选项
- `p-merge-files` - PDF 文件输入
- `p-remove-file` - PDF 文件输入
- `p-remove-pages` - 页码输入
- `p-remove-info` - 信息显示
- `p-insert-main` - 主文档输入
- `p-insert-ins` - 插入文档输入
- `p-insert-pos` - 位置选择
- `p-insert-page` - 页码输入
- `p-insert-info` - 信息显示
- `p-reorder-file` - PDF 文件输入
- `p-reorder-info` - 信息显示
- `p-normalize-file` - PDF 文件输入
- `p-normalize-info` - 信息显示
- `p-toimg-file` - PDF 文件输入
- `p-toimg-start` - 起始页
- `p-toimg-end` - 结束页
- `p-toimg-dpi` - DPI 设置
- `p-toimg-fmt` - 格式选择
- `p-toimg-maxsize` - 大小限制
- `p-toimg-long` - 长图选项
- `p-toimg-info` - 信息显示

### 结果显示
- `r-img2pdf` - 图片转 PDF 结果
- `r-merge` - 合并结果
- `r-remove` - 删除结果
- `r-insert` - 插入结果
- `r-reorder` - 重排结果
- `r-normalize` - 统一尺寸结果
- `r-to_images` - 转图片结果

## 🔗 API 端点

**Base URL**: `https://api.liangyiren.top`

### 认证
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录
- `GET /api/auth/verify` - 验证 Token

### 工具
- `POST /api/tools/token-calc` - Token 计算器（无需登录）
- `POST /api/tools/pdf/info` - 获取 PDF 信息
- `POST /api/tools/pdf/images_to_pdf` - 图片转 PDF
- `POST /api/tools/pdf/merge` - 合并 PDF
- `POST /api/tools/pdf/remove_pages` - 删除页面
- `POST /api/tools/pdf/insert` - 插入 PDF
- `POST /api/tools/pdf/reorder` - 页面重排
- `POST /api/tools/pdf/normalize` - 统一尺寸
- `POST /api/tools/pdf/to_images` - PDF 转图片
- `GET /api/tools/pdf/download/<filename>` - 下载文件

## 📐 CSS 类名

### 布局
- `container` - 主容器
- `page-header` - 页面标题
- `tab-nav` - Tab 导航容器
- `tab-btn` - Tab 按钮
- `tab-btn.active` - 激活的 Tab
- `tab-content` - Tab 内容区
- `tab-content.active` - 显示的内容区
- `section-title` - 区域标题

### 卡片
- `demo-grid` - 演示卡片网格（2列）
- `demo-card` - 演示卡片
- `demo-header` - 卡片头部
- `demo-title` - 卡片标题
- `demo-btn` - 演示按钮
- `demo-body` - 卡片内容
- `source-grid` - 源码卡片网格（3列）
- `source-card` - 源码卡片
- `tech-tags` - 技术标签容器
- `tech-tag` - 技术标签
- `source-link` - 源码链接

### 在线工具
- `login-prompt` - 登录提示
- `online-card` - 在线工具卡片
- `online-header` - 工具头部
- `online-body` - 工具内容
- `online-body.active` - 展开状态

### PDF 工具
- `pdf-tabs` - PDF Tab 容器
- `pdf-tab` - PDF Tab 按钮
- `pdf-tab.active` - 激活的 Tab
- `pdf-panel` - PDF 面板
- `pdf-panel.active` - 显示的面板
- `pdf-form-row` - 表单行
- `pdf-info` - 信息提示
- `pdf-btn` - PDF 操作按钮
- `pdf-result` - 结果显示
- `pdf-result.ok` - 成功结果
- `pdf-result.err` - 错误结果
- `pdf-dl` - 下载链接

### 认证
- `auth-btn` - 认证按钮
- `auth-btn.logged-in` - 已登录状态
- `modal` - 弹窗
- `modal-content` - 弹窗内容
- `modal-close` - 关闭按钮
- `auth-switch` - 切换提示

## 🎨 CSS 变量（来自 style.css）

```css
--bg-body: #0a0a0f
--bg-card: #13131a
--border: #2a2a35
--primary: #3b82f6
--secondary: #8b5cf6
--text-muted: #9ca3af
```

## 📱 响应式断点

- `max-width: 1200px` - 演示卡片变为 1 列，源码卡片变为 2 列
- `max-width: 768px` - 源码卡片变为 1 列

---

**文件位置**: `/Users/lzm/macbook_space/integrity/docs/`
**备份文件**: `tools.html.backup` (1125 行)
**详细文档**: `TOOLS_REFACTOR_PROGRESS.md`
**快速指南**: `QUICK_GUIDE.md`
