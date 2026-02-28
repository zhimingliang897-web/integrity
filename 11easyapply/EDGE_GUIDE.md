# EasyApply – Edge 浏览器使用指南

EasyApply 基于 Chrome Extension **Manifest V3** 标准开发，该标准自 Edge 100 起完全兼容，**无需修改任何代码**。

---

## 🚀 方式一：开发者模式直接加载（推荐测试用）

1. 打开 Microsoft Edge 浏览器
2. 地址栏输入 `edge://extensions/` 并回车
3. 右上角开启 **「开发人员模式」**
4. 点击 **「加载解压缩的扩展」**
5. 选择 `easyapply` 文件夹（含 `manifest.json` 的那一层）
6. 插件图标出现在工具栏后即可使用，功能与 Chrome 版完全一致 ✅

---

## 🏪 方式二：发布到 Edge 附加组件商店

如需正式发布，请按以下步骤操作：

### 1. 打包插件

```bash
# 将 easyapply 目录打包为 zip
# Windows 右键 → 发送到 → 压缩文件夹
# 或使用命令行：
Compress-Archive -Path .\easyapply\* -DestinationPath .\easyapply.zip
```

### 2. 注册开发者账号

- 访问 [Microsoft Partner Center](https://partner.microsoft.com/dashboard)
- 登录 Microsoft 账号
- 进入 **Edge 加载项** 部分，完成开发者注册（免费）

### 3. 提交审核

- 上传 `easyapply.zip`
- 填写商店信息（名称/描述/截图）
- 提交后通常 **1–3 个工作日**完成审核

---

## 🔑 Chrome 与 Edge 的关键区别

| 项目 | Chrome Web Store | Microsoft Edge Add-ons |
|------|-----------------|------------------------|
| 开发者注册费 | $5 一次性 | 免费 |
| 审核周期 | 约 3 天 | 1–3 工作日 |
| 发布平台 | chrome.google.com/webstore | microsoftedge.microsoft.com/addons |
| 代码兼容 | ✅ 原生 | ✅ 完全兼容 MV3 |

---

## ⚠️ 注意事项

- 同一份代码可同时发布到 Chrome 商店和 Edge 商店，不需要任何改动
- Edge 下载的 `.xlsx` 文件默认保存路径和 Chrome 相同（浏览器下载文件夹）
- 若在 Edge 中遇到 `chrome` API 不可用的问题，可在代码中用 `const browser = window.chrome || window.browser` 做兼容（本插件暂不涉及，因为 Edge 已内置 `chrome` 命名空间）
