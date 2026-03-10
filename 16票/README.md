# 大麦自动抢票工具

通过电脑控制手机，自动完成大麦APP抢票流程。

## 快速开始

### 1. 创建Conda环境

```bash
cd e:\integrity\16票
conda env create -f environment.yml
conda activate damai
```

### 2. 初始化设备（首次需要）

```bash
python -m uiautomator2 init
```

### 3. 测试连接

```bash
python test_connection.py
```

### 4. 配置抢票信息

编辑 `config.py`:

```python
# 抢票时间
TARGET_TIME = "2026-03-20 10:00:00"

# 观演人姓名（必须与大麦APP中一致）
VIEWER_NAMES = ["你的姓名"]

# 票价优先级
PRICE_PRIORITY = ["580", "380", "280"]
```

### 5. 运行抢票

```bash
# 抢票当天，提前5分钟运行
python main.py
```

## 使用前准备

1. **手机端**
   - 开启USB调试（设置 → 开发者选项 → USB调试）
   - 开启USB调试(安全设置)
   - 登录大麦APP
   - 添加实名观演人

2. **电脑端**
   - 安装ADB工具
   - 安装Conda环境

详细步骤请查看 [SETUP_GUIDE.md](SETUP_GUIDE.md)

## 抢票流程

1. 手机USB连接电脑
2. 打开大麦APP，进入演出详情页
3. 运行 `python main.py`
4. 等待开票时间
5. 脚本自动执行抢票
6. 在手机上完成支付

## 文件说明

| 文件 | 说明 |
|------|------|
| config.py | 配置文件，设置抢票时间、票价等 |
| main.py | 主程序入口 |
| damai_buyer.py | 抢票核心逻辑 |
| device_helper.py | 设备连接工具 |
| test_connection.py | 连接测试脚本 |

## 注意事项

- 此工具仅供学习研究
- 热门演出竞争激烈，不保证100%成功
- 建议先用冷门演出测试完整流程
- 实名制演出需提前在大麦APP添加观演人
