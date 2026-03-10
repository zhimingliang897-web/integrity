# -*- coding: utf-8 -*-
"""
设备连接测试脚本
用于验证手机连接和基础操作是否正常
"""

import sys
import time

from device_helper import DeviceHelper
import config


def test_connection():
    """测试设备连接"""
    print("=" * 50)
    print("测试1: 设备连接")
    print("=" * 50)

    device = DeviceHelper()
    if device.connect():
        print("[√] 测试通过\n")
        return device
    else:
        print("[×] 测试失败\n")
        return None


def test_time_sync(device):
    """测试时间同步"""
    print("=" * 50)
    print("测试2: 网络时间同步")
    print("=" * 50)

    offset = device.sync_time()
    if offset is not None:
        print("[√] 测试通过\n")
        return True
    else:
        print("[×] 测试失败（将使用本地时间）\n")
        return False


def test_screenshot(device):
    """测试截图功能"""
    print("=" * 50)
    print("测试3: 截图功能")
    print("=" * 50)

    filepath = device.screenshot("test_screenshot.png")
    if filepath:
        print("[√] 测试通过\n")
        return True
    else:
        print("[×] 测试失败\n")
        return False


def test_ui_dump(device):
    """测试UI层级导出"""
    print("=" * 50)
    print("测试4: UI层级导出")
    print("=" * 50)

    xml = device.dump_hierarchy("test_ui_dump.xml")
    if xml:
        print(f"    UI元素数量: {xml.count('<node')}")
        print("[√] 测试通过\n")
        return True
    else:
        print("[×] 测试失败\n")
        return False


def test_click(device):
    """测试点击操作"""
    print("=" * 50)
    print("测试5: 点击操作（可选）")
    print("=" * 50)

    response = input("是否测试点击操作？这会在手机屏幕上执行点击 (y/n): ")
    if response.lower() != 'y':
        print("[跳过] 用户取消\n")
        return True

    width, height = device.get_screen_size()
    print(f"    屏幕尺寸: {width} x {height}")

    # 点击屏幕中心
    center_x = width // 2
    center_y = height // 2
    print(f"    将点击屏幕中心: ({center_x}, {center_y})")

    device.click(center_x, center_y)
    print("[√] 点击已执行，请检查手机屏幕\n")
    return True


def test_damai_detection(device):
    """测试大麦APP检测"""
    print("=" * 50)
    print("测试6: 大麦APP检测")
    print("=" * 50)

    # 检查当前APP
    try:
        current_app = device.device.app_current()
        print(f"    当前应用: {current_app.get('package', 'Unknown')}")

        if current_app.get('package') == config.DAMAI_PACKAGE:
            print("[√] 大麦APP已打开")

            # 检查是否在演出详情页
            buy_buttons = ["立即购买", "选座购买", "即将开抢", "立即预约", "缺货登记"]
            found_button = None
            for btn in buy_buttons:
                if device.exists(text=btn):
                    found_button = btn
                    break

            if found_button:
                print(f"[√] 检测到按钮: {found_button}")
                print("[√] 测试通过\n")
                return True
            else:
                print("[!] 未检测到购买按钮")
                print("    请进入演出详情页后重新测试\n")
                return False
        else:
            print("[!] 大麦APP未打开")
            print(f"    大麦包名: {config.DAMAI_PACKAGE}")
            response = input("是否尝试打开大麦APP? (y/n): ")
            if response.lower() == 'y':
                if device.open_app():
                    print("[√] 大麦APP已打开\n")
                    return True
            return False

    except Exception as e:
        print(f"[×] 检测失败: {e}\n")
        return False


def main():
    """主测试函数"""
    print("\n")
    print("╔══════════════════════════════════════════════════╗")
    print("║           大麦抢票工具 - 连接测试                ║")
    print("╚══════════════════════════════════════════════════╝")
    print("\n")

    # 测试统计
    passed = 0
    failed = 0
    skipped = 0

    # 测试1: 设备连接
    device = test_connection()
    if device:
        passed += 1
    else:
        failed += 1
        print("\n[×] 设备连接失败，无法继续测试")
        print("\n请检查:")
        print("1. 手机是否通过USB连接电脑")
        print("2. 是否开启了USB调试")
        print("3. 是否在手机上授权了USB调试")
        print("4. 是否安装了ADB工具")
        print("\n提示: 可以在命令行运行 'adb devices' 检查连接状态")
        sys.exit(1)

    # 测试2: 时间同步
    if test_time_sync(device):
        passed += 1
    else:
        skipped += 1  # 时间同步失败不算致命错误

    # 测试3: 截图
    if test_screenshot(device):
        passed += 1
    else:
        failed += 1

    # 测试4: UI导出
    if test_ui_dump(device):
        passed += 1
    else:
        failed += 1

    # 测试5: 点击操作
    if test_click(device):
        passed += 1
    else:
        skipped += 1

    # 测试6: 大麦检测
    if test_damai_detection(device):
        passed += 1
    else:
        skipped += 1

    # 测试结果
    print("\n")
    print("=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    print(f"  跳过: {skipped}")

    if failed == 0:
        print("\n[√] 所有关键测试通过！可以开始使用抢票功能")
        print("\n下一步:")
        print("1. 编辑 config.py 设置抢票时间和票价")
        print("2. 打开大麦APP，进入目标演出详情页")
        print("3. 运行 python main.py 开始抢票")
    else:
        print("\n[!] 有测试未通过，请根据上面的提示排查问题")

    print("\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] 用户中断测试")
    except Exception as e:
        print(f"\n[×] 测试出错: {e}")
        import traceback
        traceback.print_exc()
