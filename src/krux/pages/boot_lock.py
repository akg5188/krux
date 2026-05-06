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

import os
import binascii
import ujson as json
import urandom as random

from . import DIGITS, ESC_KEY, MENU_CONTINUE, Menu, Page
from ..themes import theme

BOOT_LOCK_PATH = "/flash/boot_lock.json"
BOOT_LOCK_VERSION = 1
BOOT_LOCK_MIN_LEN = 4
BOOT_LOCK_MAX_LEN = 12
BOOT_LOCK_ITERATIONS = 100000
BOOT_LOCK_MAX_ATTEMPTS = 5
BOOT_LOCK_CONTEXT = b"krux-amigo-boot-lock-v1"
BOOT_LOCK_MAX_FILE_SIZE = 512


def _constant_time_equal(left, right):
    """Compare two byte-like objects without early exit."""
    if not isinstance(left, (bytes, bytearray)):
        return False
    if not isinstance(right, (bytes, bytearray)):
        return False
    diff = len(left) ^ len(right)
    for index in range(min(len(left), len(right))):
        diff |= left[index] ^ right[index]
    return diff == 0


class BootLockStore:
    """Small flash-backed PIN hash store for Amigo's boot lock.

    This is a local convenience gate. It is intentionally not described as a
    secure element or as equivalent to the Raspberry Pi encrypted boot partition.
    """

    def __init__(self, path=BOOT_LOCK_PATH):
        self.path = path

    def is_configured(self):
        """Returns True when a valid lock file exists."""
        return self._load_record() is not None

    def set_pin(self, pin):
        """Stores a new PIN hash."""
        if not self._valid_pin(pin):
            return False, "口令必须是 4 到 12 位数字"
        salt = self._random_salt()
        record = {
            "version": BOOT_LOCK_VERSION,
            "iterations": BOOT_LOCK_ITERATIONS,
            "salt": self._hexlify(salt),
            "hash": self._hexlify(self._derive_hash(pin, salt, BOOT_LOCK_ITERATIONS)),
        }
        try:
            with open(self.path, "w") as f:
                f.write(json.dumps(record))
            return True, "开机口令已保存"
        except Exception as error:
            return False, "保存开机口令失败: %s" % error

    def verify_pin(self, pin):
        """Checks a candidate PIN against the stored hash."""
        record = self._load_record()
        if record is None:
            return False
        try:
            salt = binascii.unhexlify(record["salt"])
            expected = binascii.unhexlify(record["hash"])
            iterations = int(record.get("iterations", BOOT_LOCK_ITERATIONS))
        except Exception:
            return False
        candidate = self._derive_hash(pin, salt, iterations)
        return _constant_time_equal(candidate, expected)

    def clear(self):
        """Deletes the stored boot lock."""
        try:
            os.remove(self.path)
        except Exception:
            pass

    def _load_record(self):
        try:
            with open(self.path, "r") as f:
                contents = f.read(BOOT_LOCK_MAX_FILE_SIZE + 1)
            if len(contents) > BOOT_LOCK_MAX_FILE_SIZE:
                return None
            record = json.loads(contents)
        except Exception:
            return None
        if not isinstance(record, dict):
            return None
        if record.get("version") != BOOT_LOCK_VERSION:
            return None
        if not self._valid_hex(record.get("salt"), 32):
            return None
        if not self._valid_hex(record.get("hash"), 64):
            return None
        return record

    @staticmethod
    def _valid_pin(pin):
        return (
            isinstance(pin, str)
            and pin.isdigit()
            and BOOT_LOCK_MIN_LEN <= len(pin) <= BOOT_LOCK_MAX_LEN
        )

    @staticmethod
    def _valid_hex(value, length):
        if not isinstance(value, str) or len(value) != length:
            return False
        for char in value:
            if char not in "0123456789abcdefABCDEF":
                return False
        return True

    @staticmethod
    def _hexlify(value):
        return binascii.hexlify(value).decode("ascii")

    @staticmethod
    def _random_salt():
        return bytes([random.getrandbits(8) for _ in range(16)])

    @staticmethod
    def _device_secret():
        try:
            from machine import unique_id

            uid = unique_id()
        except Exception:
            uid = b""
        if isinstance(uid, str):
            uid = uid.encode()
        if not isinstance(uid, (bytes, bytearray)):
            uid = b""
        return bytes(uid)

    @classmethod
    def _derive_hash(cls, pin, salt, iterations):
        secret = cls._pin_secret(pin)
        full_salt = BOOT_LOCK_CONTEXT + cls._device_secret() + bytes(salt)
        try:
            import uhashlib_hw

            return uhashlib_hw.pbkdf2_hmac_sha256(secret, full_salt, iterations)
        except Exception:
            import hashlib

            return hashlib.pbkdf2_hmac("sha256", secret, full_salt, iterations)

    @staticmethod
    def _pin_secret(pin):
        try:
            import uhashlib_hw

            return uhashlib_hw.sha256(pin.encode()).digest()
        except Exception:
            import hashlib

            return hashlib.sha256(pin.encode()).digest()


class BootLockPage(Page):
    """Amigo-native boot PIN UI."""

    def __init__(self, ctx, store=None):
        super().__init__(ctx, None)
        self.store = store or BootLockStore()

    def unlock_at_boot(self):
        """Runs the boot gate. Returns False after too many wrong attempts."""
        if not self.store.is_configured():
            return True

        self.flash_text("已启用开机口令\n请输入数字口令")
        attempts = 0
        while attempts < BOOT_LOCK_MAX_ATTEMPTS:
            pin = self._capture_pin("开机口令", allow_cancel=False)
            if self.store.verify_pin(pin):
                self.flash_text("设备已解锁", theme.go_color)
                return True
            attempts += 1
            remaining = BOOT_LOCK_MAX_ATTEMPTS - attempts
            if remaining:
                self.flash_error("开机口令错误\n还可重试 %d 次" % remaining)
        self.flash_error("开机口令错误次数过多\n设备即将关机")
        return False

    def manage(self):
        """Settings entry for enabling, changing, and disabling the boot lock."""
        items = [("功能说明", self.show_info)]
        if self.store.is_configured():
            items.extend(
                [
                    ("修改开机口令", self.change_pin),
                    ("关闭开机口令", self.disable),
                ]
            )
        else:
            items.append(("开启开机口令", self.enable))
        submenu = Menu(self.ctx, items)
        submenu.run_loop()
        return MENU_CONTINUE

    def show_info(self):
        self.flash_text(
            "开机口令会在进入主菜单前拦截。\n"
            "它保存在本机闪存中，适合防误用。\n"
            "它不是硬件安全芯片。"
        )
        return MENU_CONTINUE

    def enable(self):
        if not self.prompt(
            "开机口令只保护本机启动入口。\n不是硬件安全芯片。\n继续?",
            self.ctx.display.height() // 2,
        ):
            return MENU_CONTINUE
        return self._set_new_pin()

    def change_pin(self):
        if not self._verify_current_pin():
            return MENU_CONTINUE
        return self._set_new_pin()

    def disable(self):
        if not self._verify_current_pin():
            return MENU_CONTINUE
        if self.prompt("关闭开机口令?", self.ctx.display.height() // 2):
            self.store.clear()
            self.flash_text("开机口令已关闭")
        return MENU_CONTINUE

    def _verify_current_pin(self):
        pin = self._capture_pin("当前开机口令")
        if pin == ESC_KEY:
            return False
        if not self.store.verify_pin(pin):
            self.flash_error("当前开机口令错误")
            return False
        return True

    def _set_new_pin(self):
        first = self._capture_pin("新开机口令")
        if first == ESC_KEY:
            return MENU_CONTINUE
        if not BootLockStore._valid_pin(first):
            self.flash_error("口令必须是 4 到 12 位数字")
            return MENU_CONTINUE
        second = self._capture_pin("再次输入新口令")
        if second == ESC_KEY:
            return MENU_CONTINUE
        if first != second:
            self.flash_error("两次输入不一致")
            return MENU_CONTINUE
        ok, message = self.store.set_pin(first)
        if ok:
            self.flash_text(message, theme.go_color)
        else:
            self.flash_error(message)
        return MENU_CONTINUE

    def _capture_pin(self, title, allow_cancel=True):
        while True:
            captured = self.capture_from_keypad(
                title,
                [DIGITS],
                esc_prompt=allow_cancel,
                mask_buffer=True,
            )
            if captured == ESC_KEY:
                if allow_cancel:
                    return ESC_KEY
                self.flash_error("必须输入开机口令")
                continue
            if len(captured) <= BOOT_LOCK_MAX_LEN:
                return captured
            self.flash_error("口令最多 12 位")
