# EasyApply - 智能简历填充助手

一款浏览器扩展，帮助你快速填充招聘网站表单，并自动追踪投递记录。

## 功能特性

- **一键填充**：保存简历信息，在任意招聘网站一键自动填充表单
- **多简历管理**：支持创建多份简历配置（如：校招版、社招版）
- **投递追踪**：自动记录每次投递的公司、岗位、时间、链接
- **Excel 导出**：投递记录可导出为 Excel，方便统计和管理
- **本地备份**：每次保存自动备份到本地 JSON 文件
- **跨浏览器**：兼容 Chrome 和 Edge 浏览器

## 安装方法

### Chrome 浏览器

1. 打开 `chrome://extensions/`
2. 右上角开启「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择 `11easyapply` 文件夹

### Edge 浏览器

1. 打开 `edge://extensions/`
2. 右上角开启「开发人员模式」
3. 点击「加载解压缩的扩展」
4. 选择 `11easyapply` 文件夹

详细说明见 [EDGE_GUIDE.md](EDGE_GUIDE.md)

## 使用方法

### 填充简历

1. 点击浏览器工具栏的扩展图标
2. 在「简历信息」Tab 填写/编辑你的信息
3. 打开招聘网站的简历填写页面
4. 点击「一键填充」按钮

### 投递记录

- 填充后会弹出确认框，保存本次投递记录
- 在「投递记录」Tab 查看所有记录
- 支持修改状态（待跟进/面试中/已拒绝/已Offer）
- 支持内联编辑面试时间和备注

### 导出与备份

- **导出 Excel**：点击按钮，选择保存位置（建议存到本项目文件夹）
- **下载当前投递记录**：一键下载当前记录 JSON 备份到本地
- **说明**：扩展内已不提供“导入备份/一键去重”，建议在本地处理后自行归档

### 本地 Excel 去重（整行完全一致才删除）

项目内提供脚本：`excel_exact_dedup.py`

- 规则：只有“整行每个单元格都一致”才判定重复
- 行为：重复行只删后续副本，保留第一条
- 保留差异：只要任意单元格不同，就保留

先安装依赖：

```bash
pip install openpyxl
```

常用命令（在仓库根目录执行）：

```bash
# 处理所有工作表（默认首行视为表头，不参与去重）
python ./11easyapply/excel_exact_dedup.py "./11easyapply/投递记录_2026-3-11.xlsx"

# 指定输出文件
python ./11easyapply/excel_exact_dedup.py "./11easyapply/投递记录_2026-3-11.xlsx" -o "./11easyapply/投递记录_2026-3-11_去重后.xlsx"

# 仅处理某个工作表
python ./11easyapply/excel_exact_dedup.py "./11easyapply/投递记录_2026-3-11.xlsx" --sheet "📑 详细记录"

# 首行也参与去重
python ./11easyapply/excel_exact_dedup.py "./11easyapply/投递记录_2026-3-11.xlsx" --no-header
```

## 文件说明

```
11easyapply/
├── manifest.json      # 扩展配置文件
├── background.js      # 后台服务脚本
├── content.js         # 页面内容脚本（负责填充表单）
├── popup.html         # 扩展弹窗界面
├── popup.js           # 弹窗逻辑（简历管理、投递记录）
├── excel_exact_dedup.py # 本地 Excel 精确去重脚本
├── lib/
│   └── xlsx.min.js    # SheetJS 库（Excel 读写）
└── 投递记录_*.xlsx    # 导出的投递记录
```

## 数据存储

- **浏览器存储**：`chrome.storage.local`
  - `profiles`：简历配置
  - `applicationRecords`：投递记录
- **本地备份**：每次保存自动下载到 `下载目录/投递记录_自动备份.json`

## 版本

当前版本：v1.1
