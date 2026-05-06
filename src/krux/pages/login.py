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

import sys
from hashlib import sha256
from embit.networks import NETWORKS
from . import (
    Menu,
    MENU_CONTINUE,
    MENU_EXIT,
    LETTERS,
    ESC_KEY,
    EXTRA_MNEMONIC_LENGTH_FLAG,
)
from .mnemonic_loader import MnemonicLoader
from ..display import DEFAULT_PADDING, FONT_HEIGHT, BOTTOM_PROMPT_LINE
from ..settings import ELLIPSIS
from ..krux_settings import Settings
from ..key import (
    Key,
    P2WPKH,
    P2WSH,
    P2SH,
    SINGLESIG_SCRIPT_MAP,
    MULTISIG_SCRIPT_MAP,
    MINISCRIPT_SCRIPT_MAP,
    TYPE_SINGLESIG,
    TYPE_MULTISIG,
    TYPE_MINISCRIPT,
    POLICY_TYPE_IDS,
    NAME_MULTISIG,
)
from ..krux_settings import t
from ..kboard import kboard

DOUBLE_MNEMONICS_MAX_TRIES = 200
MASK256 = (1 << 256) - 1
MASK128 = (1 << 128) - 1
HEX_ENTROPY_DIGITS = "0123456789ABCDEF"
HEX_ENTROPY_BYTES_BY_WORDS = {
    12: 16,
    15: 20,
    18: 24,
    21: 28,
    24: 32,
}
CARD_RANKS = "A23456789TJQK"
CARD_SUITS = "CDHS"
CARD_SUIT_HASH_SYMBOLS = {
    "C": "\u2663",
    "D": "\u2666",
    "H": "\u2665",
    "S": "\u2660",
}
CARD_EVENT_BITS = {
    "AC": "00000",
    "2C": "00001",
    "3C": "00010",
    "4C": "00011",
    "5C": "00100",
    "6C": "00101",
    "7C": "00110",
    "8C": "00111",
    "9C": "01000",
    "TC": "01001",
    "JC": "01010",
    "QC": "01011",
    "KC": "01100",
    "AD": "01101",
    "2D": "01110",
    "3D": "01111",
    "4D": "10000",
    "5D": "10001",
    "6D": "10010",
    "7D": "10011",
    "8D": "10100",
    "9D": "10101",
    "TD": "10110",
    "JD": "10111",
    "QD": "11000",
    "KD": "11001",
    "AH": "11010",
    "2H": "11011",
    "3H": "11100",
    "4H": "11101",
    "5H": "11110",
    "6H": "11111",
    "7H": "0000",
    "8H": "0001",
    "9H": "0010",
    "TH": "0011",
    "JH": "0100",
    "QH": "0101",
    "KH": "0110",
    "AS": "0111",
    "2S": "1000",
    "3S": "1001",
    "4S": "1010",
    "5S": "1011",
    "6S": "1100",
    "7S": "1101",
    "8S": "1110",
    "9S": "1111",
    "TS": "00",
    "JS": "01",
    "QS": "10",
    "KS": "11",
}


class Login(MnemonicLoader):
    """Represents the login page of the app"""

    # Used on boot.py when changing the locale on Settings
    SETTINGS_MENU_INDEX = 2

    def __init__(self, ctx):
        login_menu_items = [
            (t("Load Mnemonic"), self.load_key),
            (
                t("New Mnemonic"),
                (self.new_key if not Settings().security.hide_mnemonic else None),
            ),
            (t("Settings"), self.settings),
            (t("Tools"), self.tools),
            ("固件自检", self.self_check),
            (t("About"), self.about),
        ]
        if ctx.power_manager is not None:
            kboard.has_battery = ctx.power_manager.has_battery()
        if kboard.has_battery:
            login_menu_items.append((t("Shutdown"), self.shutdown))

        super().__init__(
            ctx,
            Menu(
                ctx,
                login_menu_items,
                back_label=None,
            ),
        )

    def new_key(self):
        """Handler for the 'new mnemonic' menu item"""
        if kboard.is_amigo:
            via_camera = "摄像头取熵\n拍照生成助记词"
            via_cards = "扑克牌创建\n按洗牌顺序输入"
            via_hex = "十六进制创建\n手输随机十六进制"
            via_words = "手输助记词\n逐词输入"
            via_d6 = "D6 骰子\n六面骰"
            via_d20 = "D20 骰子\n二十面骰"
        else:
            via_camera = t("Via Camera")
            via_cards = "扑克牌创建"
            via_hex = "十六进制创建"
            via_words = t("Via Words")
            via_d6 = t("Via D6")
            via_d20 = t("Via D20")

        submenu = Menu(
            self.ctx,
            [
                (via_camera, self.new_key_from_snapshot),
                (via_cards, self.new_key_from_card_entropy),
                (via_hex, self.new_key_from_hexadecimal_entropy),
                (via_words, lambda: self.load_key_from_text(new=True)),
                (via_d6, self.new_key_from_dice),
                (via_d20, lambda: self.new_key_from_dice(True)),
            ],
        )
        index, status = submenu.run_loop()
        if index == submenu.back_index:
            return MENU_CONTINUE
        return status

    def new_key_from_dice(self, d_20=False):
        """Handler for both 'new mnemonic'>'via D6/D20' menu items. Default is D6"""
        from .new_mnemonic.dice_rolls import DiceEntropy

        dice_entropy = DiceEntropy(self.ctx, d_20)
        captured_entropy = dice_entropy.new_key()
        if captured_entropy is not None:
            from embit.bip39 import mnemonic_from_bytes

            words = mnemonic_from_bytes(captured_entropy).split()
            return self._load_key_from_words(words, new=True)
        return MENU_CONTINUE

    @staticmethod
    def _normalize_card_events(card_data):
        if isinstance(card_data, list):
            text = "".join(card_data)
        else:
            text = str(card_data)
        text = text.upper()
        cards = []
        index = 0
        while index < len(text) - 1:
            card = text[index : index + 2]
            if card[0] in CARD_RANKS and card[1] in CARD_SUITS:
                cards.append(card)
                index += 2
            else:
                index += 1
        return cards

    @staticmethod
    def _card_entropy_bit_length(cards):
        return sum(
            len(CARD_EVENT_BITS[card])
            for card in Login._normalize_card_events(cards)
        )

    @staticmethod
    def _format_cards_for_iancoleman_hash(cards):
        clean_cards = " ".join(Login._normalize_card_events(cards))
        for suit, symbol in CARD_SUIT_HASH_SYMBOLS.items():
            clean_cards = clean_cards.replace(suit, symbol)
        return clean_cards

    @staticmethod
    def _mnemonic_from_iancoleman_cards(cards, len_mnemonic):
        """Generate BIP39 words using iancoleman "Card" entropy semantics."""
        from embit.bip39 import mnemonic_from_bytes

        entropy_bytes_len = HEX_ENTROPY_BYTES_BY_WORDS[len_mnemonic]
        card_text = Login._format_cards_for_iancoleman_hash(cards)
        entropy_bytes = sha256(card_text.encode("utf-8")).digest()
        return mnemonic_from_bytes(entropy_bytes[:entropy_bytes_len]).split()

    @staticmethod
    def _cards_preview(cards, limit=12):
        preview_cards = Login._normalize_card_events(cards)[-limit:]
        preview = " ".join(preview_cards)
        if len(cards) > limit:
            preview = ELLIPSIS + preview
        return preview

    def _capture_card_entropy(self, required_bits, cards=None):
        cards = list(cards or [])
        pending_rank = ""
        delete_flag = False

        def delete_card(buffer):
            nonlocal delete_flag
            delete_flag = True
            return buffer

        while True:
            actual_bits = self._card_entropy_bit_length(cards)
            if pending_rank:
                title = "%d/%d位 花色%s" % (
                    actual_bits,
                    required_bits,
                    pending_rank,
                )
                keyset = CARD_SUITS
            else:
                title = "%d/%d位 点数" % (actual_bits, required_bits)
                keyset = CARD_RANKS
            value = self.capture_from_keypad(
                title,
                [keyset],
                delete_key_fn=delete_card,
                go_on_change=True,
                buffer_title="\n" + self._cards_preview(cards),
            )
            if value == ESC_KEY:
                return None
            if delete_flag:
                delete_flag = False
                if pending_rank:
                    pending_rank = ""
                elif cards:
                    cards.pop()
                continue
            if not value:
                if pending_rank:
                    self.flash_text("请先选择花色")
                elif actual_bits >= required_bits:
                    return cards
                else:
                    self.flash_text("还差 %d 位熵" % (required_bits - actual_bits))
                continue
            if pending_rank:
                cards.append(pending_rank + value)
                pending_rank = ""
            else:
                pending_rank = value

    def _confirm_card_entropy(self, cards, required_bits):
        actual_bits = self._card_entropy_bit_length(cards)
        card_text = " ".join(cards)
        max_lines = max(4, self.ctx.display.height() // FONT_HEIGHT - 5)
        self.ctx.display.clear()
        self.ctx.display.draw_hcentered_text(
            "核对扑克牌\n已录入 %d 张\n熵值:%d/%d 位\n%s"
            % (len(cards), actual_bits, required_bits, card_text),
            max_lines=max_lines,
            highlight_prefix=":",
        )
        return self.prompt(t("Proceed?"), BOTTOM_PROMPT_LINE)

    def new_key_from_card_entropy(self):
        """Create a new mnemonic from playing-card entropy."""
        len_mnemonic = self.choose_len_mnemonic(extended=True)
        if not len_mnemonic:
            return MENU_CONTINUE

        required_bits = HEX_ENTROPY_BYTES_BY_WORDS[len_mnemonic] * 8
        intro = (
            "按洗好的扑克牌顺序输入\n\n"
            "点数:A 2-9 T J Q K\n"
            "花色:C梅 D方 H红 S黑\n"
            "例:AH QS 9D TC\n"
            "24 词需要多副牌或补充输入"
        )
        self.ctx.display.draw_hcentered_text(intro)
        if not self.prompt(t("Proceed?"), BOTTOM_PROMPT_LINE):
            return MENU_CONTINUE

        cards = []
        while True:
            cards = self._capture_card_entropy(required_bits, cards)
            if cards is None:
                return MENU_CONTINUE
            if self._confirm_card_entropy(cards, required_bits):
                break

        words = self._mnemonic_from_iancoleman_cards(cards, len_mnemonic)
        return self._load_key_from_words(words, new=True)

    @staticmethod
    def _format_hex_pairs(hex_text):
        clean_hex = "".join(
            ch for ch in str(hex_text).upper() if ch in HEX_ENTROPY_DIGITS
        )
        return " ".join(clean_hex[i : i + 2] for i in range(0, len(clean_hex), 2))

    @staticmethod
    def _mnemonic_from_iancoleman_hex(hex_text, len_mnemonic):
        """Generate BIP39 words using iancoleman "Hex [0-9A-F]" semantics."""
        clean_hex = "".join(
            ch for ch in str(hex_text).upper() if ch in HEX_ENTROPY_DIGITS
        )
        entropy_bytes_len = HEX_ENTROPY_BYTES_BY_WORDS[len_mnemonic]
        if len(clean_hex) != entropy_bytes_len * 2:
            raise ValueError("十六进制熵长度无效")

        from embit.bip39 import mnemonic_from_bytes

        # iancoleman normal HEX mode hashes the filtered text, then truncates.
        entropy_bytes = sha256(clean_hex.lower().encode("utf-8")).digest()
        return mnemonic_from_bytes(entropy_bytes[:entropy_bytes_len]).split()

    def new_key_from_hexadecimal_entropy(self):
        """Create a new mnemonic from typed hexadecimal entropy."""
        len_mnemonic = self.choose_len_mnemonic(extended=True)
        if not len_mnemonic:
            return MENU_CONTINUE

        required_chars = HEX_ENTROPY_BYTES_BY_WORDS[len_mnemonic] * 2
        intro = (
            "请输入随机十六进制字符\n\n"
            "%d 词需要 %d 个字符\n按树莓派规则处理:\n"
            "先对十六进制文本做 SHA256\n再生成 BIP39 助记词"
        ) % (len_mnemonic, required_chars)
        self.ctx.display.draw_hcentered_text(intro)
        if not self.prompt(t("Proceed?"), BOTTOM_PROMPT_LINE):
            return MENU_CONTINUE

        hex_chars = []
        delete_flag = False

        def delete_hex_char(buffer):
            nonlocal delete_flag
            delete_flag = True
            return buffer

        while True:
            preview = "".join(hex_chars[-24:])
            if len(hex_chars) > 24:
                preview = ELLIPSIS + preview
            char = self.capture_from_keypad(
                "十六进制 %d/%d" % (len(hex_chars), required_chars),
                [HEX_ENTROPY_DIGITS],
                delete_key_fn=delete_hex_char,
                possible_keys_fn=(
                    lambda _buffer: ""
                    if len(hex_chars) >= required_chars
                    else HEX_ENTROPY_DIGITS
                ),
                go_on_change=True,
                buffer_title="\n" + preview,
            )
            if char == ESC_KEY:
                return MENU_CONTINUE
            if char:
                if len(hex_chars) < required_chars:
                    hex_chars.append(char)
                continue
            if delete_flag:
                delete_flag = False
                if hex_chars:
                    hex_chars.pop()
                continue
            if len(hex_chars) < required_chars:
                self.flash_text(
                    "还需要 %d 个字符" % (required_chars - len(hex_chars))
                )
                continue
            break

        hex_entropy = "".join(hex_chars)
        self.ctx.display.clear()
        hex_display = self._format_hex_pairs(hex_entropy)
        max_lines = max(4, self.ctx.display.height() // FONT_HEIGHT - 5)
        self.ctx.display.draw_hcentered_text(
            "核对十六进制熵\n\n%s" % hex_display,
            max_lines=max_lines,
            highlight_prefix=":",
        )
        if not self.prompt(t("Proceed?"), BOTTOM_PROMPT_LINE):
            return MENU_CONTINUE

        words = self._mnemonic_from_iancoleman_hex(hex_entropy, len_mnemonic)
        return self._load_key_from_words(words, new=True)

    def new_key_from_snapshot(self):
        """Use camera's entropy to create a new mnemonic"""
        extra_option = t("Double mnemonic")
        len_mnemonic = self.choose_len_mnemonic(extra_option, extended=True)
        if not len_mnemonic:
            return MENU_CONTINUE

        self.ctx.display.draw_hcentered_text(
            t("Use camera's entropy to create a new mnemonic")
            + ". "
            + t("(Experimental)")
        )
        if self.prompt(t("Proceed?"), BOTTOM_PROMPT_LINE):
            from .capture_entropy import CameraEntropy

            camera_entropy = CameraEntropy(self.ctx)
            entropy_bytes = camera_entropy.capture()
            if entropy_bytes is not None:
                import binascii
                from embit.bip39 import mnemonic_from_bytes
                from ..bip39 import entropy_checksum

                entropy_hash = binascii.hexlify(entropy_bytes).decode()
                self.ctx.display.clear()
                self.ctx.display.draw_centered_text(
                    t("SHA256 of snapshot:") + "\n\n%s" % entropy_hash,
                    highlight_prefix=":",
                )
                self.ctx.input.wait_for_button()

                # Checks if user wants to create a double mnemonic
                if len_mnemonic == EXTRA_MNEMONIC_LENGTH_FLAG:
                    # import time  # Debug
                    # pre_t = time.ticks_ms()  # Debug

                    # split the mnemonic into two parts
                    first_12_entropy = entropy_bytes[:16]
                    second_12_entropy = entropy_bytes[16:32]

                    # calculate the checksum for the first 12 words
                    checksum1 = entropy_checksum(first_12_entropy, 4)
                    # print first 12 words

                    # replace checksum1 as first 4 bits of second 12 words
                    snd_12_array = bytearray(second_12_entropy)
                    snd_12_array[0] = (snd_12_array[0] & 0x0F) | (
                        (checksum1 & 0x0F) << 4
                    )
                    second_12_entropy = bytes(snd_12_array)
                    # reassemble the 256 bits entropy that has first 12 words with valid checksum
                    entropy_bytes = first_12_entropy + second_12_entropy

                    # Increment 1 to full 24 words entropy until
                    # both last 12 words and all 24 have valid checksum
                    tries = 0
                    entropy_int = int.from_bytes(entropy_bytes, "big")
                    while True:
                        # calculate the checksum for the new 24 words
                        ck_sum_24 = entropy_checksum(entropy_bytes, 8)

                        # Extract the lower 128 bits from the integer.
                        snd_12_int = entropy_int & MASK128
                        # Shift and combine with first 4 bits of the 24 wwords checksum
                        shifted_entr = ((snd_12_int << 4) & MASK128) | (ck_sum_24 >> 4)
                        shifted_entropy_bytes = shifted_entr.to_bytes(16, "big")
                        checksum_l_12 = entropy_checksum(shifted_entropy_bytes, 4)
                        # check if checksum_l_12 is equal to the last 4 bits of the
                        # checksum of the full 24 words
                        if checksum_l_12 == (ck_sum_24 & 0x0F):
                            break

                        # Increment the integer value and mask to 256 bits.
                        entropy_int = (entropy_int + 1) & MASK256
                        entropy_bytes = entropy_int.to_bytes(32, "big")
                        tries += 1
                        if tries > DOUBLE_MNEMONICS_MAX_TRIES:
                            raise ValueError("Failed to find a valid double mnemonic")
                    # print("Tries: {} / {} ms".format(tries, time.ticks_ms() - pre_t))  # Debug

                num_bytes = (
                    32
                    if len_mnemonic == EXTRA_MNEMONIC_LENGTH_FLAG
                    else HEX_ENTROPY_BYTES_BY_WORDS[len_mnemonic]
                )
                entropy_mnemonic = mnemonic_from_bytes(entropy_bytes[:num_bytes])
                return self._load_key_from_words(entropy_mnemonic.split(), new=True)
        return MENU_CONTINUE

    def _load_key_from_words(self, words, charset=LETTERS, new=False):
        mnemonic = " ".join(words)

        # Don't show word list confirmation or the mnemonic editor if hide mnemonic is enabled
        if not Settings().security.hide_mnemonic:
            if charset != LETTERS:
                if self._confirm_key_from_digits(mnemonic, charset) is not None:
                    return MENU_CONTINUE

            from .mnemonic_editor import MnemonicEditor

            mnemonic = MnemonicEditor(self.ctx, mnemonic, new).edit()
        if mnemonic is None:
            return MENU_CONTINUE

        passphrase = ""
        if not hasattr(Settings().wallet, "policy_type") and hasattr(
            Settings().wallet, "multisig"
        ):
            # Retro compatibility with old settings - Multisig (false or true)
            if Settings().wallet.multisig:
                Settings().wallet.policy_type = NAME_MULTISIG

        # New settings - Policy type (single-sig, multisig, miniscript)
        policy_type = POLICY_TYPE_IDS.get(Settings().wallet.policy_type, TYPE_SINGLESIG)
        network = NETWORKS[Settings().wallet.network]
        account = 0

        # If single-sig, by default we use p2wpkh
        # but respect the script type setting
        # in default wallet settings
        if policy_type == TYPE_SINGLESIG:
            script_type = SINGLESIG_SCRIPT_MAP.get(
                Settings().wallet.script_type, P2WPKH
            )

        # If multi-sig, by default we use p2wsh
        # but respect the script type setting
        # in default wallet settings, but if we're
        # using P2SH, we don't use, by default,
        # an account (m/45')
        if policy_type == TYPE_MULTISIG:
            script_type = MULTISIG_SCRIPT_MAP.get(Settings().wallet.script_type, P2WSH)
            if script_type == P2SH:
                account = None

        # If miniscript, by default we use p2wsh
        # but respect the script type setting
        # in default wallet settings
        if policy_type == TYPE_MINISCRIPT:
            script_type = MINISCRIPT_SCRIPT_MAP.get(
                Settings().wallet.script_type, P2WSH
            )

        derivation_path = ""

        from ..wallet import Wallet
        from ..themes import theme
        from .utils import Utils

        utils = Utils(self.ctx)
        while True:
            key = Key(
                mnemonic,
                policy_type,
                network,
                passphrase,
                account,
                script_type,
                derivation_path,
            )
            network_name = network["name"]
            if not derivation_path:
                derivation_path = key.derivation

            wallet_info = "\n" + utils.generate_wallet_info(
                network_name, policy_type, script_type, derivation_path, True
            )
            wallet_info += "\n" + (
                t("No Passphrase")
                if not passphrase
                else t("Passphrase") + " (%d): *…*" % len(passphrase)
            )

            self.ctx.display.clear()
            submenu = Menu(
                self.ctx,
                [
                    (t("Load Wallet"), lambda: None),
                    (t("Passphrase"), lambda: None),
                    (t("Customize"), lambda: None),
                ],
                offset=(
                    self.ctx.display.draw_hcentered_text(wallet_info, info_box=True)
                    * FONT_HEIGHT
                    + DEFAULT_PADDING
                ),
            )

            # draw fingerprint with highlight color
            self.ctx.display.draw_hcentered_text(
                key.fingerprint_hex_str(True),
                color=theme.highlight_color,
                bg_color=theme.info_bg_color,
            )

            # draw network with highlight color
            self.ctx.display.draw_hcentered_text(
                network_name,
                DEFAULT_PADDING + FONT_HEIGHT,
                color=Utils.get_network_color(network_name),
                bg_color=theme.info_bg_color,
            )

            index, _ = submenu.run_loop()
            if index == submenu.back_index:
                if self.prompt(t("Are you sure?"), self.ctx.display.height() // 2):
                    del key
                    return MENU_CONTINUE
            if index == 0:
                break
            if index == 1:
                from .wallet_settings import PassphraseEditor

                passphrase_editor = PassphraseEditor(self.ctx)
                temp_passphrase = passphrase_editor.load_passphrase_menu(mnemonic)
                if temp_passphrase is not None:
                    passphrase = temp_passphrase
            elif index == 2:
                from .wallet_settings import WalletSettings

                wallet_settings = WalletSettings(self.ctx)
                network, policy_type, script_type, account, derivation_path = (
                    wallet_settings.customize_wallet(key)
                )

        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(t("Loading…"))

        self.ctx.wallet = Wallet(key)
        return MENU_EXIT

    def tools(self):
        """Handler for the 'Tools' menu item"""
        from .tools import Tools

        while True:
            if Tools(self.ctx).run() == MENU_EXIT:
                break

        # Unimport tools
        sys.modules.pop("krux.pages.tools")
        del sys.modules["krux.pages"].tools

        return MENU_CONTINUE

    def settings(self):
        """Handler for the 'settings' menu item"""
        from .settings_page import SettingsPage

        settings_page = SettingsPage(self.ctx)
        return settings_page.settings()

    def self_check(self):
        """Handler for the 'firmware self-check' menu item"""
        from .self_check import SelfCheck

        return SelfCheck(self.ctx).self_check()

    def about(self):
        """Handler for the 'about' menu item"""

        import board
        from ..metadata import VERSION
        from ..qr import FORMAT_NONE

        title = "selfcustody.github.io/krux"
        msg = (
            title
            + "\n"
            + t("Hardware")
            + ": %s\n" % board.config["type"]
            + t("Version")
            + ": %s" % VERSION
        )
        offset_x = 0
        width = 0
        if kboard.is_cube:
            offset_x = self.ctx.display.width() // 4
            width = self.ctx.display.width() // 2
        self.display_qr_codes(
            title,
            FORMAT_NONE,
            msg,
            offset_x=offset_x,
            width=width,
            highlight_prefix=":",
        )
        return MENU_CONTINUE
