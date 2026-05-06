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

from ...display import BOTTOM_PROMPT_LINE
from ...key import Key
from ...wallet import Wallet
from .. import DIGITS, ESC_KEY, MENU_CONTINUE, Menu, Page


DEFAULT_SECONDARY_SHIFT_VALUES = (8, 7, 6, 7, 6, 7, 7, 3, 5, 2, 4, 2)
SECONDARY_WORD_COUNT = 12
SECONDARY_OPERATORS = "+-*/"
STEEL_RESTORE_WEIGHTS = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
STEEL_RESTORE_WEIGHT_SET = set(STEEL_RESTORE_WEIGHTS)


class SecondaryMnemonic(Page):
    """TP-style second-layer mnemonic transform for Amigo."""

    def run(self):
        """Show the second-layer mnemonic menu."""
        submenu = Menu(
            self.ctx,
            [
                ("默认加密\n+8 +7 +6 ...", self.default_encrypt),
                ("默认还原\n-8 -7 -6 ...", self.default_restore),
                ("自定义加密\n12 组 +8/-8", self.custom_encrypt),
                ("自定义还原\n12 组 +8/-8", self.custom_restore),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    @staticmethod
    def _default_entries(restore=False):
        operator = "-" if restore else "+"
        return [(operator, value) for value in DEFAULT_SECONDARY_SHIFT_VALUES]

    @staticmethod
    def _parse_shift_token(token, default_operator):
        token = str(token or "").strip()
        if not token:
            raise ValueError("运算项不能为空")

        operator = default_operator
        if token[0] in SECONDARY_OPERATORS:
            operator = token[0]
            token = token[1:].strip()
        if operator not in SECONDARY_OPERATORS:
            raise ValueError("只支持 +、-、*、/ 四种运算")
        if not token.isdigit():
            raise ValueError("移动数字必须是非负整数")

        value = int(token)
        if operator in "*/" and value <= 0:
            raise ValueError("乘法/除法的数字必须大于 0")
        return operator, value

    @classmethod
    def parse_shift_entries(cls, raw, default_operator="+", expected_len=12):
        """Parse space/comma separated shift entries such as '+8 -7 +6'."""
        normalized = (
            str(raw or "")
            .replace("，", " ")
            .replace(",", " ")
            .replace("；", " ")
            .replace(";", " ")
            .strip()
        )
        if not normalized:
            return cls._default_entries(default_operator == "-")

        tokens = [token for token in normalized.split() if token]
        if len(tokens) == 1:
            return [
                cls._parse_shift_token(tokens[0], default_operator)
                for _ in range(expected_len)
            ]
        if len(tokens) != expected_len:
            raise ValueError("需要输入 12 组运算，例如 +8 +7 +6 ...")
        return [cls._parse_shift_token(token, default_operator) for token in tokens]

    @staticmethod
    def format_shift_entries(entries):
        """Format entries as '+8 +7 +6 ...' for review."""
        return " ".join("%s%d" % (operator, value) for operator, value in entries)

    @staticmethod
    def _transform_index(index, operator, value):
        if index < 0 or index >= 2048:
            raise ValueError("BIP39 序号必须在 0 到 2047 之间")
        if operator == "+":
            return (index + value) % 2048
        if operator == "-":
            return (index - value) % 2048
        if operator == "*":
            return min(index * value, 2047)
        if operator == "/":
            return index // value
        raise ValueError("不支持的运算方式")

    @classmethod
    def shift_words(cls, words, entries):
        """Transform 12 BIP39 words with literal per-word operators."""
        from embit.wordlists.bip39 import WORDLIST

        if len(words) != SECONDARY_WORD_COUNT:
            raise ValueError("二次助记词第一版只支持 12 词")
        if len(entries) != SECONDARY_WORD_COUNT:
            raise ValueError("移动数字数量必须是 12 组")

        shifted_words = []
        for position, word in enumerate(words):
            try:
                word_index = WORDLIST.index(word)
            except ValueError as exc:
                raise ValueError("第 %d 个词不是 BIP39 英文词" % (position + 1)) from exc
            operator, value = entries[position]
            shifted_words.append(
                WORDLIST[cls._transform_index(word_index, operator, int(value))]
            )
        return shifted_words

    @staticmethod
    def parse_steel_plate_indices(raw, expected_len=12):
        """Parse 12 steel plate groups into 0-based BIP39 word indices."""
        normalized = (
            str(raw or "")
            .replace("，", ",")
            .replace("；", ",")
            .replace("\n", ",")
            .strip()
        )
        if not normalized:
            raise ValueError("请输入钢板序号")

        if "," in normalized:
            groups = [group.strip() for group in normalized.split(",")]
            if len(groups) != expected_len:
                raise ValueError("需要输入 12 组钢板序号")
            return [
                SecondaryMnemonic._parse_steel_plate_group(group, position)
                for position, group in enumerate(groups, 1)
            ]

        tokens = normalized.split()
        if len(tokens) != expected_len or any(not token.isdigit() for token in tokens):
            raise ValueError("请输入 12 个序号，或用逗号分隔 12 组打孔位")

        indices = [int(token) for token in tokens]
        if any(index < 0 or index >= 2048 for index in indices):
            raise ValueError("钢板序号必须在 0 到 2047 之间")
        return indices

    @staticmethod
    def _parse_steel_plate_group(group, position):
        if not group:
            raise ValueError("第%02d组为空" % position)
        tokens = group.split()
        if any(not token.isdigit() for token in tokens):
            raise ValueError("第%02d组含非法内容" % position)

        numbers = [int(token) for token in tokens]
        if len(numbers) == 1 and 0 <= numbers[0] < 2048:
            return numbers[0]

        invalid = [
            number for number in numbers if number not in STEEL_RESTORE_WEIGHT_SET
        ]
        if invalid:
            raise ValueError("第%02d组存在非法权重" % position)
        if len(set(numbers)) != len(numbers):
            raise ValueError("第%02d组有重复权重" % position)

        index = sum(numbers)
        if index >= 2048:
            raise ValueError("第%02d组权重和超出范围" % position)
        return index

    @staticmethod
    def words_from_indices(indices):
        from embit.wordlists.bip39 import WORDLIST

        return [WORDLIST[int(index)] for index in indices]

    @classmethod
    def restore_words_from_steel_plate(cls, raw_plate_numbers, restore_entries=None):
        """Restore real words from steel groups holding secondary fake words."""
        fake_words = cls.words_from_indices(
            cls.parse_steel_plate_indices(raw_plate_numbers)
        )
        return cls.shift_words(
            fake_words,
            restore_entries or cls._default_entries(True),
        )

    def default_encrypt(self):
        """Run the default + shift used by the Raspberry Pi signer."""
        return self._run_shift(self._default_entries(False), "二次加密结果")

    def default_restore(self):
        """Run the default - shift to recover a default-encrypted mnemonic."""
        return self._run_shift(self._default_entries(True), "二次还原结果")

    def custom_encrypt(self):
        """Capture custom literal operators and apply them to the mnemonic."""
        return self._capture_and_run("+", "二次加密结果")

    def custom_restore(self):
        """Capture custom literal operators and apply them to the mnemonic."""
        return self._capture_and_run("-", "二次还原结果")

    def _capture_and_run(self, default_operator, title):
        starting_buffer = self.format_shift_entries(
            self._default_entries(default_operator == "-")
        )
        captured = self.capture_from_keypad(
            "输入 12 组运算",
            [DIGITS + " +-*/"],
            starting_buffer=starting_buffer,
            buffer_title="空格分隔\n例如 +8 -7",
        )
        if captured == ESC_KEY:
            return MENU_CONTINUE
        try:
            entries = self.parse_shift_entries(captured, default_operator)
        except ValueError as exc:
            self.flash_error(str(exc))
            return MENU_CONTINUE
        return self._run_shift(entries, title)

    def _run_shift(self, entries, title):
        source_words = self.ctx.wallet.key.mnemonic.split(" ")
        try:
            result_words = self.shift_words(source_words, entries)
        except ValueError as exc:
            self.flash_error(str(exc))
            return MENU_CONTINUE

        if any(operator in "*/" for operator, _ in entries):
            if not self.prompt(
                "乘除会丢失信息，真钱包慎用。\n继续?",
                self.ctx.display.height() // 2,
            ):
                return MENU_CONTINUE

        result_mnemonic = " ".join(result_words)
        self.display_mnemonic(result_mnemonic, title=title)
        self.ctx.input.wait_for_button()
        if not self._mnemonic_checksum_is_valid(result_mnemonic):
            self.flash_text("结果校验无效\n仅用于备份/还原")
            return MENU_CONTINUE
        if self.prompt("加载结果为当前助记词?", BOTTOM_PROMPT_LINE):
            self._load_result(result_mnemonic)
        return MENU_CONTINUE

    @staticmethod
    def _mnemonic_checksum_is_valid(mnemonic):
        from embit import bip39

        return bip39.mnemonic_is_valid(mnemonic)

    def _load_result(self, mnemonic):
        current_key = self.ctx.wallet.key
        new_key = Key(
            mnemonic,
            current_key.policy_type,
            current_key.network,
            "",
            current_key.account_index,
            current_key.script_type,
        )
        self.ctx.wallet = Wallet(new_key)
        self.flash_text(
            "%s：已加载" % new_key.fingerprint_hex_str(),
            highlight_prefix=":",
        )
