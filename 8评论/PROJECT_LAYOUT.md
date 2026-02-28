# 8评论 项目整理建议

目标是让目录保持三件事清晰:
- 哪些是长期维护的源码
- 哪些是可随时删除的运行产物
- 哪些是本地敏感配置

## 推荐分层

建议保持如下结构（现有代码可逐步迁移，不必一次完成）：

```text
8评论/
├── main.py
├── config.py                  # 本地私有配置（不进仓库）
├── config.example.py          # 配置模板（可提交）
├── requirements.txt
├── README.md
├── PROJECT_LAYOUT.md
├── analyzer/                  # LLM 分析模块
├── scrapers/                  # 评论抓取模块
├── searchers/                 # 搜索模块
├── topic/                     # 话题流水线
├── utils/                     # 通用工具
├── scripts/
│   └── debug_archive/         # 临时调试脚本归档
├── output/                    # 运行输出（CSV/TXT）
└── docs/                      # 可选：扩展文档
```

## 日常整理约定

- `output/` 只放运行结果，不放源码。
- `scripts/debug_archive/` 只放一次性调试脚本，稳定后迁移到正式模块。
- `config.py` 只在本机使用；分享项目时只提供 `config.example.py`。
- 每次提交前清理 `__pycache__/` 和临时文件，避免污染版本历史。

## 已落地的基础整理

- 新增 `.gitignore`，默认忽略缓存、运行产物、代理与环境变量文件。
- 新增 `config.example.py`，用于无敏感信息的配置分发。
