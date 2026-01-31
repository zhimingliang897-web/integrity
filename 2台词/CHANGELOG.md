# 更新日志

## v5 — 删除 + 上传修复

- Day 卡片右上角新增删除按钮，hover 显示，点击二次确认后删除整个 day 文件夹
- 修复拖拽上传 `No file` 报错（`closeModal` 提前清空了文件引用）
- 上传弹窗自动建议下一个 Day 编号，支持手动修改
- 已存在的 Day 拒绝覆盖，防止误操作

## v4 — 本地 Web 学习界面

- 新增 `app.py`：Flask 本地 Web 应用，替代直接看 Markdown
- 单词卡片式美化展示：大标题、释义高亮、对话分块、影视来源标签
- 顶部快速导航栏，点击单词跳转
- 拖拽上传 PDF：弹窗指定 Day 编号，自动创建文件夹并后台执行完整处理流水线
- 处理进度实时轮询（extracting → scraping → formatting → done）

## v3 — LLM 生成学习笔记

- 新增 `quote_formatter.py`：读取 JSON 台词数据，调 LLM 生成学习笔记
- 每个单词生成中英释义 + 2-3 段精选影视对话
- 对话附中文翻译，标注影视来源和年份
- 输出 `dayN_study.md`，按 `## word` 分节、`---` 分隔

## v2 — 影视台词搜索

- 新增 `pop_mystic_scraper.py`：通过 popmystic.com OpenSearch API 批量查询台词
- 每个单词返回数百条影视引用（标题、年份、剧集、台词原文）
- 输出 `dayN.json` + `dayN.csv`，已有文件自动跳过

## v1 — PDF 单词提取

- 新增 `pdf_extractor.py`：从 PDF 提取最大字号字符
- LLM 自动拆分连续字符为独立单词（deepseek-v3.2）
- 支持 auto / interactive 两种模式
- 按 `word/day*/` 目录结构批量扫描处理
