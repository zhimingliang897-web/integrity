# 下次会话 TODO 清单

## 🎯 主要目标
完成剩余的高优先级项目（多模型对比平台），将进度从 29% 提升到 36%

---

## ✅ 已完成（4/14 = 29%）
- ✅ 基础设施（demos 目录、通用脚本、模板）
- ✅ 分镜视频生成器 (`demos/video-maker.html`)
- ✅ 台词学习工具 (`demos/dialogue-learning.html`)
- ✅ AI 辩论赛 (`demos/ai-debate.html`) - 本次完成
- ✅ 图文互转工具 (`demos/image-prompt.html`) - 本次完成
- ✅ 演示页面索引 (`demos/index.html`)
- ✅ 进度报告和快速指南

---

## 📋 下次要完成（1 个高优先级项目）

### 1. 多模型对比平台 (`demos/ai-compare.html`)
**源码位置**：`17ai-compare/`

**需要实现的功能**：
- [ ] 问题输入框
- [ ] 模型选择（支持 2-4 个模型同时对比）
- [ ] 并发提交按钮
- [ ] 流式输出展示（实时显示每个模型的回复）
- [ ] 响应时间统计
- [ ] 结果对比分析

**开发步骤**：
```bash
# 1. 复制模板
cp docs/demos/_template.html docs/demos/ai-compare.html

# 2. 查看源码
cat 17ai-compare/README.md

# 3. 实现多模型并发界面
# 4. 实现流式输出
# 5. 添加统计功能
```

**关键技术点**：
- 多个 API 并发调用
- 流式输出（SSE 或 WebSocket）
- 响应时间计算
- 结果对比展示

**预计时间**：3-4 小时

---

## 🔧 完成后的更新任务

### 2. 更新 tools.html
为多模型对比平台添加演示链接（已有样式，直接复制即可）

### 3. 更新 demos/index.html
更新完成状态和统计数据：
- 已完成：5
- 待完成：9
- 完成度：36%

---

## 📋 后续待完成项目（中低优先级）

### 中优先级（5 个）

**2. EasyApply 浏览器插件** (`demos/easyapply.html`)
- 源码：`11easyapply/`
- 预计时间：2-3 小时

**3. CourseDigest 智能助考** (`demos/course-digest.html`)
- 源码：`13course_digest/`
- 预计时间：3-4 小时

**4. 个人文件助手 Agent** (`demos/file-agent.html`)
- 源码：`14file-agent-v0/` 和 `14.1file-agent-v1/`
- 预计时间：2-3 小时

**5. 小红书内容生成器** (`demos/redbook-generator.html`)
- 源码：`15redbook/`
- 预计时间：2-3 小时

**6. 小红书图片生成器** (`demos/xhs-image-generator.html`)
- 源码：`20AIer-xhs/`
- 预计时间：2-3 小时

### 低优先级（2 个）

**7. Token 对比工具** (`demos/token-compare.html`)
- 源码：`18tokens/`
- 预计时间：2 小时

**8. 大麦抢票助手** (`demos/ticket-helper.html`)
- 源码：`16票/`（私有项目，仅说明）
- 预计时间：1-2 小时

---

## 📚 快速参考

### 开发模板
```bash
# 1. 复制模板
cp docs/demos/_template.html docs/demos/[项目名].html

# 2. 启动本地服务器测试
cd docs && python3 -m http.server 8000

# 3. 访问页面
open http://localhost:8000/demos/[项目名].html
```

### 常用工具函数（demos-common.js）
```javascript
// 检查登录
const { token, isLoggedIn } = DemoUtils.checkAuth();

// 显示消息
DemoUtils.showMessage('操作成功', 'success');
DemoUtils.showMessage('操作失败', 'error');

// 加载状态
DemoUtils.showLoading(button, '处理中...');
DemoUtils.hideLoading(button);

// 文件上传
const result = await DemoUtils.uploadFile(file, '/api/endpoint', {
    param1: 'value1'
});

// 文件下载
DemoUtils.downloadFile(blob, 'filename.ext');
```

### API 调用示例
```javascript
const { token } = DemoUtils.checkAuth();

// POST 请求
const response = await fetch(API_BASE + '/api/tools/your-endpoint', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ param: 'value' })
});

const data = await response.json();
```

---

## 📊 预期成果

完成多模型对比平台后：
- **进度**：5/14 完成（36%）
- **高优先级**：5/5 完成（100%）✅
- **剩余工作**：9 个项目（中低优先级）

---

## 🎯 成功标准

每个演示页面需要包含：
- ✅ 完整的功能演示区
- ✅ 清晰的使用说明（步骤）
- ✅ 示例展示
- ✅ 技术栈说明
- ✅ 响应式设计（移动端适配）
- ✅ 错误处理
- ✅ 加载状态提示

---

## 📞 重要文档

- `PROJECT_PROGRESS_REPORT.md` - 详细进度报告
- `DEMO_QUICK_START.md` - 开发指南
- `PROJECT_COMPLETION_PLAN.md` - 完整计划
- `WORK_SUMMARY_2026-03-12_SESSION2.md` - 本次会话总结
- `demos/_template.html` - 页面模板
- `tools-modules/demos-common.js` - 工具函数

---

**更新日期**：2026-03-12  
**当前进度**：4/14（29%）  
**下次目标**：完成多模型对比平台，达到 36% 进度  
**预计完成时间**：3-4 小时
