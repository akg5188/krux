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

from ...display import DEFAULT_PADDING, FONT_HEIGHT
from ...krux_settings import t, Settings, THERMAL_ADAFRUIT_TXT
from .. import (
    Page,
    Menu,
    MENU_CONTINUE,
)
from ...kboard import kboard


def amigo_text(chinese, default_text):
    """Use Chinese text on Amigo while keeping other boards unchanged."""
    if kboard.is_amigo:
        return chinese
    return default_text


STEEL_PUNCH_WEIGHTS = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
STEEL_PUNCH_WEIGHTS_DESC = tuple(reversed(STEEL_PUNCH_WEIGHTS))
STEEL_PUNCH_WORDS_PER_PAGE = 6


class MnemonicsView(Page):
    """UI to show mnemonic in different formats"""

    def mnemonic(self):
        """Menu with export mnemonic formats"""
        if kboard.is_amigo:
            qr_label = "二维码备份\n明文 / SeedQR / 加密"
            encrypted_label = "加密备份\nSD 卡 / 闪存"
            other_label = "其他格式\n助记词 / 编号 / 钢板"
        else:
            qr_label = t("QR Code")
            encrypted_label = t("Encrypted")
            other_label = t("Other Formats")

        submenu = Menu(
            self.ctx,
            [
                (qr_label, self.qr_code_backup),
                (encrypted_label, self.encrypt_mnemonic_menu),
                (other_label, self.other_backup_formats),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def qr_code_backup(self):
        """Handler for the 'QR Code Backup' menu item"""
        if kboard.is_amigo:
            plaintext_label = "明文二维码\n通用钱包可扫"
            compact_label = "紧凑 SeedQR\n更小二维码"
            seedqr_label = "助记词二维码\n标准 SeedQR"
            encrypted_label = "加密二维码\n需密码解密"
        else:
            plaintext_label = t("Plaintext QR")
            compact_label = "Compact SeedQR"
            seedqr_label = "SeedQR"
            encrypted_label = t("Encrypted QR Code")
        submenu = Menu(
            self.ctx,
            [
                (plaintext_label, self.display_standard_qr),
                (compact_label, lambda: self.display_seed_qr(True)),
                (seedqr_label, self.display_seed_qr),
                (encrypted_label, self.encrypt_qr_code),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def other_backup_formats(self):
        """Handler for the 'Other Formats' menu item"""
        if kboard.is_amigo:
            words_label = "完整助记词\n逐词查看"
            numbers_label = "助记词编号\n0-2047"
            entropy_label = "原始熵\nBIP39 熵"
            steel_label = "钢板打孔\n位权核对"
            stackbit_label = "1248 打孔板\n打孔备份"
            tinyseed_label = "点阵备份\n查看布局"
        else:
            words_label = t("Words")
            numbers_label = t("Numbers")
            entropy_label = "查看原始熵"
            steel_label = "钢板打孔数字"
            stackbit_label = "Stackbit 1248"
            tinyseed_label = "Tinyseed"
        submenu = Menu(
            self.ctx,
            [
                (
                    words_label,
                    lambda: self.show_mnemonic(
                        self.ctx.wallet.key.mnemonic,
                        amigo_text("助记词", t("Mnemonic")),
                    ),
                ),
                (numbers_label, self.display_mnemonic_numbers),
                (entropy_label, self.display_raw_entropy),
                (steel_label, self.display_steel_punch_numbers),
                (stackbit_label, self.stackbit),
                (tinyseed_label, self.tiny_seed),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def encrypt_mnemonic_menu(self):
        """Handler for Mnemonic > Encrypt Mnemonic menu item"""
        from ..encryption_ui import EncryptMnemonic

        encrypt_mnemonic_menu = EncryptMnemonic(self.ctx)
        return encrypt_mnemonic_menu.encrypt_menu()

    def encrypt_qr_code(self):
        """Handler for Encrypted QR Code menu item"""
        from ..encryption_ui import EncryptMnemonic

        encrypt_qr_code = EncryptMnemonic(self.ctx)
        return encrypt_qr_code.encrypted_qr_code()

    def show_mnemonic(self, mnemonic, suffix="", display_mnemonic=None):
        """Displays only the mnemonic words or indexes"""
        self.display_mnemonic(
            mnemonic, suffix=suffix, display_mnemonic=display_mnemonic
        )
        self.ctx.input.wait_for_button()

        # Avoid printing text on a cnc
        if Settings().hardware.printer.driver == THERMAL_ADAFRUIT_TXT:
            self.ctx.display.clear()
            if self.prompt(
                amigo_text("打印助记词?", t("Print?"))
                + "\n\n"
                + Settings().hardware.printer.driver
                + "\n\n",
                self.ctx.display.height() // 2,
            ):
                from ..print_page import PrintPage

                print_page = PrintPage(self.ctx)
                mnemonic = display_mnemonic or mnemonic
                print_page.print_mnemonic_text(mnemonic, suffix)
        return MENU_CONTINUE

    def display_mnemonic_numbers(self):
        """Handler for the 'numbers' menu item"""
        from ..utils import Utils
        from .. import BASE_DEC_SUFFIX, BASE_HEX_SUFFIX, BASE_OCT_SUFFIX

        if kboard.is_amigo:
            decimal_label = "十进制编号\n0-2047"
            hex_label = "十六进制编号\n0-7FF"
            octal_label = "八进制编号\n0-3777"
        else:
            decimal_label = t("Decimal")
            hex_label = t("Hexadecimal")
            octal_label = t("Octal")
        submenu = Menu(
            self.ctx,
            [
                (
                    decimal_label,
                    lambda: self.show_mnemonic(
                        self.ctx.wallet.key.mnemonic,
                        BASE_DEC_SUFFIX,
                        Utils.get_mnemonic_numbers(
                            self.ctx.wallet.key.mnemonic, Utils.BASE_DEC
                        ),
                    ),
                ),
                (
                    hex_label,
                    lambda: self.show_mnemonic(
                        self.ctx.wallet.key.mnemonic,
                        BASE_HEX_SUFFIX,
                        Utils.get_mnemonic_numbers(
                            self.ctx.wallet.key.mnemonic, Utils.BASE_HEX
                        ),
                    ),
                ),
                (
                    octal_label,
                    lambda: self.show_mnemonic(
                        self.ctx.wallet.key.mnemonic,
                        BASE_OCT_SUFFIX,
                        Utils.get_mnemonic_numbers(
                            self.ctx.wallet.key.mnemonic, Utils.BASE_OCT
                        ),
                    ),
                ),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    @staticmethod
    def _format_entropy_bytes(entropy):
        return " ".join("%02X" % byte for byte in entropy)

    def display_raw_entropy(self):
        """Display the original BIP39 entropy bytes as HEX."""
        from embit import bip39

        try:
            entropy = bip39.mnemonic_to_bytes(self.ctx.wallet.key.mnemonic)
        except Exception:
            self.flash_error("这组助记词无法显示原始熵")
            return MENU_CONTINUE

        self.display_mnemonic(
            self._format_entropy_bytes(entropy),
            title="原始熵",
            suffix="BIP39 熵: %d 位" % (len(entropy) * 8),
        )
        self.ctx.input.wait_for_button()
        return MENU_CONTINUE

    @staticmethod
    def _steel_punch_weights(index):
        """Return the 0-based BIP39 steel punch weights for a word index."""
        if index < 0 or index >= 2048:
            raise ValueError("BIP39 序号必须在 0 到 2047 之间")

        remaining = index
        weights = []
        for weight in STEEL_PUNCH_WEIGHTS_DESC:
            if remaining >= weight:
                weights.append(weight)
                remaining -= weight
        return sorted(weights)

    @staticmethod
    def _format_steel_punch_weight_lines(weights):
        if not weights:
            return ["打孔: 无需打孔"]

        selected = set(weights)
        first_half = [
            weight for weight in STEEL_PUNCH_WEIGHTS[:6] if weight in selected
        ]
        second_half = [
            weight for weight in STEEL_PUNCH_WEIGHTS[6:] if weight in selected
        ]
        return [
            "前 6 位: " + (" ".join(str(weight) for weight in first_half) or "无"),
            "后 5 位: " + (" ".join(str(weight) for weight in second_half) or "无"),
        ]

    @classmethod
    def _format_steel_punch_pages(cls, mnemonic):
        """Build large-screen pages for the titanium/steel punch backup flow."""
        from embit.wordlists.bip39 import WORDLIST

        words = mnemonic.split(" ")
        pages = []
        for page_start in range(0, len(words), STEEL_PUNCH_WORDS_PER_PAGE):
            lines = []
            page_words = words[page_start : page_start + STEEL_PUNCH_WORDS_PER_PAGE]
            for offset, word in enumerate(page_words):
                position = page_start + offset + 1
                word_index = WORDLIST.index(word)
                lines.append("%02d %s #%04d" % (position, word, word_index))
                lines.extend(
                    cls._format_steel_punch_weight_lines(
                        cls._steel_punch_weights(word_index)
                    )
                )
            pages.append(lines)
        return pages

    def display_steel_punch_numbers(self):
        """Display 0-based BIP39 indices and punch weights for steel plates."""
        try:
            pages = self._format_steel_punch_pages(self.ctx.wallet.key.mnemonic)
        except Exception:
            self.flash_error("这组助记词无法显示钢板打孔数字")
            return MENU_CONTINUE

        for page_index, lines in enumerate(pages):
            self.ctx.display.clear()
            self.ctx.display.draw_hcentered_text(
                "钢板打孔数字 %d/%d" % (page_index + 1, len(pages))
            )
            y_offset = 2 * FONT_HEIGHT
            for line in lines:
                self.ctx.display.draw_string(DEFAULT_PADDING, y_offset, line)
                y_offset += FONT_HEIGHT
            self.ctx.input.wait_for_button()
        return MENU_CONTINUE

    def display_standard_qr(self):
        """Displays regular words QR code"""
        title = amigo_text("明文二维码", t("Plaintext QR"))
        data = self.ctx.wallet.key.mnemonic
        self.display_qr_codes(data, title=title)

        from ..utils import Utils

        utils = Utils(self.ctx)
        utils.print_standard_qr(data, title=title)
        return MENU_CONTINUE

    def display_seed_qr(self, binary=False):
        """Display Seed QR with with different view modes"""

        from ..qr_view import SeedQRView

        seed_qr_view = SeedQRView(self.ctx, binary)
        return seed_qr_view.display_qr()

    def stackbit(self):
        """Displays which numbers 1248 user should punch on 1248 steel card"""
        from ..stack_1248 import Stackbit

        stackbit = Stackbit(self.ctx)
        word_index = 1
        words = self.ctx.wallet.key.mnemonic.split(" ")

        while word_index < len(words):
            y_offset = 2 * FONT_HEIGHT
            for _ in range(6):
                stackbit.export_1248(word_index, y_offset, words[word_index - 1])
                if not kboard.has_minimal_display:
                    y_offset += 3 * FONT_HEIGHT
                else:
                    y_offset += 5 + 2 * FONT_HEIGHT
                word_index += 1
            self.ctx.input.wait_for_button()
            self.ctx.display.clear()
        return MENU_CONTINUE

    def tiny_seed(self):
        """Displays the seed in Tinyseed format"""
        from ..tiny_seed import TinySeed

        tiny_seed = TinySeed(self.ctx)
        tiny_seed.export()

        # Allow to print on thermal printer only
        if (
            Settings().hardware.printer.driver == THERMAL_ADAFRUIT_TXT
            and self.ctx.camera.mode is not None
        ):
            # TinySeed printing requires a camera frame buffer to draw in.
            if self.print_prompt(t("Print Tinyseed?")):
                tiny_seed.print_tiny_seed()
        return MENU_CONTINUE
