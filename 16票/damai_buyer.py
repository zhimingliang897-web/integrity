# -*- coding: utf-8 -*-
"""
大麦抢票核心逻辑
"""

import time
from datetime import datetime

import config
from device_helper import DeviceHelper


class DamaiBuyer:
    """大麦抢票类"""

    def __init__(self, device_helper: DeviceHelper):
        self.device = device_helper
        self.d = device_helper.device  # uiautomator2 device对象

    def _save_screenshot(self, step_name):
        """保存调试截图"""
        if config.SAVE_SCREENSHOTS:
            filename = f"{datetime.now().strftime('%H%M%S')}_{step_name}.png"
            self.device.screenshot(filename)

    def _click_with_retry(self, text, max_retry=3, interval=0.1):
        """
        带重试的点击操作

        Args:
            text: 要点击的文字
            max_retry: 最大重试次数
            interval: 重试间隔（秒）

        Returns:
            bool: 是否点击成功
        """
        for i in range(max_retry):
            if self.device.click_text(text, timeout=1):
                return True
            time.sleep(interval)
        return False

    def _click_contains_with_retry(self, text, max_retry=3, interval=0.1):
        """带重试的模糊匹配点击"""
        for i in range(max_retry):
            if self.device.click_text_contains(text, timeout=1):
                return True
            time.sleep(interval)
        return False

    def check_page_ready(self):
        """
        检查是否在演出详情页

        Returns:
            bool: 是否准备就绪
        """
        # 检查是否有购买相关按钮
        buy_keywords = ["立即购买", "选座购买", "即将开抢", "立即预约", "缺货登记"]
        for keyword in buy_keywords:
            if self.device.exists(text=keyword):
                print(f"[√] 检测到按钮: {keyword}")
                return True

        print("[!] 未检测到购买按钮，请确保停留在演出详情页")
        return False

    def wait_for_buy_button(self):
        """
        等待购买按钮可点击

        Returns:
            bool: 按钮是否可点击
        """
        print("[*] 等待购买按钮...")

        for i in range(config.MAX_RETRY):
            # 检查各种可能的购买按钮
            if self.device.exists(text="立即购买"):
                return "立即购买"
            if self.device.exists(text="选座购买"):
                return "选座购买"
            if self.device.exists(text="立即预订"):
                return "立即预订"

            # 如果是即将开抢状态，快速刷新
            if self.device.exists(text="即将开抢"):
                self.device.swipe_down()
                time.sleep(config.CLICK_INTERVAL / 1000)
                continue

            time.sleep(config.CLICK_INTERVAL / 1000)

        return None

    def click_buy_button(self):
        """
        点击购买按钮

        Returns:
            bool: 是否点击成功
        """
        print("[*] 尝试点击购买按钮...")
        self._save_screenshot("01_before_buy")

        # 按优先级尝试点击不同的购买按钮
        buy_buttons = ["立即购买", "选座购买", "立即预订"]

        for button_text in buy_buttons:
            if self._click_with_retry(button_text):
                print(f"[√] 点击成功: {button_text}")
                time.sleep(0.3)
                self._save_screenshot("02_after_buy_click")
                return True

        print("[×] 未找到购买按钮")
        return False

    def select_ticket_info(self):
        """
        选择场次、票价、数量

        Returns:
            bool: 是否选择成功
        """
        print("[*] 选择票务信息...")
        time.sleep(0.5)  # 等待弹窗加载

        # 选择场次（如果有多场）
        if config.SESSION_PRIORITY:
            for session in config.SESSION_PRIORITY:
                if self._click_contains_with_retry(session):
                    print(f"[√] 选择场次: {session}")
                    time.sleep(0.2)
                    break

        # 选择票价
        for price in config.PRICE_PRIORITY:
            if self._click_contains_with_retry(price):
                print(f"[√] 选择票价: {price}")
                time.sleep(0.2)
                self._save_screenshot("03_select_price")
                break

        # 调整购票数量
        # 大麦默认是1张，如果需要多张，点击加号
        if config.TICKET_COUNT > 1:
            for _ in range(config.TICKET_COUNT - 1):
                # 尝试点击加号按钮
                if self.d(resourceId="cn.damai:id/img_jia").exists:
                    self.d(resourceId="cn.damai:id/img_jia").click()
                elif self.device.exists(text="+"):
                    self.device.click_text("+")
                time.sleep(0.1)

        return True

    def select_viewers(self):
        """
        选择实名观演人

        Returns:
            bool: 是否选择成功
        """
        print("[*] 选择观演人...")
        time.sleep(0.3)

        # 检查是否需要选择观演人
        if not config.VIEWER_NAMES:
            print("[!] 未配置观演人，跳过")
            return True

        # 点击选择观演人区域（如果需要）
        if self.device.exists(text="选择观演人"):
            self.device.click_text("选择观演人")
            time.sleep(0.3)

        # 选择配置的观演人
        for viewer_name in config.VIEWER_NAMES:
            if self._click_contains_with_retry(viewer_name):
                print(f"[√] 选择观演人: {viewer_name}")
                time.sleep(0.1)

        self._save_screenshot("04_select_viewer")
        return True

    def confirm_order(self):
        """
        确认订单

        Returns:
            bool: 是否确认成功
        """
        print("[*] 确认订单...")

        # 点击确定/确认按钮
        confirm_buttons = ["确定", "确认", "立即下单", "提交订单", "立即支付"]

        for button_text in confirm_buttons:
            if self._click_with_retry(button_text):
                print(f"[√] 点击: {button_text}")
                time.sleep(0.3)
                self._save_screenshot("05_confirm_order")

                # 可能还有二次确认
                for button_text2 in confirm_buttons:
                    if self.device.exists(text=button_text2):
                        self.device.click_text(button_text2)
                        time.sleep(0.2)

                return True

        return False

    def submit_order(self):
        """
        提交订单（最后一步）

        Returns:
            bool: 是否提交成功
        """
        print("[*] 提交订单...")

        submit_buttons = ["立即支付", "提交订单", "确认订单", "去支付"]

        for i in range(5):  # 多次尝试
            for button_text in submit_buttons:
                if self._click_with_retry(button_text, max_retry=1):
                    print(f"[√] 点击: {button_text}")
                    self._save_screenshot("06_submit_order")
                    return True
            time.sleep(0.2)

        return False

    def run(self):
        """
        执行完整的抢票流程

        Returns:
            bool: 是否抢票成功
        """
        print("\n" + "=" * 50)
        print("开始抢票流程")
        print("=" * 50)

        try:
            # 步骤1: 点击购买按钮
            if not self.click_buy_button():
                # 如果失败，快速重试
                for _ in range(config.MAX_RETRY):
                    self.device.swipe_down()
                    time.sleep(0.05)
                    if self.click_buy_button():
                        break
                else:
                    print("[×] 无法点击购买按钮")
                    return False

            # 步骤2: 选择票务信息
            self.select_ticket_info()

            # 步骤3: 选择观演人
            self.select_viewers()

            # 步骤4: 确认订单
            self.confirm_order()

            # 步骤5: 提交订单
            if self.submit_order():
                print("\n" + "=" * 50)
                print("[√] 抢票流程完成！请在手机上完成支付")
                print("=" * 50)
                self._save_screenshot("07_final")
                return True
            else:
                print("[!] 提交订单步骤可能未完成，请检查手机")
                return False

        except Exception as e:
            print(f"[×] 抢票过程出错: {e}")
            self._save_screenshot("error")
            return False

    def quick_buy(self):
        """
        极速抢票模式 - 简化流程，追求速度

        Returns:
            bool: 是否成功
        """
        print("[*] 极速模式启动...")

        for attempt in range(config.MAX_RETRY):
            try:
                # 快速点击购买
                if self.d(text="立即购买").exists(timeout=0.1):
                    self.d(text="立即购买").click()
                elif self.d(text="选座购买").exists(timeout=0.1):
                    self.d(text="选座购买").click()
                else:
                    # 刷新页面
                    self.device.swipe_down()
                    continue

                time.sleep(0.1)

                # 快速选择票价（点击第一个可用的）
                for price in config.PRICE_PRIORITY:
                    if self.d(textContains=price).exists(timeout=0.1):
                        self.d(textContains=price).click()
                        break

                time.sleep(0.1)

                # 快速确认
                for btn in ["确定", "确认", "立即下单", "提交订单"]:
                    if self.d(text=btn).exists(timeout=0.1):
                        self.d(text=btn).click()

                time.sleep(0.1)

                # 提交
                for btn in ["立即支付", "提交订单", "去支付"]:
                    if self.d(text=btn).exists(timeout=0.1):
                        self.d(text=btn).click()
                        print(f"[√] 极速模式完成 (尝试 {attempt + 1})")
                        return True

            except Exception as e:
                print(f"[!] 尝试 {attempt + 1} 失败: {e}")
                continue

        return False
