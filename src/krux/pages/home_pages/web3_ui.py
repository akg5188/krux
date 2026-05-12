# The MIT License (MIT)
#
# Copyright (c) 2021-2024 Krux contributors
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

from .. import ESC_KEY, MENU_CONTINUE, MENU_SHUTDOWN, Menu, Page
from ..qr_capture import QRCodeCapture
from ...display import BOTTOM_PROMPT_LINE, DEFAULT_PADDING, FONT_HEIGHT
from ...themes import theme
from ...web3 import (
    Web3Error,
    Web3RequestDataType,
    WEB3_WALLET_PROFILE_BITGET,
    WEB3_WALLET_PROFILE_LABELS,
    WEB3_WALLET_PROFILE_METAMASK,
    WEB3_WALLET_PROFILE_OKX,
    WEB3_WALLET_PROFILE_RABBY,
    WEB3_WALLET_PROFILE_TOKENPOCKET,
    build_connect_qr_bundle,
    build_connect_summary,
    build_request_summary,
    parse_scanned_web3_request,
    sign_web3_request,
    derive_web3_account,
)
from ...qr import FORMAT_NONE, FORMAT_UR
from ..wallet_settings import DERIVATION_KEYPAD


class Web3(Page):
    """Web3 / TP user interface"""

    def __init__(self, ctx):
        super().__init__(ctx, None)
        self.ctx = ctx

    def web3(self):
        """Handler for the top-level Web3 menu item"""
        submenu_items = [
            ("连接钱包\nOKX Bitget MetaMask", self.connect_wallet),
            ("扫码签名\n消息 交易 TP中转", self.scan_and_sign),
        ]
        submenu = Menu(self.ctx, submenu_items)
        submenu.run_loop()
        return MENU_CONTINUE

    def _wallet_key(self):
        wallet = getattr(self.ctx, "wallet", None)
        if wallet is None or wallet.key is None:
            return None
        return wallet.key

    def _verify_sign_pin(self):
        """Verify the configured Amigo PIN before signing."""
        from ..boot_lock import BootLockPage

        return BootLockPage(self.ctx).verify_before_signing()

    def _display_bundle(self, bundle, title):
        if bundle.pages:
            self.display_qr_codes(bundle.pages, FORMAT_NONE, title)
            return
        if bundle.ur is not None:
            self.display_qr_codes(bundle.ur, FORMAT_UR, title)
            return
        self.display_qr_codes(bundle.text or "", FORMAT_NONE, title)

    def _prompt_sign_request(self, preview):
        """Show a compact preview without letting long data cover the buttons."""
        prompt_y = BOTTOM_PROMPT_LINE
        max_preview_lines = max(3, (prompt_y // FONT_HEIGHT) - 2)
        preview_lines = self.ctx.display.to_lines(preview, max_preview_lines)

        self.ctx.display.clear()
        self.ctx.display.draw_hcentered_text(
            preview_lines,
            DEFAULT_PADDING,
            max_lines=max_preview_lines,
        )
        self.ctx.display.draw_hcentered_text(
            "内容已省略" if len(preview_lines) >= max_preview_lines else "",
            max(prompt_y - FONT_HEIGHT, DEFAULT_PADDING),
            theme.frame_color,
            max_lines=1,
        )
        return self.prompt("签名此请求?", prompt_y)

    def connect_wallet(self):
        """Show profile-specific Web3 connection QRs"""
        submenu = Menu(
            self.ctx,
            [
                ("OKX 钱包", lambda: self._connect_wallet_profile(WEB3_WALLET_PROFILE_OKX)),
                (
                    "Bitget 钱包",
                    lambda: self._connect_wallet_profile(WEB3_WALLET_PROFILE_BITGET),
                ),
                (
                    "MetaMask",
                    lambda: self._connect_wallet_profile(
                        WEB3_WALLET_PROFILE_METAMASK
                    ),
                ),
                (
                    "Rabby",
                    lambda: self._connect_wallet_profile(WEB3_WALLET_PROFILE_RABBY),
                ),
                (
                    "TokenPocket",
                    lambda: self._connect_wallet_profile(
                        WEB3_WALLET_PROFILE_TOKENPOCKET
                    ),
                ),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def _connect_wallet_profile(self, wallet_profile):
        wallet_key = self._wallet_key()
        if wallet_key is None:
            self.flash_error("请先加载助记词")
            return MENU_CONTINUE

        try:
            account = derive_web3_account(wallet_key)
            bundle = build_connect_qr_bundle(wallet_key, wallet_profile=wallet_profile)
        except (Web3Error, ValueError) as exc:
            self.ctx.display.to_portrait()
            self.flash_error(str(exc))
            return MENU_CONTINUE

        wallet_title = WEB3_WALLET_PROFILE_LABELS.get(wallet_profile, "链上钱包")
        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(build_connect_summary(account, wallet_profile))
        if not self.prompt("显示连接二维码?", BOTTOM_PROMPT_LINE):
            return MENU_CONTINUE

        self._display_bundle(bundle, wallet_title)
        return MENU_CONTINUE

    def scan_and_sign(self):
        """Scan a Web3 request and sign it"""
        wallet_key = self._wallet_key()
        if wallet_key is None:
            self.flash_error("请先加载助记词")
            return MENU_CONTINUE

        qr_capture = QRCodeCapture(self.ctx)
        try:
            payload, qr_format = qr_capture.qr_capture_loop()
            if payload is None:
                return MENU_CONTINUE
            request = parse_scanned_web3_request(payload, qr_format)
        except Web3Error as exc:
            self.flash_error(str(exc))
            return MENU_CONTINUE

        preview = build_request_summary(request)
        if request.message_text:
            preview += "\n" + self.fit_to_line(request.message_text, "消息: ")
        elif request.typed_data_json:
            preview += "\n" + self.fit_to_line(request.typed_data_json, "结构化数据: ")

        if not self._prompt_sign_request(preview):
            return MENU_CONTINUE

        pin_result = self._verify_sign_pin()
        if pin_result == MENU_SHUTDOWN:
            return MENU_SHUTDOWN
        if not pin_result:
            return MENU_CONTINUE

        try:
            result = sign_web3_request(wallet_key, request)
        except Web3Error as exc:
            self.flash_error(str(exc))
            return MENU_CONTINUE

        title = "签名结果"
        if request.data_type == Web3RequestDataType.PERSONAL_MESSAGE:
            title = "消息签名结果"
        elif request.data_type == Web3RequestDataType.TYPED_DATA:
            title = "结构化数据签名结果"
        elif request.data_type == Web3RequestDataType.TRANSACTION:
            title = "交易签名结果"
        elif request.data_type == Web3RequestDataType.TYPED_TRANSACTION:
            title = "结构化交易签名结果"

        self._display_bundle(result.qr_bundle, title)
        return MENU_CONTINUE

    def _is_valid_derivation_path(self, derivation_path):
        parts = derivation_path.split("/")
        if parts[0] != "m":
            return False
        return all(
            p and ((p[-1] in "'hH" and p[:-1].isdigit()) or p.isdigit())
            for p in parts[1:]
        )

    def _capture_derivation_path(self, title, default_value):
        value = self.capture_from_keypad(
            title,
            [DERIVATION_KEYPAD],
            starting_buffer=default_value,
        )
        if value == ESC_KEY:
            return None
        value = str(value or "").strip()
        if not value:
            return default_value
        if not self._is_valid_derivation_path(value):
            self.flash_error("派生路径无效")
            return None
        return value
