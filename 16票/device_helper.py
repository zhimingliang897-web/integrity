# -*- coding: utf-8 -*-
"""
设备连接和操作工具
"""

import os
import time
import ntplib
from datetime import datetime
from pathlib import Path

import uiautomator2 as u2

import config


class DeviceHelper:
    """设备操作辅助类"""

    def __init__(self):
        self.device = None
        self.device_info = None
        self.time_offset = 0  # 本地时间与服务器时间的偏差

    def connect(self, serial=None):
        """
        连接设备

        Args:
            serial: 设备序列号，如果为None则自动连接第一个设备

        Returns:
            bool: 连接是否成功
        """
        try:
            if serial:
                self.device = u2.connect(serial)
            else:
                self.device = u2.connect()

            # 获取设备信息
            self.device_info = self.device.info
            print(f"[√] 设备连接成功")
            print(f"    设备型号: {self.device.device_info.get('model', 'Unknown')}")
            print(f"    屏幕尺寸: {self.device_info['displayWidth']} x {self.device_info['displayHeight']}")
            return True

        except Exception as e:
            print(f"[×] 设备连接失败: {e}")
            print("    请检查:")
            print("    1. 手机是否通过USB连接电脑")
            print("    2. 是否开启了USB调试")
            print("    3. 是否授权了USB调试")
            return False

    def sync_time(self):
        """
        同步网络时间，计算本地时间偏差

        Returns:
            float: 时间偏差（秒）
        """
        try:
            ntp_client = ntplib.NTPClient()
            # 使用多个NTP服务器，提高成功率
            ntp_servers = [
                'ntp.aliyun.com',
                'time.windows.com',
                'pool.ntp.org'
            ]

            for server in ntp_servers:
                try:
                    response = ntp_client.request(server, timeout=5)
                    self.time_offset = response.offset
                    print(f"[√] 时间同步成功 (服务器: {server})")
                    print(f"    本地时间偏差: {self.time_offset*1000:.1f} 毫秒")
                    return self.time_offset
                except:
                    continue

            print("[!] 无法同步网络时间，将使用本地时间")
            self.time_offset = 0
            return 0

        except Exception as e:
            print(f"[!] 时间同步失败: {e}")
            self.time_offset = 0
            return 0

    def get_accurate_time(self):
        """
        获取校准后的当前时间戳

        Returns:
            float: 校准后的Unix时间戳
        """
        return time.time() + self.time_offset

    def wait_until(self, target_time_str, callback=None):
        """
        等待直到目标时间

        Args:
            target_time_str: 目标时间字符串，格式 "YYYY-MM-DD HH:MM:SS"
            callback: 每秒回调函数，接收剩余秒数作为参数

        Returns:
            bool: 是否成功等待到目标时间
        """
        try:
            target_dt = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
            target_ts = target_dt.timestamp()

            # 提前准备时间（毫秒转秒）
            prepare_seconds = config.PREPARE_MS / 1000

            while True:
                current_ts = self.get_accurate_time()
                remaining = target_ts - current_ts

                if remaining <= 0:
                    return True

                if callback:
                    callback(remaining)

                # 根据剩余时间调整等待精度
                if remaining > 60:
                    time.sleep(1)
                elif remaining > 10:
                    time.sleep(0.1)
                elif remaining > prepare_seconds:
                    time.sleep(0.01)
                else:
                    # 最后阶段，高精度等待
                    time.sleep(0.001)

        except Exception as e:
            print(f"[×] 等待时间出错: {e}")
            return False

    def screenshot(self, filename=None):
        """
        截图

        Args:
            filename: 保存的文件名，如果为None则自动生成

        Returns:
            str: 截图文件路径
        """
        if not self.device:
            print("[×] 设备未连接")
            return None

        try:
            # 确保截图目录存在
            screenshot_dir = Path(config.SCREENSHOT_DIR)
            screenshot_dir.mkdir(exist_ok=True)

            if filename is None:
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            filepath = screenshot_dir / filename
            self.device.screenshot(str(filepath))
            print(f"[√] 截图已保存: {filepath}")
            return str(filepath)

        except Exception as e:
            print(f"[×] 截图失败: {e}")
            return None

    def click(self, x, y):
        """点击指定坐标"""
        if self.device:
            self.device.click(x, y)

    def click_text(self, text, timeout=5):
        """
        点击包含指定文字的元素

        Args:
            text: 要点击的文字
            timeout: 等待超时时间（秒）

        Returns:
            bool: 是否点击成功
        """
        if not self.device:
            return False

        try:
            element = self.device(text=text)
            if element.wait(timeout=timeout):
                element.click()
                return True
            return False
        except:
            return False

    def click_text_contains(self, text, timeout=5):
        """
        点击包含指定文字的元素（模糊匹配）

        Args:
            text: 要匹配的文字
            timeout: 等待超时时间（秒）

        Returns:
            bool: 是否点击成功
        """
        if not self.device:
            return False

        try:
            element = self.device(textContains=text)
            if element.wait(timeout=timeout):
                element.click()
                return True
            return False
        except:
            return False

    def exists(self, text=None, resource_id=None):
        """
        检查元素是否存在

        Args:
            text: 元素文字
            resource_id: 元素ID

        Returns:
            bool: 元素是否存在
        """
        if not self.device:
            return False

        try:
            if text:
                return self.device(text=text).exists(timeout=1)
            elif resource_id:
                return self.device(resourceId=resource_id).exists(timeout=1)
            return False
        except:
            return False

    def swipe_down(self):
        """下滑刷新页面"""
        if self.device:
            self.device.swipe(0.5, 0.3, 0.5, 0.7, duration=0.2)

    def swipe_up(self):
        """上滑页面"""
        if self.device:
            self.device.swipe(0.5, 0.7, 0.5, 0.3, duration=0.2)

    def open_app(self, package_name=None):
        """
        打开应用

        Args:
            package_name: 应用包名，默认为大麦
        """
        if not self.device:
            return False

        package = package_name or config.DAMAI_PACKAGE
        try:
            self.device.app_start(package)
            print(f"[√] 已打开应用: {package}")
            time.sleep(2)  # 等待应用启动
            return True
        except Exception as e:
            print(f"[×] 打开应用失败: {e}")
            return False

    def get_screen_size(self):
        """
        获取屏幕尺寸

        Returns:
            tuple: (宽, 高)
        """
        if self.device_info:
            return (self.device_info['displayWidth'],
                    self.device_info['displayHeight'])
        return (0, 0)

    def dump_hierarchy(self, filename=None):
        """
        导出当前页面的UI层级结构（用于调试）

        Args:
            filename: 保存的文件名

        Returns:
            str: XML内容
        """
        if not self.device:
            return None

        try:
            xml = self.device.dump_hierarchy()

            if filename:
                screenshot_dir = Path(config.SCREENSHOT_DIR)
                screenshot_dir.mkdir(exist_ok=True)
                filepath = screenshot_dir / filename
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(xml)
                print(f"[√] UI结构已保存: {filepath}")

            return xml
        except Exception as e:
            print(f"[×] 导出UI结构失败: {e}")
            return None
