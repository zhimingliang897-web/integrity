# Docs 目录结构说明

## 📁 目录组织

```
docs/
├── index.html                  # 首页
├── news.html                   # AI 热点页面
├── tools.html                  # 工具库页面
├── style.css                   # 全局样式
├── README.md                   # 项目说明
├── DEPLOYMENT.md               # 部署文档
├── DEPLOY_LOG.md               # 部署日志
│
├── data/                       # 数据文件
│   └── news.json              # AI 热点数据
│
├── server/                     # 后端代码（本地备份）
│   ├── app/
│   │   ├── main.py
│   │   └── tools/
│   ├── requirements.txt
│   └── README.md
│
├── tools-modules/              # 工具页面模块（新）
│   ├── tools-styles.css       # 工具页面样式
│   ├── tools-auth.js          # 认证模块
│   ├── tools-demo.js          # 演示模块
│   └── tools-pdf.js           # PDF 工具模块
│
├── documentation/              # 文档中心（新）
│   ├── SKILL_FRONTEND_REFACTOR.md      # Skill 详细文档
│   ├── SKILL_QUICK_GUIDE.md            # Skill 快速指南
│   ├── skill-frontend-refactor.json    # Skill JSON 配置
│   ├── TOOLS_REFACTOR_PROGRESS.md      # 重构进度文档
│   ├── FILES_SUMMARY.md                # 文件清单
│   ├── QUICK_GUIDE.md                  # 快速指南
│   ├── README_TOOLS.md                 # 工具说明
│   └── INDEX.md                        # 索引文档
│
└── archive/                    # 归档文件（新）
    ├── tools.html.backup      # 原始备份文件
    ├── tools-test.html        # 测试文件
    ├── tools-final.html       # 最终版本
    └── DEPLOYMENT1.md         # 旧部署文档
```

## 📝 目录说明

### 根目录
存放网站的主要页面和全局资源：
- **HTML 页面**：index.html, news.html, tools.html
- **全局样式**：style.css
- **核心文档**：README.md, DEPLOYMENT.md, DEPLOY_LOG.md

### data/
存放网站使用的数据文件：
- `news.json` - AI 热点新闻数据（由 GitHub Actions 自动更新）

### server/
后端 API 代码的本地备份：
- Flask 应用代码
- API 路由和工具函数
- 部署配置

### tools-modules/ ⭐ 新增
工具页面的模块化文件：
- **CSS 模块**：tools-styles.css（9.8KB）
- **JS 模块**：
  - tools-auth.js（3.8KB）- 用户认证
  - tools-demo.js（6.2KB）- 演示功能
  - tools-pdf.js（6.8KB）- PDF 工具

**用途**：将原本混在一起的代码拆分为独立模块，提高可维护性

### documentation/ ⭐ 新增
项目文档中心：
- **Skill 文档**：前端重构的完整流程和最佳实践
- **进度文档**：记录重构进度和完成情况
- **参考文档**：快速指南、文件清单等

**用途**：集中管理所有项目文档，便于查阅和维护

### archive/ ⭐ 新增
归档不再使用的文件：
- 备份文件
- 测试文件
- 旧版本文档

**用途**：保留历史文件以备查，但不影响主目录的整洁

## 🔗 路径引用

### tools.html 中的引用
```html
<!-- CSS -->
<link rel="stylesheet" href="style.css">
<link rel="stylesheet" href="tools-modules/tools-styles.css">

<!-- JavaScript -->
<script src="tools-modules/tools-auth.js"></script>
<script src="tools-modules/tools-demo.js"></script>
<script src="tools-modules/tools-pdf.js"></script>
```

### 其他页面的引用
```html
<!-- index.html, news.html -->
<link rel="stylesheet" href="style.css">
```

## 📋 文件清单

### 主要页面（3 个）
- index.html - 首页
- news.html - AI 热点
- tools.html - 工具库

### 样式文件（2 个）
- style.css - 全局样式
- tools-modules/tools-styles.css - 工具页面样式

### JavaScript 模块（3 个）
- tools-modules/tools-auth.js - 认证
- tools-modules/tools-demo.js - 演示
- tools-modules/tools-pdf.js - PDF 工具

### 文档文件（8 个）
- README.md - 项目说明
- DEPLOYMENT.md - 部署文档
- DEPLOY_LOG.md - 部署日志
- documentation/SKILL_FRONTEND_REFACTOR.md
- documentation/SKILL_QUICK_GUIDE.md
- documentation/TOOLS_REFACTOR_PROGRESS.md
- documentation/FILES_SUMMARY.md
- documentation/QUICK_GUIDE.md

### 归档文件（4 个）
- archive/tools.html.backup
- archive/tools-test.html
- archive/tools-final.html
- archive/DEPLOYMENT1.md

## 🎯 整理原则

1. **功能分离**：按功能将文件分类到不同目录
2. **模块化**：相关的代码文件放在一起
3. **文档集中**：所有文档放在 documentation/ 目录
4. **归档隔离**：不再使用的文件放在 archive/ 目录
5. **路径清晰**：使用相对路径，便于维护

## 🔄 迁移记录

**日期**：2026-03-12

**变更**：
1. 创建 `tools-modules/` 目录
   - 移入：tools-auth.js, tools-demo.js, tools-pdf.js, tools-styles.css

2. 创建 `documentation/` 目录
   - 移入：SKILL_*.md, skill-*.json, *_PROGRESS.md, FILES_SUMMARY.md, QUICK_GUIDE.md, README_TOOLS.md, INDEX.md

3. 创建 `archive/` 目录
   - 移入：tools.html.backup, tools-test.html, tools-final.html, DEPLOYMENT1.md

4. 更新 `tools.html` 中的路径引用
   - CSS: `tools-styles.css` → `tools-modules/tools-styles.css`
   - JS: `tools-*.js` → `tools-modules/tools-*.js`

## ✅ 验证

整理后的目录结构更加清晰：
- ✅ 主要页面在根目录，易于访问
- ✅ 模块文件集中管理
- ✅ 文档统一存放
- ✅ 归档文件隔离
- ✅ 路径引用正确

---

**创建日期**：2026-03-12  
**最后更新**：2026-03-12  
**维护者**：Integrity Lab
