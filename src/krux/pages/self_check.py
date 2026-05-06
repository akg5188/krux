# The MIT License (MIT)
#
# Copyright (c) 2021-2026 Krux contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import board

from . import MENU_CONTINUE, Menu, Page
from ..display import BOTTOM_PROMPT_LINE
from ..kboard import kboard
from ..metadata import VERSION


class SelfCheck(Page):
    """Chinese self-check menu for the Amigo firmware."""

    def __init__(self, ctx):
        menu_items = [
            (self._menu_label("状态总览", "版本 / 屏幕 / 功能"), self.status_overview),
            (self._menu_label("SD 卡检查", "检测存储卡"), self.sd_check),
            (self._menu_label("测试套件", "逐项检查设备"), self.test_suite),
        ]
        if kboard.has_touchscreen:
            menu_items.append(
                (self._menu_label("触摸测试", "检查大屏触摸"), self.touch_test)
            )
        super().__init__(ctx, Menu(ctx, menu_items))

    def self_check(self):
        """Run the self-check menu."""
        self.menu.run_loop()
        return MENU_CONTINUE

    def status_overview(self):
        """Show firmware, device, screen, and enabled feature summary."""
        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(
            "\n".join(
                [
                    "固件自检",
                    "设备:" + self._device_name(),
                    "版本:" + VERSION,
                    "屏幕:" + self._screen_summary(),
                    "触摸:" + ("已启用" if kboard.has_touchscreen else "未启用"),
                    "扫码:相机二维码",
                    "链上:已启用",
                    "签名:本机助记词",
                ]
            ),
            highlight_prefix=":",
        )
        self.prompt("返回菜单?", BOTTOM_PROMPT_LINE)
        return MENU_CONTINUE

    def sd_check(self):
        """Reuse Krux's SD card test from Device Tests."""
        from .device_tests import DeviceTests

        return DeviceTests(self.ctx).sd_check()

    def test_suite(self):
        """Reuse Krux's built-in device test suite."""
        from .device_tests import DeviceTests

        return DeviceTests(self.ctx).test_suite()

    def touch_test(self):
        """Reuse Krux's touch-screen test."""
        from .device_tests import DeviceTests

        return DeviceTests(self.ctx).test_touch()

    def _menu_label(self, title, subtitle):
        if kboard.is_amigo:
            return title + "\n" + subtitle
        return title

    def _device_name(self):
        if board.config.get("type") == "amigo":
            return "Sipeed Matrix Amigo"
        return str(board.config.get("type", "未知设备"))

    def _screen_summary(self):
        lcd_config = board.config.get("lcd", {})
        width = lcd_config.get("width", "?")
        height = lcd_config.get("height", "?")
        if board.config.get("type") == "amigo":
            return "3.5 寸触摸屏 %sx%s" % (width, height)
        return "%sx%s" % (width, height)
