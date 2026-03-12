# Integrity Lab - 认证系统说明

## 🔐 认证系统概述

Integrity Lab 采用基于 JWT (JSON Web Token) 的认证系统，确保只有注册用户才能使用在线工具。所有演示页面和在线工具都需要登录后才能访问核心功能。

---

## 📋 账号注册规则

### 注册要求

**用户名规则**：
- 长度：3-20 个字符
- 允许字符：字母、数字、下划线
- 不允许：特殊符号、空格
- 唯一性：用户名不能重复

**密码规则**：
- 最小长度：6 位
- 建议：包含字母和数字的组合
- 安全提示：建议使用 8 位以上的强密码

**邀请码规则**：
- 必须提供有效的邀请码才能注册
- 邀请码区分大小写
- 每个邀请码可以被多次使用

### 当前有效邀请码

```
demo2026      # 演示账号专用
test2026      # 测试账号专用
friend2026    # 朋友分享专用
```

> **获取邀请码**：如需邀请码，请联系管理员或通过 GitHub Issue 申请

---

## 🔑 登录流程

### 1. 前端登录步骤

```javascript
// 1. 用户点击"登录"按钮
// 2. 弹出登录表单
// 3. 输入用户名和密码
// 4. 提交登录请求

const response = await fetch('https://api.liangyiren.top/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'your_username',
        password: 'your_password'
    })
});

const data = await response.json();
// 返回：{ message: '登录成功', token: 'jwt_token', username: 'your_username' }
```

### 2. Token 存储

登录成功后，系统会将 Token 和用户名存储在浏览器的 `localStorage` 中：

```javascript
localStorage.setItem('token', data.token);
localStorage.setItem('username', data.username);
```

### 3. Token 使用

后续所有 API 请求都需要在 Header 中携带 Token：

```javascript
const token = localStorage.getItem('token');

fetch('https://api.liangyiren.top/api/tools/pdf/merge', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ' + token
    },
    body: formData
});
```

### 4. 退出登录

```javascript
localStorage.removeItem('token');
localStorage.removeItem('username');
// 刷新页面或跳转到首页
```

---

## 🛡️ Token 安全机制

### Token 特性

- **类型**：JWT (JSON Web Token)
- **有效期**：7 天
- **算法**：HS256
- **存储位置**：浏览器 localStorage

### Token 内容

```json
{
    "user_id": 123,
    "exp": 1710000000  // 过期时间戳
}
```

### 安全措施

1. **HTTPS 传输**：所有 API 请求通过 HTTPS 加密传输
2. **密码哈希**：密码使用 SHA256 哈希后存储，不存储明文
3. **Token 过期**：Token 7 天后自动过期，需要重新登录
4. **CORS 限制**：API 仅允许特定域名访问
5. **账户禁用**：管理员可以禁用违规账户

---

## 🚫 访问控制

### 游客可访问（无需登录）

- ✅ 首页 (`index.html`)
- ✅ AI 热点页面 (`news.html`)
- ✅ 工具库页面 (`tools.html`) - 仅查看
- ✅ 演示区域 - 前端模拟演示
- ✅ 源码浏览 - 查看项目介绍

### 需要登录才能访问

- 🔒 所有在线工具（PDF 工具集等）
- 🔒 所有演示页面的实际功能
- 🔒 文件上传和处理
- 🔒 API 调用

### 前端权限检查

所有需要登录的功能都会先检查 Token：

```javascript
const { token, isLoggedIn } = DemoUtils.checkAuth();

if (!isLoggedIn) {
    DemoUtils.showMessage('请先登录', 'error');
    window.location.href = '../tools.html';  // 跳转到登录页面
    return;
}

// 继续执行需要登录的操作
```

---

## 📝 注册流程

### 1. 前端注册步骤

```javascript
// 1. 用户点击"注册"链接
// 2. 切换到注册表单
// 3. 输入用户名、密码、邀请码
// 4. 提交注册请求

const response = await fetch('https://api.liangyiren.top/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'new_username',
        password: 'new_password',
        invite_code: 'demo2026'
    })
});

const data = await response.json();
// 返回：{ message: '注册成功', token: 'jwt_token', username: 'new_username' }
```

### 2. 注册验证

后端会进行以下验证：

1. ✅ 用户名不能为空
2. ✅ 用户名长度 3-20 字符
3. ✅ 用户名不能重复
4. ✅ 密码不能为空
5. ✅ 密码长度至少 6 位
6. ✅ 邀请码必须有效

### 3. 自动登录

注册成功后，系统会自动返回 Token，前端自动完成登录，无需再次输入密码。

---

## 🔄 Token 刷新机制

### 当前机制

- Token 有效期：7 天
- 过期后需要重新登录
- 暂不支持自动刷新

### 未来计划

- 实现 Refresh Token 机制
- 支持 Token 自动续期
- 添加"记住我"功能

---

## 🧪 测试账号

### 开发测试账号

```
用户名：test
密码：123456
邀请码：demo2026
```

> **注意**：测试账号仅供开发测试使用，请勿在生产环境使用

### 创建自己的账号

1. 访问 https://zhimingliang897-web.github.io/integrity/tools.html
2. 点击"登录"按钮
3. 点击"注册"链接
4. 输入用户名、密码和邀请码（demo2026）
5. 点击"注册"按钮
6. 注册成功后自动登录

---

## 🛠️ 后端 API 接口

### 1. 注册接口

**请求**：
```http
POST /api/auth/register
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password",
    "invite_code": "demo2026"
}
```

**成功响应**：
```json
{
    "message": "注册成功",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "username": "your_username"
}
```

**错误响应**：
```json
{
    "error": "用户名已存在"
}
```

### 2. 登录接口

**请求**：
```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

**成功响应**：
```json
{
    "message": "登录成功",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "username": "your_username"
}
```

**错误响应**：
```json
{
    "error": "用户名或密码错误"
}
```

### 3. Token 验证接口

**请求**：
```http
GET /api/auth/verify
Authorization: Bearer your_token
```

**成功响应**：
```json
{
    "valid": true,
    "username": "your_username"
}
```

**错误响应**：
```json
{
    "valid": false
}
```

---

## 🐛 常见问题

### 1. Token 过期怎么办？

**现象**：API 请求返回 401 错误

**解决方案**：
- 重新登录获取新的 Token
- Token 有效期为 7 天，过期后必须重新登录

### 2. 忘记密码怎么办？

**当前方案**：
- 暂不支持密码找回功能
- 请联系管理员重置密码

**未来计划**：
- 添加邮箱验证功能
- 支持密码找回

### 3. 邀请码在哪里获取？

**获取方式**：
- 使用公开邀请码：`demo2026`、`test2026`、`friend2026`
- 联系管理员申请专属邀请码
- 通过 GitHub Issue 申请

### 4. 为什么需要邀请码？

**原因**：
- 防止恶意注册
- 控制用户数量
- 保护服务器资源
- 确保用户质量

### 5. 可以修改用户名或密码吗？

**当前状态**：
- 暂不支持修改用户名
- 暂不支持修改密码

**未来计划**：
- 添加个人资料编辑功能
- 支持密码修改

### 6. 账户会被禁用吗？

**禁用原因**：
- 违反使用规则
- 恶意使用服务
- 频繁上传大文件
- 滥用 API 接口

**申诉方式**：
- 通过 GitHub Issue 联系管理员
- 说明情况并申请解封

---

## 📊 数据存储

### 用户数据

**存储位置**：SQLite 数据库 (`data/users.db`)

**存储内容**：
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    invite_code VARCHAR(32),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

**隐私保护**：
- 密码使用 SHA256 哈希存储，不存储明文
- 不收集个人敏感信息
- 不记录用户操作日志（除错误日志外）

### 本地存储（浏览器）

**localStorage 存储内容**：
```javascript
{
    "token": "jwt_token_string",
    "username": "your_username"
}
```

**清除方式**：
- 退出登录时自动清除
- 浏览器清除缓存时清除
- 手动清除：浏览器开发者工具 → Application → Local Storage

---

## 🔒 安全建议

### 用户端

1. **使用强密码**：至少 8 位，包含字母、数字和符号
2. **不要共享账号**：每个人使用自己的账号
3. **定期更换密码**：建议每 3 个月更换一次（功能开发中）
4. **注意钓鱼网站**：只在官方域名登录
5. **公共电脑使用后退出**：使用公共电脑后记得退出登录

### 开发者端

1. **不要硬编码 Token**：不要在代码中写死 Token
2. **使用 HTTPS**：所有 API 请求使用 HTTPS
3. **验证 Token 有效性**：每次请求前检查 Token
4. **处理 Token 过期**：捕获 401 错误并提示重新登录
5. **不要在 URL 中传递 Token**：使用 Header 传递

---

## 📞 技术支持

### 遇到问题？

1. **查看文档**：先查看本文档和 README.md
2. **检查控制台**：打开浏览器开发者工具查看错误信息
3. **提交 Issue**：https://github.com/zhimingliang897-web/integrity/issues
4. **联系管理员**：通过 GitHub 联系

### 反馈建议

欢迎通过以下方式提供反馈：
- GitHub Issue
- Pull Request
- 邮件联系

---

## 📄 相关文档

- `README.md` - 项目总体说明
- `DEMO_QUICK_START.md` - 演示页面开发指南
- `PROJECT_PROGRESS_REPORT.md` - 项目进度报告
- `server/README.md` - 后端 API 文档

---

**文档版本**：v2.0  
**最后更新**：2026-03-12  
**维护者**：Integrity Lab Team
