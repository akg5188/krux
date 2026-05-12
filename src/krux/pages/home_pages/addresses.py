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

import gc
from ...display import BOTTOM_PROMPT_LINE
from ...krux_settings import t
from ...settings import THIN_SPACE
from ...qr import FORMAT_NONE
from ...kboard import kboard
from .. import (
    Page,
    Menu,
    MENU_CONTINUE,
    MENU_EXIT,
    ESC_KEY,
)
from ...format import format_address

SCAN_ADDRESS_LIMIT = 50
EXPORT_ADDRESS_LIMIT = SCAN_ADDRESS_LIMIT * 100
BTC_DERIVATION_PURPOSES = (44, 49, 84, 86)
EVM_COIN_TYPE = 60


class Addresses(Page):
    """UI to show and scan wallet addresses"""

    def _amigo_text(self, chinese, default_text):
        """Use Chinese text on Amigo while keeping other boards unchanged."""
        if kboard.is_amigo:
            return chinese
        return default_text

    def addresses_menu(self):
        """Handler for the 'address' menu item"""
        # only show address for single-sig or multisig with wallet output descriptor loaded
        if not self.ctx.wallet.is_loaded() and (
            self.ctx.wallet.is_multisig() or self.ctx.wallet.is_miniscript()
        ):
            self.flash_error(
                self._amigo_text(
                    "请先加载钱包描述符",
                    t("Please load a wallet output descriptor"),
                )
            )
            return MENU_CONTINUE

        scan_label = self._amigo_text("扫描地址\n核对收款 / 找零", t("Scan Address"))
        list_label = self._amigo_text("地址列表\n收款 / 找零", t("List Addresses"))
        export_label = self._amigo_text("导出地址\n保存到 SD 卡", t("Export Addresses"))

        submenu = Menu(
            self.ctx,
            [
                (scan_label, lambda: self._receive_change_menu(self.scan_address)),
                (list_label, lambda: self._receive_change_menu(self.list_address_type)),
                (
                    export_label,
                    (
                        None
                        if not self.has_sd_card()
                        else lambda: self._receive_change_menu(self.export_address)
                    ),
                ),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def list_address_type(self, addr_type=0):
        """Handler for the 'receive addresses' or 'change addresses' menu item"""
        if not self.ctx.wallet.is_loaded() and (
            self.ctx.wallet.is_multisig() or self.ctx.wallet.is_miniscript()
        ):
            self.flash_error(
                self._amigo_text(
                    "请先加载钱包描述符",
                    t("Please load a wallet output descriptor"),
                )
            )
            return MENU_CONTINUE

        loading_txt = (
            self._amigo_text("正在加载找零地址...", t("Loading change addresses…"))
            if addr_type == 1
            else self._amigo_text("正在加载收款地址...", t("Loading receive addresses…"))
        )
        max_addresses = self.ctx.display.max_menu_lines() - 3
        address_index = 0
        while True:
            items = []
            if address_index >= max_addresses:
                items.append(
                    (
                        "%d...%d" % (address_index - max_addresses, address_index - 1),
                        lambda: MENU_EXIT,
                    )
                )

            self.ctx.display.clear()
            self.ctx.display.draw_centered_text(loading_txt)
            addresses = self.ctx.wallet.obtain_addresses(
                address_index, limit=max_addresses, branch_index=addr_type
            )
            for addr in addresses:
                pos_str = str(address_index) + "." + THIN_SPACE
                qr_title = pos_str + format_address(addr)
                items.append(
                    (
                        self.fit_to_line(addr, pos_str, fixed_chars=3),
                        lambda address=addr, title=qr_title: self.show_address(
                            address, title
                        ),
                    )
                )
                address_index += 1

            items.append(
                (
                    "%d...%d" % (address_index, address_index + max_addresses - 1),
                    lambda: MENU_EXIT,
                )
            )

            submenu = Menu(self.ctx, items)
            stay_on_this_addr_menu = True
            while stay_on_this_addr_menu:
                next_index = len(submenu.menu) - 2
                prev_index = 0 if address_index > max_addresses else -1
                index, _ = submenu.run_loop(
                    swipe_up_fnc=lambda: (next_index, MENU_EXIT),
                    swipe_down_fnc=lambda: (prev_index, MENU_EXIT),
                )

                if index == submenu.back_index:  # Back
                    del submenu, items
                    gc.collect()
                    return MENU_CONTINUE
                if index == next_index:  # Next
                    stay_on_this_addr_menu = False
                if index == 0 and address_index > max_addresses:  # Prev
                    stay_on_this_addr_menu = False
                    address_index -= 2 * max_addresses

    def _qr_highlight_addr(self, formatted_text, y_offset):
        """Case highlight address for QR"""

        from ..utils import Utils

        utils = Utils(self.ctx)

        first_line_prefix = "." + THIN_SPACE
        lines = self.ctx.display.to_lines(formatted_text)
        highlight_state = True
        for i, line in enumerate(lines):
            x_offset = self.ctx.display.get_center_offset_x(line)
            addr_prefix = None
            # case for addr with index prefix
            if i == 0 and first_line_prefix in line:
                addr_prefix = line[: line.find(first_line_prefix)] + first_line_prefix

            highlight_state = utils.display_addr_highlighted(
                y_offset, x_offset, line, i, highlight_state, addr_prefix
            )

    def show_address(self, addr, title="", quick_exit=False):
        """Show addr provided as a QRCode"""
        from ..qr_view import SeedQRView

        seed_qr_view = SeedQRView(self.ctx, data=addr, title=title)
        seed_qr_view.display_qr(
            allow_export=True,
            transcript_tools=False,
            quick_exit=quick_exit,
            highlight_function=self._qr_highlight_addr,
        )

        return MENU_CONTINUE

    def show_receive_address_by_index(self):
        """Capture an address index and display that receive address."""
        from ..utils import Utils

        utils = Utils(self.ctx)
        index = ""
        while index == "":
            index = utils.capture_index_from_keypad(
                self._amigo_text("收款地址编号", t("Index")),
                initial_val=0,
                range_min=0,
                range_max=EXPORT_ADDRESS_LIMIT - 1,
            )
        if index is None:
            return MENU_CONTINUE

        try:
            address = next(
                self.ctx.wallet.obtain_addresses(index, limit=1, branch_index=0)
            )
        except Exception as exc:
            self.flash_error(str(exc))
            return MENU_CONTINUE

        title = str(index) + "." + THIN_SPACE + format_address(address)
        return self.show_address(address, title=title)

    def _default_btc_address_path(self):
        """Return the current wallet account path extended to address index 0."""
        try:
            derivation = self.ctx.wallet.key.derivation
        except Exception:
            derivation = ""
        if not derivation:
            derivation = "m/84h/0h/0h"
        return derivation + "/0/0"

    def show_address_by_derivation_path(self):
        """Capture a full derivation path and show the derived BTC or EVM address."""
        return self._show_derived_address_by_path(self._default_btc_address_path())

    def _capture_derivation_path(self, default_path):
        from ..wallet_settings import DERIVATION_KEYPAD

        derivation_path = self.capture_from_keypad(
            self._amigo_text("派生路径", t("Derivation Path")),
            [DERIVATION_KEYPAD],
            starting_buffer=default_path.replace("'", "h"),
            delete_key_fn=lambda value: value[:-1] if len(value) > 1 else value,
        )
        if derivation_path == ESC_KEY:
            return None
        return str(derivation_path or "").strip().replace("'", "h")

    def _path_parts(self, derivation_path):
        parts = [part for part in derivation_path.split("/") if part]
        if not parts or parts[0] != "m":
            raise ValueError("派生路径必须从 m/ 开始")
        if len(parts) < 6:
            raise ValueError("请输入完整地址路径\n例如 m/84h/0h/0h/0/0")
        return parts

    @staticmethod
    def _path_node_value(node):
        value = node[:-1] if node and node[-1] in "'hH" else node
        if not value.isdigit():
            raise ValueError("派生路径片段无效: %s" % node)
        return int(value)

    @staticmethod
    def _btc_address_type_label(purpose, coin_type):
        network = "主网" if coin_type == 0 else "测试网"
        purpose_labels = {
            44: "Legacy P2PKH",
            49: "Nested SegWit P2SH-P2WPKH",
            84: "Native SegWit P2WPKH",
            86: "Taproot P2TR",
        }
        return "BTC %s %s" % (network, purpose_labels[purpose])

    def derive_address_from_path(self, derivation_path):
        """Derive a displayable wallet address from a full BTC or EVM path."""
        from embit import bip32
        from .sign_message_ui import SignMessage
        from ...web3 import derive_web3_address, ethereum_checksum_address

        parts = self._path_parts(derivation_path)
        # Parse once with embit too, so invalid BIP32 ranges fail before display.
        bip32.parse_path(derivation_path)

        purpose = self._path_node_value(parts[1])
        coin_type = self._path_node_value(parts[2])

        if coin_type == EVM_COIN_TYPE:
            address = derive_web3_address(
                self.ctx.wallet.key,
                derivation_path,
                checksum=False,
            )
            return "EVM 以太坊地址", ethereum_checksum_address(address)

        if coin_type in (0, 1) and purpose in BTC_DERIVATION_PURPOSES:
            address = SignMessage(self.ctx).get_bitcoin_address(derivation_path)
            return self._btc_address_type_label(purpose, coin_type), address

        raise ValueError("暂只支持 BTC 或 EVM 地址路径")

    def _derived_address_preview(self, derivation_path, address_type, address):
        return "\n".join(
            [
                "类型: " + address_type,
                "路径: " + derivation_path,
                "地址:",
                address,
            ]
        )

    def _show_derived_address_by_path(self, default_path):
        derivation_path = self._capture_derivation_path(default_path)
        if derivation_path is None:
            return MENU_CONTINUE
        try:
            address_type, address = self.derive_address_from_path(derivation_path)
        except Exception as exc:
            self.flash_error(str(exc))
            return MENU_CONTINUE

        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(
            self._derived_address_preview(derivation_path, address_type, address),
            highlight_prefix=":",
        )
        if not self.prompt("继续?", BOTTOM_PROMPT_LINE):
            return MENU_CONTINUE
        return self.show_address(
            address,
            title="%s\n%s" % (address_type, self.fit_to_line(derivation_path)),
        )

    def _receive_change_menu(self, callback):
        receive_label = self._amigo_text("收款地址", t("Receive"))
        change_label = self._amigo_text("找零地址", t("Change"))
        submenu = Menu(
            self.ctx,
            [
                (receive_label, callback),
                (
                    change_label,
                    (
                        None
                        if not self.ctx.wallet.has_change_addr()
                        else lambda: callback(1)
                    ),
                ),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def export_address(self, addr_type=0):
        """Allow user to export addresses to SD card"""
        from ..utils import Utils
        from ...sd_card import SDHandler, ADDRESSES_FILE_EXTENSION
        from ..file_operations import SaveFile
        from ...wdt import wdt

        utils = Utils(self.ctx)

        start_address = ""
        while start_address == "":
            start_address = utils.capture_index_from_keypad(
                self._amigo_text("起始编号", t("Index")), initial_val=0
            )
        if start_address is None:
            return

        quantity = ""
        while quantity == "":
            quantity = utils.capture_index_from_keypad(
                self._amigo_text("导出数量", t("Quantity")),
                initial_val=SCAN_ADDRESS_LIMIT,
                range_min=1,
                range_max=EXPORT_ADDRESS_LIMIT,
            )
        if quantity is None:
            return

        default_filename = "Receive" if addr_type == 0 else "Change"
        default_filename += "-" + self.ctx.wallet.key.fingerprint_hex_str()
        save_page = SaveFile(self.ctx)
        filename = save_page.set_filename(
            default_filename,
            file_extension=ADDRESSES_FILE_EXTENSION,
        )
        if filename == ESC_KEY:
            return

        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(
            self._amigo_text("处理中...", t("Processing…"))
        )

        try:
            with SDHandler():
                with open(SDHandler.PATH_STR % filename, "w") as file:
                    i = start_address
                    for addr in self.ctx.wallet.obtain_addresses(
                        start_address, limit=quantity, branch_index=addr_type
                    ):
                        file.write(str(i) + "," + addr + "\n")
                        i += 1

                        if i % SCAN_ADDRESS_LIMIT == 0:
                            self.ctx.display.clear()
                            self.ctx.display.draw_centered_text(
                                self._amigo_text("处理中...", t("Processing…"))
                                + "\n\n%d%%" % int((i - start_address) / quantity * 100)
                            )
                            wdt.feed()

                self.flash_text(
                    self._amigo_text("已保存到 SD 卡:", t("Saved to SD card:"))
                    + "\n\n%s" % filename,
                    highlight_prefix=":",
                )
        except OSError:
            self.flash_text(
                self._amigo_text("未检测到 SD 卡.", t("SD card not detected."))
            )

    def _scan_highlight_addr(self, result_message):
        """Case highlight address for scan"""
        from ..utils import Utils

        utils = Utils(self.ctx)

        lines = self.ctx.display.to_lines(result_message)
        y_offset = self.ctx.display.get_center_offset_y(len(lines))
        highlight = True
        count_empty = 0
        addr_highlighted = False
        for i, line in enumerate(lines):
            if len(line) > 0:
                if (count_empty == 0 and "." not in line) or count_empty == 1:
                    x_offset = self.ctx.display.get_center_offset_x(line)
                    highlight = utils.display_addr_highlighted(
                        y_offset, x_offset, line, i, highlight
                    )
                    addr_highlighted = True
            else:
                count_empty += 1
                if addr_highlighted:
                    break

    def scan_address(self, addr_type=0):
        """Handler for the 'receive' or 'change' menu item"""
        from ..qr_capture import QRCodeCapture
        from ..encryption_ui import decrypt_kef

        qr_capture = QRCodeCapture(self.ctx)
        data, qr_format = qr_capture.qr_capture_loop()
        if data is None or qr_format != FORMAT_NONE:
            self.flash_error(self._amigo_text("加载失败", t("Failed to load")))
            return MENU_CONTINUE

        try:
            data = decrypt_kef(self.ctx, data)

            # Cpython raises UnicodeDecodeError, MaixPy raises TypeError
            try:
                data = data.decode()
            except:
                self.flash_error(self._amigo_text("加载失败", t("Failed to load")))
                return MENU_CONTINUE
        except KeyError:
            self.flash_error(self._amigo_text("解密失败", t("Failed to decrypt")))
            return MENU_CONTINUE
        except ValueError:
            # ValueError=not KEF or declined to decrypt
            pass

        addr = None
        data = data.decode() if isinstance(data, bytes) else data
        try:
            from ...wallet import parse_address

            addr = parse_address(data)
        except:
            self.flash_error(self._amigo_text("无效地址", t("Invalid address")))
            return MENU_CONTINUE

        self.show_address(data, title=format_address(addr), quick_exit=True)

        if self.ctx.wallet.is_loaded() or not self.ctx.wallet.is_multisig():
            self.ctx.display.clear()
            if not self.prompt(
                self._amigo_text("确认这是本钱包地址?", t("Check that address belongs to this wallet?")),
                self.ctx.display.height() // 2,
            ):
                return MENU_CONTINUE

            checking_match_txt = self._amigo_text(
                "正在核对地址... %d-%d", t("Verifying…") + " " + t("%d to %d")
            )
            checked_no_match_txt = self._amigo_text(
                "已检查 %d 个地址, 没找到匹配项.",
                t("Checked %d addresses with no matches."),
            )
            is_valid_txt = self._amigo_text(
                "%s\n\n该地址属于本钱包", "%s\n\n" + t("is a valid address!")
            )
            not_found_txt = self._amigo_text(
                "%s\n\n未在前 %d 个地址中找到",
                "%s\n\n" + t("was NOT FOUND in the first %d addresses"),
            )

            found = False
            num_checked = 0
            while not found:
                self.ctx.display.clear()
                self.ctx.display.draw_centered_text(
                    checking_match_txt
                    % (num_checked, num_checked + SCAN_ADDRESS_LIMIT - 1)
                )
                for some_addr in self.ctx.wallet.obtain_addresses(
                    num_checked, limit=SCAN_ADDRESS_LIMIT, branch_index=addr_type
                ):
                    num_checked += 1

                    found = addr == some_addr
                    if found:
                        break

                gc.collect()

                if not found:
                    self.ctx.display.clear()
                    self.ctx.display.draw_centered_text(
                        checked_no_match_txt % num_checked
                    )
                    if not self.prompt(
                        self._amigo_text("继续查找下一批?", t("Try more?")),
                        BOTTOM_PROMPT_LINE,
                    ):
                        break

            self.ctx.display.clear()
            result_message = (
                is_valid_txt % (str(num_checked - 1) + ".\n\n" + format_address(addr))
                if found
                else not_found_txt % (format_address(addr), num_checked)
            )
            self.ctx.display.draw_centered_text(result_message)
            self._scan_highlight_addr(result_message)
            self.ctx.input.wait_for_button()
        return MENU_CONTINUE
