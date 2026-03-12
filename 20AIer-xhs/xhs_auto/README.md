# 🦞 小红书图文自动化生成器

将 `.txt` 文章一键转换为小红书图文，包含：
- 封面图 + 内容页
- 评论区建议 + Tags

---

## 快速开始

### 1. 安装依赖
```bash
cd 20AIer-xhs/xhs_auto
pip install -r requirements.txt
```

### 2. 准备文章
把文章保存为 `.txt` 文件，例如 `my_article.txt`

### 3. 运行
```bash
python main.py my_article.txt
```

### 4. 输出
自动生成到 `output/my_article/`：
- `slide_00_cover.png` - 封面
- `slide_01.png` ~ `slide_0N.png` - 内容页
- `comments.txt` - 评论区建议 + Tags

---

## 配置 (config.yaml)

### API
```yaml
api:
  api_key: sk-xxx        # 阿里云百炼 API Key
  model: qwen3.5-plus
```

### 封面样式
```yaml
cover:
  font_size_line1: 62    # 第一行字号
  font_size_line2: 72    # 第二行字号
  font_size_single: 78   # 单行字号
  title_color: "#1A1A2E" # 标题颜色
  underline_color: "#667EEA" # 下划线颜色
  stroke_width: 2        # 描边宽度
  line_height: 1.3       # 行高
```

### 内容页样式
```yaml
font_sizes:
  title: 44
  body: 32
  label: 24

line_height:
  title: 1.4
  body: 1.6
  block: 1.55
```

### 主题配色
```yaml
theme:
  bg: "#F8F6F3"     # 背景
  card_bg: "#FFFFFF" # 卡片
  top_bar: "#667EEA" # 渐变起点
  top_bar2: "#764BA2" # 渐变终点

layout:
  center_title: true
  card_shadow: true
  card_margin: 32

bg_gradient: true
```

---

## 生成内容说明

### 封面
- 自动提取第一页标题
- 大字居中 + 下划线装饰
- 渐变背景 + 白色卡片

### 内容页
- 每页 1-2 个信息点
- 少即是多，读得进去
- 说人话，不堆砌
- 结尾直接结束，不加"评论区见"

### 评论区建议
- 3 条精炼建议
- 5 个相关 Tags
- 不打广告，实事求是

---

## 注意事项

1. Windows 字体用微软雅黑，macOS 用苹方
2. API Key 在阿里云百炼获取
3. 内容有问题可以调 `llm_formatter.py` 的 Prompt