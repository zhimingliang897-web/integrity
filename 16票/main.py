# -*- coding: utf-8 -*-
"""
大麦自动抢票 - 主程序入口
"""

import sys
import time
from datetime import datetime

import config
from device_helper import DeviceHelper
from damai_buyer import DamaiBuyer


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    大麦自动抢票工具                          ║
║                                                              ║
║  使用说明:                                                   ║
║  1. 确保手机已通过USB连接电脑                                ║
║  2. 确保大麦APP已打开并停在演出详情页                        ║
║  3. 修改 config.py 配置抢票时间和票价                        ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_config():
    """打印当前配置"""
    print("\n当前配置:")
    print("-" * 40)
    print(f"  抢票时间:   {config.TARGET_TIME}")
    print(f"  购票数量:   {config.TICKET_COUNT}")
    print(f"  观演人:     {', '.join(config.VIEWER_NAMES)}")
    print(f"  票价优先级: {' > '.join(config.PRICE_PRIORITY)}")
    if config.SESSION_PRIORITY:
        print(f"  场次优先级: {' > '.join(config.SESSION_PRIORITY)}")
    print(f"  抢票模式:   {config.MODE}")
    print("-" * 40)


def countdown_callback(remaining):
    """倒计时回调函数"""
    if remaining > 60:
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        print(f"\r[*] 距离开票还有: {minutes:02d}:{seconds:02d}    ", end="", flush=True)
    elif remaining > 10:
        print(f"\r[*] 距离开票还有: {remaining:.1f} 秒    ", end="", flush=True)
    else:
        print(f"\r[!] 倒计时: {remaining:.3f} 秒    ", end="", flush=True)


def main():
    """主函数"""
    print_banner()
    print_config()

    # 创建设备助手
    device = DeviceHelper()

    # 连接设备
    print("\n[*] 正在连接设备...")
    if not device.connect():
        print("\n[×] 无法连接设备，请检查:")
        print("    1. 手机是否通过USB连接")
        print("    2. USB调试是否开启")
        print("    3. 是否已授权调试")
        sys.exit(1)

    # 同步时间
    print("\n[*] 正在同步网络时间...")
    device.sync_time()

    # 创建抢票器
    buyer = DamaiBuyer(device)

    # 检查页面状态
    print("\n[*] 检查页面状态...")
    if not buyer.check_page_ready():
        print("\n[!] 警告: 未检测到购买按钮")
        response = input("是否继续? (y/n): ")
        if response.lower() != 'y':
            print("已退出")
            sys.exit(0)

    # 解析目标时间
    try:
        target_dt = datetime.strptime(config.TARGET_TIME, "%Y-%m-%d %H:%M:%S")
        target_ts = target_dt.timestamp()
    except ValueError:
        print(f"\n[×] 时间格式错误: {config.TARGET_TIME}")
        print("    正确格式: YYYY-MM-DD HH:MM:SS")
        sys.exit(1)

    # 检查时间
    current_ts = device.get_accurate_time()
    if target_ts <= current_ts:
        print(f"\n[!] 目标时间已过，将立即执行抢票")
        response = input("是否立即开始? (y/n): ")
        if response.lower() != 'y':
            print("已退出")
            sys.exit(0)
    else:
        remaining = target_ts - current_ts
        print(f"\n[√] 将在 {config.TARGET_TIME} 开始抢票")
        print(f"    距离开票还有 {remaining:.0f} 秒")
        print("\n[*] 等待中... (按 Ctrl+C 取消)")

        # 等待开票时间
        try:
            device.wait_until(config.TARGET_TIME, callback=countdown_callback)
        except KeyboardInterrupt:
            print("\n\n[!] 用户取消")
            sys.exit(0)

    print("\n\n" + "=" * 50)
    print("⚡ 开始抢票！")
    print("=" * 50)

    # 执行抢票
    start_time = time.time()

    if config.MODE == "rush":
        success = buyer.quick_buy()
    else:
        success = buyer.run()

    end_time = time.time()
    elapsed = end_time - start_time

    # 结果
    print("\n" + "=" * 50)
    if success:
        print(f"[√] 抢票流程完成！耗时: {elapsed:.2f} 秒")
        print("[!] 请立即在手机上完成支付！")
    else:
        print(f"[×] 抢票可能未成功，耗时: {elapsed:.2f} 秒")
        print("[!] 请检查手机屏幕")

    print("=" * 50)

    # 最终截图
    device.screenshot("final_result.png")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] 用户中断")
    except Exception as e:
        print(f"\n[×] 程序错误: {e}")
        import traceback
        traceback.print_exc()
