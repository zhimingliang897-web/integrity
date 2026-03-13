# 小红书英语内容生成器

AI自动生成小红书英语教育内容，支持内容管理和一键发布。

## 功能特点

- AI自动生成选题、文案、知识点
- 自动生成精美封面和内容页图片
- 内容管理：查看待发布/已发布内容
- 支持自定义主题输入
- 一键发布到小红书
- Obsidian集成，导出发布队列

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 启动图形界面

```bash
python gui.py
```

浏览器自动打开 `http://127.0.0.1:7860`

### 3. 配置

在"设置"标签页配置：
- API Key：阿里千问或OpenAI的API Key
- Obsidian路径：你的vault路径

### 4. 获取小红书Cookie

1. 点击"刷新Cookie"
2. 浏览器自动打开小红书
3. 登录后程序自动获取
4. Cookie有效期约1-2周

### 5. 生成并发布

1. 选择分类或输入自定义主题
2. 设置知识点数量（建议5-8个）
3. 点击"开始生成"
4. 预览无误后点击"发布到小红书"

## 命令行使用

```bash
# 只生成内容
python main.py -c "餐饮美食"

# 自定义主题
python main.py --topic "咖啡店点单"

# 生成并私密发布
python main.py -c "交通出行" --publish --private

# 测试Cookie
python main.py --test-cookie
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-c, --category` | 分类 | 随机 |
| `-n, --phrase-count` | 知识点数量 | 5 |
| `--publish` | 自动发布 | 否 |
| `--private` | 私密发布 | 否 |
| `--no-obsidian` | 不导出Obsidian | 否 |

## 分类列表

| 分类 | 场景示例 |
|------|---------|
| 餐饮美食 | 点餐、咖啡店、餐厅 |
| 交通出行 | 打车、地铁、机场 |
| 购物消费 | 商场、超市、退换货 |
| 职场办公 | 会议、邮件、同事交流 |
| 社交聊天 | 聊天、约会、派对 |
| 旅行住宿 | 酒店、民宿、景点 |
| 医疗健康 | 看病、药店、症状描述 |
| 租房生活 | 租房、水电、邻居 |
| 校园学习 | 课堂、图书馆、考试 |
| 娱乐休闲 | 电影、健身、游戏 |

## 需补充的隐私/本地配置（未随仓库提交）

| 文件名 | 说明（对他人） | 样式/格式 |
|--------|----------------|-----------|
| **cookies.json** | 小红书登录态，用于发布与刷新 Cookie | JSON 数组，每项包含 `name`、`value`、`domain`、`path`、`expires`、`httpOnly`、`secure`、`sameSite`。可从浏览器登录小红书后导出，或运行本工具「刷新 Cookie」自动生成。 |

**自己使用**：从本仓库的 **`_secrets/15redbook/cookies.json`** 拷贝到本项目 `15redbook/` 目录下（文件名保持不变）即可。

## 项目结构

```
15redbook/
├── gui.py               # 图形界面
├── main.py              # 主程序
├── config.yaml          # 配置文件
├── cookies.json         # [需自行补充] 小红书 Cookie，见上方说明
├── llm_client.py        # LLM调用
├── prompts.py           # Prompt模板
├── html_renderer.py     # HTML渲染
├── image_generator.py   # 图片生成
├── xhs_publisher.py     # 小红书发布
├── cookie_manager.py    # Cookie管理
├── obsidian_exporter.py # Obsidian导出
└── output/              # 输出目录
    └── {batch_id}/
        ├── cover.png
        ├── slide_1~N.png
        ├── content.json
        ├── caption.txt
        └── publish_status.json
```

## 常见问题

**Q: Cookie失效？**
运行 `python cookie_manager.py --refresh` 重新登录

**Q: 发布失败？**
1. 检查Cookie是否有效
2. 标题不超过20字
3. 先私密发布测试

**Q: 知识点数量？**
建议5-8个，太多影响阅读
