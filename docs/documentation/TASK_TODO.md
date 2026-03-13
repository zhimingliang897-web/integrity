# Integrity Lab Demo 功能完善任务清单

**文档更新时间：2026-03-13**

---

## 一、项目现状总结

### ✅ 已完成

| 模块 | 状态 | 说明 |
|------|------|------|
| 后端 API 部署 | ✅ 完成 | 服务器 `8.138.164.133:5000` 内部测试正常 |
| 5 个新 Blueprint | ✅ 完成 | ai_compare, image_prompt, ai_debate, dialogue_learning, video_maker |
| 统一 DashScope API | ✅ 完成 | 所有 AI 功能使用 qwen3.5-plus |
| 前端 Demo 页面 | ✅ 存在 | 13 个 Demo 页面已创建 |

### ❌ 待解决的问题

| 问题 | 优先级 | 影响范围 | 状态 |
|------|--------|----------|------|
| 域名被劫持导致 HTTPS 无法访问 | P0 | 所有线上功能无法使用 | 🔍 已定位 |
| 云服务商安全组未开放端口 8000 | P0 | 前端无法外网访问 | ⏳ 需手动配置 |
| 登录认证流程未测试 | P1 | 用户无法使用在线工具 | ⏳ 待测试 |
| Demo 页面部分使用模拟数据 | P2 | 部分功能体验不完整 | ⏳ 待优化 |

### ✅ 最新完成

| 任务 | 完成时间 | 说明 |
|------|---------|------|
| 三端代码统一 | 2026-03-13 | 本地、GitHub、服务器代码已同步 |
| 前端错误处理优化 | 2026-03-13 | AI 辩论、台词学习、视频生成等页面 |
| Nginx 反向代理配置 | 2026-03-13 | 端口 8000 统一提供前端和 API |
| HTTPS 问题排查 | 2026-03-13 | 定位为域名被劫持 |

---

## 二、任务清单

### P0 - 紧急任务

#### 1. ✅ HTTPS 访问问题已定位

**问题根源**：域名 `api.liangyiren.top` 被劫持或被墙
- 通过域名访问 HTTPS 时，TLS 握手阶段连接被重置
- HTTP 请求被重定向到返回 403 的 "Beaver" 服务器
- 直接使用 IP 地址访问正常：`curl -k -I https://8.138.164.133/`
- SSL 证书有效（Let's Encrypt，有效期至 2026-06-10）
- 服务器内部访问正常：`curl https://api.liangyiren.top/` 返回正常

**已完成的配置**：
1. ✅ Nginx 在端口 8000 配置反向代理，统一提供前端和 API
2. ✅ 前端使用 `window.location.origin` 自动适配同源 API
3. ✅ 配置文件：`/etc/nginx/conf.d/integrity-web.conf`

**待完成的操作**（需手动）：
1. ⏳ 在阿里云控制台开放安全组端口 8000
2. ⏳ 或者：注册新域名并重新配置 DNS
3. ⏳ 或者：使用 Cloudflare CDN 绕过劫持

**临时访问方案**：
```bash
# 方案 1: 修改本地 hosts 文件（仅本地测试）
echo "8.138.164.133 api.liangyiren.top" >> /etc/hosts

# 方案 2: 使用 IP + 端口访问（需开放端口 8000）
http://8.138.164.133:8000/
```

---

### P1 - 核心功能任务

#### 2. 更新前端 API 路径

**问题**：部分 Demo 页面的 API 路径与后端不匹配

**需要修改的文件**：

| 文件 | 当前路径 | 正确路径 |
|------|----------|----------|
| `ai-compare.html:648` | `/api/tools/ai-compare` | `/api/tools/ai-compare/query` |
| `dialogue-learning.html:394` | `/api/tools/dialogue-learning/process` | ✅ 正确 |
| `video-maker.html:370` | `/api/tools/video-maker/generate` | ✅ 正确 |
| `image-prompt.html` | 使用模拟数据 | 需连接真实 API |

#### 3. 连接 Demo 页面到真实 API

**3.1 ai-compare.html - 多模型对比**

- [x] 修改 API 路径为 `/api/tools/ai-compare/query`（已使用正确路径）
- [x] 删除硬编码的 providers 列表，改为从 API 获取（已实现 loadProvidersFromAPI）
- [ ] 测试登录后调用功能

**3.2 ai-debate.html - AI 辩论赛**

- [ ] 删除 `simulateDebate()` 模拟函数（保留为 API 失败时的降级）
- [x] 实现 SSE 连接到 `/api/tools/ai-debate/start`
- [x] 处理 `event: stage/message/result` 事件（含 eventType 区分 chunk/message）
- [x] 实现流式显示（tools-online.js 与 demo 页均已修复 undefined 并支持流式）

**3.3 image-prompt.html - 图文互转**

- [x] 图片转提示词：连接 `/api/tools/image-prompt/analyze`
- [x] 提示词优化：连接 `/api/tools/image-prompt/generate`
- [x] 删除模拟函数 `generateMockPrompt()`

**3.4 dialogue-learning.html - 台词学习**

- [x] 确认 API 路径正确
- [x] 测试 PDF 上传和轮询流程
- [x] 添加错误处理（服务器错误信息展示、轮询失败处理、results 空防护）

**3.5 video-maker.html - 视频生成**

- [x] 添加任务轮询逻辑（异步任务）
- [x] 实现进度显示
- [x] 处理无 FFmpeg 的情况（仅返回剧本）

#### 4. 完善登录认证流程

**4.1 tools.html 登录功能**

- [ ] 测试注册功能（需要邀请码）
- [ ] 测试登录功能
- [ ] 测试 Token 验证
- [ ] 处理 Token 过期刷新

**4.2 登录状态同步**

- [ ] 确认 `demos-common.js` 的 `checkAuth()` 正常工作
- [ ] 确认各 Demo 页面登录状态显示正确
- [ ] 实现 Token 过期自动跳转登录

---

### P2 - 优化任务

#### 5. 优化用户体验

- [ ] 添加加载动画/骨架屏
- [ ] 优化错误提示信息
- [ ] 添加操作成功/失败的 Toast 提示
- [ ] 实现请求超时重试

#### 6. 更新 README 文档

- [ ] 更新 API 端点列表
- [ ] 添加新功能使用说明
- [ ] 更新部署文档

---

## 三、具体代码修改任务

### 任务 3.1：修复 ai-compare.html API 调用

```javascript
// 修改第 648 行
// 旧代码
const response = await fetch(`${API_BASE}/api/tools/ai-compare`, {

// 新代码
const response = await fetch(`${API_BASE}/api/tools/ai-compare/query`, {
```

```javascript
// 修改第 426-457 行，删除硬编码 providers，改为动态获取
// 在 DOMContentLoaded 中添加：
async function loadProviders() {
    try {
        const response = await fetch(`${API_BASE}/api/tools/ai-compare/providers`);
        const data = await response.json();
        // 使用 data.providers 渲染 UI
    } catch (error) {
        console.error('Failed to load providers:', error);
    }
}
```

### 任务 3.2：实现 ai-debate.html SSE 连接

```javascript
// 替换 simulateDebate 函数
async function startRealDebate(topic, rounds) {
    const { token } = DemoUtils.checkAuth();
    
    const eventSource = new EventSource(
        `${API_BASE}/api/tools/ai-debate/start?` + 
        new URLSearchParams({
            topic: topic,
            rounds: rounds,
            token: token  // 或通过 header 传递
        })
    );
    
    eventSource.addEventListener('stage', (e) => {
        const data = JSON.parse(e.data);
        updateStage(data.stage, data.desc);
    });
    
    eventSource.addEventListener('message', (e) => {
        const data = JSON.parse(e.data);
        addDebateMessage(data.speaker, data.role, data.side, data.content);
    });
    
    eventSource.addEventListener('result', (e) => {
        const data = JSON.parse(e.data);
        showDebateResult(data.winner, data.comment);
        eventSource.close();
    });
    
    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
    };
}
```

### 任务 3.3：实现 image-prompt.html 真实 API 调用

```javascript
// 图片转提示词
async function generatePrompts() {
    const { token, isLoggedIn } = DemoUtils.checkAuth();
    if (!isLoggedIn) {
        DemoUtils.showMessage('请先登录', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('image', selectedFiles[0]);
    formData.append('style', selectedStyle);

    const response = await fetch(`${API_BASE}/api/tools/image-prompt/analyze`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });

    const data = await response.json();
    // 显示 data.prompt
}

// 提示词转图片（由于没有 DALL-E，改为优化提示词）
async function generateImages() {
    const response = await fetch(`${API_BASE}/api/tools/image-prompt/generate`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            prompt: document.getElementById('prompt-text').value,
            size: document.getElementById('image-size').value,
            count: parseInt(document.getElementById('image-count').value)
        })
    });

    const data = await response.json();
    // 显示优化后的提示词（data.optimized_prompt）
}
```

---

## 四、测试清单

### 功能测试

| 功能 | 测试项 | 预期结果 |
|------|--------|----------|
| 登录 | 注册新用户 | 成功获取 Token |
| 登录 | 登录已有用户 | 成功获取 Token |
| 登录 | Token 验证 | 返回用户信息 |
| AI Compare | 获取 providers | 返回 4 个提供商 |
| AI Compare | 提交问题 | 返回模型响应 |
| AI Debate | SSE 连接 | 实时显示辩论 |
| Image Prompt | 图片分析 | 返回提示词 |
| Image Prompt | 提示词优化 | 返回优化后的提示词 |
| Dialogue | PDF 上传 | 返回 task_id |
| Dialogue | 轮询状态 | 返回进度和结果 |
| Video Maker | 提交任务 | 返回 task_id |
| Video Maker | 获取结果 | 返回剧本/视频 |

### 边界测试

- [ ] 未登录访问需要认证的 API
- [ ] Token 过期后的处理
- [ ] 大文件上传
- [ ] 长时间任务超时

---

## 五、部署检查清单

### 服务器检查

```bash
# SSH 到服务器
ssh root@8.138.164.133

# 1. 检查服务运行状态
ps aux | grep gunicorn

# 2. 检查端口监听
netstat -tlnp | grep 5000

# 3. 测试内部 API
curl http://localhost:5000/
curl http://localhost:5000/api/tools/ai-compare/providers

# 4. 检查 Nginx 配置
cat /etc/nginx/sites-enabled/default
nginx -t

# 5. 检查 SSL 证书
certbot certificates

# 6. 检查日志
tail -f /root/integrity-api/server/gunicorn.error.log
tail -f /var/log/nginx/error.log
```

### DNS 和网络检查

```bash
# 本地执行
nslookup api.liangyiren.top
ping api.liangyiren.top
curl -I https://api.liangyiren.top/
```

---

## 六、优先级执行顺序

1. **立即执行**：修复外网 HTTPS 访问问题（P0）
2. **第二步**：更新 ai-compare.html API 路径（P1）
3. **第三步**：测试登录认证流程（P1）
4. **第四步**：实现 AI Debate SSE 连接（P1）
5. **第五步**：连接其他 Demo 到真实 API（P1）
6. **最后**：优化用户体验和文档（P2）

---

## 七、相关文件索引

| 类型 | 文件路径 |
|------|----------|
| 后端主入口 | `docs/server/app/main.py` |
| AI 对比 | `docs/server/app/tools/ai_compare.py` |
| 图文互转 | `docs/server/app/tools/image_prompt.py` |
| AI 辩论 | `docs/server/app/tools/ai_debate.py` |
| 台词学习 | `docs/server/app/tools/dialogue_learning.py` |
| 视频生成 | `docs/server/app/tools/video_maker.py` |
| Demo 页面 | `docs/demos/*.html` |
| 通用 JS | `docs/assets/js/demos-common.js` |
| 登录 JS | `docs/assets/js/tools-auth.js` |

---

*文档最后更新：2026-03-13*