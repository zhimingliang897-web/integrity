# 认证系统快速参考

## 🔐 登录信息

### 测试账号
```
用户名：test
密码：123456
```

### 有效邀请码
```
demo2026      # 演示账号专用
test2026      # 测试账号专用
friend2026    # 朋友分享专用
```

---

## 📋 注册规则

### 用户名
- 长度：3-20 个字符
- 允许：字母、数字、下划线
- 唯一性：不能重复

### 密码
- 最小长度：6 位
- 建议：8 位以上，包含字母和数字

### 邀请码
- 必须提供有效的邀请码
- 区分大小写
- 可重复使用

---

## 🔑 Token 信息

- **类型**：JWT (JSON Web Token)
- **有效期**：7 天
- **存储位置**：浏览器 localStorage
- **传递方式**：HTTP Header `Authorization: Bearer <token>`

---

## 🚫 访问控制

### 游客可访问（无需登录）
- ✅ 首页、AI 热点、工具库页面
- ✅ 演示区域（前端模拟）
- ✅ 源码浏览

### 需要登录
- 🔒 所有在线工具（PDF 工具集等）
- 🔒 所有演示页面的实际功能
- 🔒 文件上传和处理
- 🔒 API 调用

---

## 📝 快速注册

1. 访问 https://zhimingliang897-web.github.io/integrity/tools.html
2. 点击"登录"按钮
3. 点击"注册"链接
4. 输入用户名、密码和邀请码（demo2026）
5. 点击"注册"按钮
6. 注册成功后自动登录

---

## 🔧 前端权限检查

所有演示页面都使用以下代码检查登录状态：

```javascript
const { token, isLoggedIn } = DemoUtils.checkAuth();

if (!isLoggedIn) {
    DemoUtils.showMessage('请先登录', 'error');
    window.location.href = '../tools.html';
    return;
}

// 继续执行需要登录的操作
```

---

## 📚 详细文档

查看 [AUTH_SYSTEM.md](AUTH_SYSTEM.md) 了解完整的认证系统说明。

---

**最后更新**：2026-03-12
