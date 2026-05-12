# The MIT License (MIT)

# Copyright (c) 2021-2024 Krux contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from . import (
    Page,
    Menu,
    MENU_CONTINUE,
    MENU_EXIT,
    ESC_KEY,
    LETTERS,
    UPPERCASE_LETTERS,
    NUM_SPECIAL_1,
    NUM_SPECIAL_2,
)
from ..krux_settings import t
from ..kboard import kboard


def amigo_text(chinese, default_text):
    """Use Chinese text on Amigo while keeping other boards unchanged."""
    if kboard.is_amigo:
        return chinese
    return default_text


class Tools(Page):
    """Krux generic tools"""

    def __init__(self, ctx):
        if kboard.is_amigo:
            datum_label = "数据工具\nPSBT xpub 地址"
            test_label = "设备测试\n触摸 SD 打印"
            qr_label = "生成二维码\n从文本创建"
            descriptor_label = "地址工具\n描述符和地址"
            flash_label = "闪存工具\n清理和维护"
            remove_label = "删除助记词\n管理已保存项"
        else:
            datum_label = t("Datum Tool")
            test_label = t("Device Tests")
            qr_label = t("Create QR Code")
            descriptor_label = t("Descriptor Addresses")
            flash_label = t("Flash Tools")
            remove_label = t("Remove Mnemonic")

        super().__init__(
            ctx,
            Menu(
                ctx,
                [
                    (datum_label, self.datum_tool),
                    (test_label, self.device_tests),
                    (qr_label, self.create_qr),
                    (descriptor_label, self.descriptor_addresses),
                    (flash_label, self.flash_tools),
                    (remove_label, self.rm_stored_mnemonic),
                ],
            ),
        )
        self.ctx = ctx

    def flash_tools(self):
        """Handler for the 'Flash Tools' menu item"""

        from .flash_tools import FlashTools

        flash_tools = FlashTools(self.ctx)
        flash_tools.flash_tools_menu()
        return MENU_CONTINUE

    def rm_stored_mnemonic(self):
        """Lists and allow deletion of stored mnemonics"""
        from .encryption_ui import LoadEncryptedMnemonic

        encrypted_mnemonics = LoadEncryptedMnemonic(self.ctx)
        while True:
            ret = encrypted_mnemonics.load_from_storage(remove_opt=True)
            if ret == MENU_CONTINUE:
                del encrypted_mnemonics
                return ret

    def datum_tool(self):
        """Handler for the 'Datum Tool' menu item"""
        import sys
        from .datum_tool import DatumToolMenu

        while True:
            if DatumToolMenu(self.ctx).run() == MENU_EXIT:
                break

        sys.modules.pop("krux.pages.datum_tool")
        del sys.modules["krux.pages"].datum_tool
        return MENU_CONTINUE

    def create_qr(self):
        """Handler for the 'Create QR Code' menu item"""
        if self.prompt(
            amigo_text("从文本生成二维码?", t("Create QR code from text?")),
            self.ctx.display.height() // 2,
        ):
            text = self.capture_from_keypad(
                amigo_text("输入文本", t("Text")),
                [LETTERS, UPPERCASE_LETTERS, NUM_SPECIAL_1, NUM_SPECIAL_2],
            )
            if text in ("", ESC_KEY):
                return MENU_CONTINUE

            from .qr_view import SeedQRView

            title = amigo_text("自定义二维码", t("Custom QR Code"))
            seed_qr_view = SeedQRView(self.ctx, data=text, title=title)
            return seed_qr_view.display_qr(allow_export=True)
        return MENU_CONTINUE

    def descriptor_addresses(self):
        """Handler for the 'Descriptor Addresses' menu item"""
        from .home_pages.wallet_descriptor import WalletDescriptor
        from .home_pages.addresses import Addresses
        from ..wallet import Wallet

        self.ctx.wallet = Wallet(None)
        menu_result = WalletDescriptor(self.ctx).wallet()
        if self.ctx.wallet.is_loaded():
            menu_result = Addresses(self.ctx).addresses_menu()
        return menu_result

    def device_tests(self):
        """Handler for the 'Device Tests' menu item"""
        import sys
        from .device_tests import DeviceTests

        page = DeviceTests(self.ctx)
        page.run()
        sys.modules.pop("krux.pages.device_tests")
        del sys.modules["krux.pages"].device_tests
        return MENU_CONTINUE
