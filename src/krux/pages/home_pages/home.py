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
from .. import (
    Page,
    Menu,
    MENU_CONTINUE,
    ESC_KEY,
    LOAD_FROM_CAMERA,
    LOAD_FROM_SD,
)
from ...display import BOTTOM_PROMPT_LINE
from ...qr import FORMAT_NONE, FORMAT_PMOFN
from ...krux_settings import t, Settings
from ...format import replace_decimal_separator
from ...key import TYPE_SINGLESIG
from ...kboard import kboard


class Home(Page):
    """Home is the main menu page of the app"""

    def __init__(self, ctx):
        shtn_reboot_label = t("Shutdown") if kboard.has_battery else t("Reboot")
        super().__init__(
            ctx,
            Menu(
                ctx,
                [
                    (
                        self._amigo_home_label("扫码签名", "比特币 / 链上 / 消息"),
                        self.signing_center,
                    ),
                    (
                        self._amigo_home_label("助记词工具", "备份 / BIP85 / 钢板"),
                        self.mnemonic_center,
                    ),
                    (
                        self._amigo_home_label("连接钱包", "公钥 / 地址 / 描述符"),
                        self.connect_wallet_center,
                    ),
                    (
                        self._amigo_home_label("固件自检", "设备 / 触摸 / SD 卡"),
                        self.self_check,
                    ),
                    (shtn_reboot_label, self.shutdown),
                ],
                back_label=None,
            ),
        )

    def _amigo_home_label(self, title, subtitle):
        """Use short two-line labels on Amigo's large touch screen."""
        if kboard.is_amigo:
            return title + "\n" + subtitle
        return title

    def _amigo_text(self, chinese, default_text):
        """Use Chinese text on Amigo while keeping other boards unchanged."""
        if kboard.is_amigo:
            return chinese
        return default_text

    def signing_center(self):
        """Pi-style signing hub: scan requests first, then choose signer route."""
        if kboard.is_amigo:
            psbt_label = "比特币交易签名\n扫码 / SD 卡"
            message_label = "比特币消息签名\n先扫地址再签名"
            web3_label = "扫码签名\n消息 / 交易 / TP 中转"
        else:
            psbt_label = "比特币 PSBT"
            message_label = "比特币消息"
            web3_label = "Web3 扫码签名"
        submenu = Menu(
            self.ctx,
            [
                (psbt_label, self.sign_psbt),
                (message_label, self.sign_message),
                (web3_label, self.web3_scan_and_sign),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def connect_wallet_center(self):
        """Group wallet connection and watch-only exports together."""
        if kboard.is_amigo:
            web3_label = "连接钱包\nOKX / Bitget / MetaMask"
            xpub_label = "扩展公钥\n文本 / 二维码 / SD 卡"
            address_label = "地址核对\n收款 / 找零 / 扫码验址"
            descriptor_label = "钱包描述符\n多签 / 迷你脚本"
        else:
            web3_label = "Web3 连接钱包"
            xpub_label = "导出 BTC xpub/zpub"
            address_label = "地址 / 扫码验址"
            descriptor_label = t("Wallet Descriptor")
        submenu = Menu(
            self.ctx,
            [
                (web3_label, self.web3_connect_wallet),
                (xpub_label, self.public_key),
                (address_label, self.addresses_menu),
                (descriptor_label, self.wallet_descriptor),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def mnemonic_center(self):
        """Group all loaded-mnemonic tools under one Pi-style entry."""
        if kboard.is_amigo:
            backup_label = "备份 / 核对助记词\n二维码 / 钢板 / 原始熵"
            bip85_label = "BIP85 子助记词\n派生新钱包或强密码"
            secondary_label = "二次助记词\n默认规则 / 自定义还原"
            xor_label = "助记词异或\n拆分或合并助记词"
            passphrase_label = "密码短语\n添加或修改 BIP39 密码"
            customize_label = "钱包设置\n网络 / 单签多签 / 路径"
        else:
            backup_label = "备份 / 核对助记词"
            bip85_label = "BIP85 子助记词"
            secondary_label = "二次助记词"
            xor_label = t("Mnemonic XOR")
            passphrase_label = t("Passphrase")
            customize_label = t("Customize")
        submenu = Menu(
            self.ctx,
            [
                (
                    backup_label,
                    (
                        self.backup_mnemonic
                        if not Settings().security.hide_mnemonic
                        else None
                    ),
                ),
                (bip85_label, self.bip85),
                (secondary_label, self.secondary_mnemonic),
                (xor_label, self.mnemonic_xor),
                (passphrase_label, self.passphrase),
                (customize_label, self.customize),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def backup_mnemonic(self):
        """Handler for the 'Backup Mnemonic' menu item"""
        from .mnemonic_backup import MnemonicsView

        mnemonics_viewer = MnemonicsView(self.ctx)
        return mnemonics_viewer.mnemonic()

    def public_key(self):
        """Handler for the 'xpub' menu item"""
        from .pub_key_view import PubkeyView

        pubkey_viewer = PubkeyView(self.ctx)
        return pubkey_viewer.public_key()

    def wallet_descriptor(self):
        """Handler for the 'wallet descriptor' menu item"""
        from .wallet_descriptor import WalletDescriptor

        wallet_descriptor = WalletDescriptor(self.ctx)
        return wallet_descriptor.wallet()

    def passphrase(self):
        """Add or replace wallet's passphrase"""
        if not self.prompt(
            self._amigo_text(
                "添加或修改钱包密码短语？",
                t("Add or change wallet passphrase?"),
            ),
            self.ctx.display.height() // 2,
        ):
            return MENU_CONTINUE

        from ..wallet_settings import PassphraseEditor
        from ...key import Key
        from ...wallet import Wallet

        passphrase_editor = PassphraseEditor(self.ctx)
        passphrase = passphrase_editor.load_passphrase_menu(
            self.ctx.wallet.key.mnemonic
        )
        if passphrase is None:
            return MENU_CONTINUE

        self.ctx.wallet = Wallet(
            Key(
                self.ctx.wallet.key.mnemonic,
                self.ctx.wallet.key.policy_type,
                self.ctx.wallet.key.network,
                passphrase,
                self.ctx.wallet.key.account_index,
                self.ctx.wallet.key.script_type,
            )
        )
        return MENU_CONTINUE

    def customize(self):
        """Handler for the 'Customize' Wallet menu item"""
        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(
            self._amigo_text(
                "自定义钱包会生成新的密钥，并卸载当前描述符。\n"
                "助记词和密码短语会保留。",
                t(
                    "Customizing your wallet will generate a new Key and unload the Descriptor."
                )
                + " "
                + t("Mnemonic and passphrase will be kept."),
            )
        )
        if not self.prompt(self._amigo_text("继续？", t("Proceed?")), BOTTOM_PROMPT_LINE):
            return MENU_CONTINUE

        from ..wallet_settings import WalletSettings
        from ...key import Key
        from ...wallet import Wallet

        prev_key = self.ctx.wallet.key

        wallet_settings = WalletSettings(self.ctx)
        network, policy_type, script_type, account, derivation_path = (
            wallet_settings.customize_wallet(self.ctx.wallet.key)
        )
        new_key = Key(
            prev_key.mnemonic,
            policy_type,
            network,
            prev_key.passphrase,
            account,
            script_type,
            derivation_path,
        )
        if prev_key != new_key:
            self.ctx.wallet = Wallet(new_key)
        return MENU_CONTINUE

    def bip85(self):
        """Handler for the 'BIP85' menu item"""
        if not self.prompt(
            self._amigo_text("派生 BIP85 熵？", t("Derive BIP85 entropy?")),
            self.ctx.display.height() // 2,
        ):
            return MENU_CONTINUE

        from .bip85 import Bip85

        bip85 = Bip85(self.ctx)
        bip85.export()
        return MENU_CONTINUE

    def mnemonic_xor(self):
        """Handler for the 'Mnemonic XOR' menu item"""
        if not self.prompt(
            self._amigo_text(
                "要把当前助记词与另一组助记词做 XOR 吗？\n"
                "密码短语和描述符会被丢弃。",
                t(
                    "XOR current mnemonic with another one? "
                    "(passphrase and descriptor will be discarded)"
                ),
            ),
            self.ctx.display.height() // 2,
        ):
            return MENU_CONTINUE

        from .mnemonic_xor import MnemonicXOR

        mnemonic_xor = MnemonicXOR(self.ctx)
        mnemonic_xor.load_key()

        return MENU_CONTINUE

    def secondary_mnemonic(self):
        """Handler for the TP-style secondary mnemonic item."""
        from .secondary_mnemonic import SecondaryMnemonic

        secondary_mnemonic = SecondaryMnemonic(self.ctx)
        secondary_mnemonic.run()

        return MENU_CONTINUE

    def wallet(self):
        """Handler for the legacy loaded-wallet submenu."""

        submenu = Menu(
            self.ctx,
            [
                (t("Wallet Descriptor"), self.wallet_descriptor),
                (t("Passphrase"), self.passphrase),
                (t("Customize"), self.customize),
                ("BIP85", self.bip85),
                (t("Mnemonic XOR"), self.mnemonic_xor),
                ("二次助记词", self.secondary_mnemonic),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def addresses_menu(self):
        """Handler for the 'address' menu item"""
        from .addresses import Addresses

        adresses = Addresses(self.ctx)
        return adresses.addresses_menu()

    def sign(self):
        """Handler for the legacy sign submenu."""
        if kboard.is_amigo:
            submenu = Menu(
                self.ctx,
                [
                    ("交易单签名", self.sign_psbt),
                    ("消息签名", self.sign_message),
                ],
            )
        else:
            submenu = Menu(
                self.ctx,
                [
                    ("PSBT", self.sign_psbt),
                    (t("Message"), self.sign_message),
                ],
            )
        submenu.run_loop()
        return MENU_CONTINUE

    def web3_connect_wallet(self):
        """Open the Web3 wallet-connection flow."""
        from .web3_ui import Web3

        return Web3(self.ctx).connect_wallet()

    def web3_scan_and_sign(self):
        """Open the Web3 scan-and-sign flow."""
        from .web3_ui import Web3

        return Web3(self.ctx).scan_and_sign()

    def load_psbt(self):
        """Loads a PSBT from camera or SD card"""

        load_method = self.load_method()

        if load_method > LOAD_FROM_SD:
            return (None, None, "")

        if load_method == LOAD_FROM_CAMERA:
            from ..qr_capture import QRCodeCapture

            qr_capture = QRCodeCapture(self.ctx)
            data, qr_format = qr_capture.qr_capture_loop()
            return (data, qr_format, "")

        # If load_method == LOAD_FROM_SD
        from ..utils import Utils
        from ...sd_card import PSBT_FILE_EXTENSION, B64_FILE_EXTENSION

        utils = Utils(self.ctx)
        psbt_filename, _ = utils.load_file(
            [PSBT_FILE_EXTENSION, B64_FILE_EXTENSION],
            prompt=False,
            only_get_filename=True,
        )
        return (None, FORMAT_NONE, psbt_filename)

    def _sign_menu(self, signer, psbt_filename, outputs):
        if kboard.is_amigo:
            submenu = Menu(
                self.ctx,
                [
                    ("重新核对", lambda: None),
                    ("签名后显示二维码", lambda: None),
                    (
                        "签名后保存到 SD 卡",
                        None if not self.has_sd_card() else lambda: None,
                    ),
                ],
                back_status=lambda: None,
            )
        else:
            submenu = Menu(
                self.ctx,
                [
                    (t("Review Again"), lambda: None),
                    (t("Sign to QR code"), lambda: None),
                    (
                        t("Sign to SD card"),
                        None if not self.has_sd_card() else lambda: None,
                    ),
                ],
                back_status=lambda: None,
            )
        index, _ = submenu.run_loop()

        while index == 0:  # Review PSBT
            self._display_transaction_for_review(outputs)
            index, _ = submenu.run_loop()

        if index == submenu.back_index:  # Back
            return MENU_CONTINUE

        # memory management
        del outputs
        del submenu
        gc.collect()

        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(
            self._amigo_text("签名中…", t("Signing…"))
        )

        if index == 1:  # Sign to QR code
            signer.sign()
            signed_psbt, qr_format = signer.psbt_qr()

            # memory management
            del signer
            gc.collect()

            from ..utils import Utils

            utils = Utils(self.ctx)

            while True:
                self.display_qr_codes(signed_psbt, qr_format)
                utils.print_standard_qr(
                    signed_psbt,
                    qr_format,
                    self._amigo_text("已签名交易单", t("Signed PSBT")),
                    width=45,
                )
                self.ctx.display.clear()
                if self.prompt(
                    self._amigo_text("完成？", t("Done?")),
                    self.ctx.display.height() // 2,
                ):
                    return MENU_CONTINUE

        # index == 2: Sign to SD card
        signer.sign(trim=False)
        psbt_filename = self._format_psbt_file_extension(psbt_filename)
        gc.collect()

        from ...sd_card import SDHandler

        if psbt_filename and psbt_filename != ESC_KEY:
            try:
                with SDHandler() as sd:
                    if signer.is_b64_file:
                        signed_psbt, _ = signer.psbt_qr()
                        sd.write(psbt_filename, signed_psbt)
                    else:
                        with open(SDHandler.PATH_STR % psbt_filename, "wb") as f:
                            # Write PSBT data directly to the file
                            signer.psbt.write_to(f)
                    saved_text = self._amigo_text(
                        "已保存到 SD 卡:", t("Saved to SD card:")
                    )
                    self.flash_text(
                        saved_text + "\n\n%s" % psbt_filename,
                        highlight_prefix=":",
                    )
                    return MENU_CONTINUE
            except OSError:
                self.flash_error(
                    self._amigo_text("未检测到 SD 卡。", t("SD card not detected."))
                )

        return MENU_CONTINUE

    def _format_psbt_file_extension(self, psbt_filename=""):
        """Formats the PSBT filename"""
        from ...sd_card import (
            PSBT_FILE_EXTENSION,
            B64_FILE_EXTENSION,
            SIGNED_FILE_SUFFIX,
        )
        from ..file_operations import SaveFile

        if psbt_filename.endswith(B64_FILE_EXTENSION):
            # Remove chained extensions
            psbt_filename = psbt_filename[: -len(B64_FILE_EXTENSION)]
            if psbt_filename.endswith(PSBT_FILE_EXTENSION):
                psbt_filename = psbt_filename[: -len(PSBT_FILE_EXTENSION)]
            extension = PSBT_FILE_EXTENSION + B64_FILE_EXTENSION
        else:
            extension = PSBT_FILE_EXTENSION

        save_page = SaveFile(self.ctx)
        psbt_filename = save_page.set_filename(
            psbt_filename,
            "QRCode",
            SIGNED_FILE_SUFFIX,
            extension,
        )
        return psbt_filename

    def _pre_load_psbt_warn(self):
        """Warns if descriptor is not loaded and wallet is multisig or miniscript"""
        if (
            not self.ctx.wallet.is_loaded()
            and self.ctx.wallet.key.policy_type != TYPE_SINGLESIG
        ):
            if kboard.is_amigo:
                warning_text = (
                    "警告: 钱包输出描述符未找到。\n\n"
                    "部分检查无法执行。"
                )
            else:
                warning_text = (
                    t("Warning:")
                    + " "
                    + t("Wallet output descriptor not found.")
                    + "\n\n"
                    + t("Some checks cannot be performed.")
                )
            self.ctx.display.draw_centered_text(
                warning_text,
                highlight_prefix=":",
            )
            return self.prompt(self._amigo_text("继续？", t("Proceed?")), BOTTOM_PROMPT_LINE)

        return True

    def _post_load_psbt_warn(self, signer):
        """Warns cases of incorrect / missing PSBT info"""
        # Warns in case of path mismatch
        path_mismatch = signer.path_mismatch()
        if path_mismatch:
            self.ctx.display.clear()
            if kboard.is_amigo:
                warning_text = (
                    "警告: 路径不匹配\n"
                    "钱包: "
                    + self.ctx.wallet.key.derivation_str()
                    + "\n"
                    + "PSBT: "
                    + path_mismatch
                )
            else:
                warning_text = (
                    t("Warning:")
                    + " "
                    + t("Path mismatch")
                    + "\n"
                    + "Wallet: "
                    + self.ctx.wallet.key.derivation_str()
                    + "\n"
                    + "PSBT: "
                    + path_mismatch
                )
            self.ctx.display.draw_centered_text(
                warning_text,
                highlight_prefix=":",
            )
            if not self.prompt(self._amigo_text("继续？", t("Proceed?")), BOTTOM_PROMPT_LINE):
                return False

        # Show the policy for multisig and miniscript PSBTs
        # in case the wallet descriptor is not loaded
        if (
            not self.ctx.wallet.is_loaded()
            and not self.ctx.wallet.key.policy_type == TYPE_SINGLESIG
        ):
            policy_str = signer.psbt_policy_string()
            self.ctx.display.clear()
            self.ctx.display.draw_centered_text(policy_str)
            if not self.prompt(
                self._amigo_text("继续？", t("Proceed?")),
                BOTTOM_PROMPT_LINE,
            ):
                return False

        # Fix zero fingerprint, it is necessary for the signing process on embit in a few cases
        if (
            self.ctx.wallet.key.fingerprint != b"\x00\x00\x00\x00"
            and signer.fill_zero_fingerprint()
        ):
            self.ctx.display.clear()
            self.ctx.display.draw_centered_text(
                self._amigo_text(
                    "交易单中未设置指纹", t("Fingerprint unset in PSBT")
                )
            )
            if not self.prompt(self._amigo_text("继续？", t("Proceed?")), BOTTOM_PROMPT_LINE):
                return False

        return True

    def _fees_psbt_warn(self, fee_percent):
        """Warn if fees greater than 10% of what is spent"""
        if fee_percent >= 10.0:
            self.ctx.display.clear()
            if kboard.is_amigo:
                fee_text = (
                    "警告: 费用过高\n"
                    + replace_decimal_separator(("%.1f" % fee_percent))
                    + "% 的金额。"
                )
            else:
                fee_text = (
                    t("Warning:")
                    + " "
                    + t("High fees!")
                    + "\n"
                    + replace_decimal_separator(("%.1f" % fee_percent))
                    + t("% of the amount.")
                )
            self.ctx.display.draw_centered_text(
                fee_text,
                highlight_prefix=":",
            )

            return self.prompt(self._amigo_text("继续？", t("Proceed?")), BOTTOM_PROMPT_LINE)

        return True

    def _display_transaction_for_review(self, outputs):
        """Display all transaction info on screen for verification"""
        from ..utils import Utils

        utils = Utils(self.ctx)

        # display summary (doesn't have addresses)
        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(outputs[0], highlight_prefix=":")
        self.ctx.input.wait_for_button()

        # display Inputs, Self-transfer and Change (have addresses)
        for message in outputs[1:]:
            self.ctx.display.clear()
            self.ctx.display.draw_centered_text(message, highlight_prefix=":")

            # highlight addresses
            lines = self.ctx.display.to_lines(message)
            y_offset = self.ctx.display.get_center_offset_y(len(lines))
            highlight = True
            count_empty = 0
            for i, line in enumerate(lines):
                if len(line) > 0:
                    if count_empty == 1:
                        x_offset = self.ctx.display.get_center_offset_x(line)
                        highlight = utils.display_addr_highlighted(
                            y_offset, x_offset, line, i, highlight
                        )
                else:
                    count_empty += 1

            self.ctx.input.wait_for_button()

    def sign_psbt(self):
        """Handler for the 'sign psbt' menu item"""

        # pre load warns
        if not self._pre_load_psbt_warn():
            return MENU_CONTINUE

        # Load a PSBT
        data, qr_format, psbt_filename = self.load_psbt()

        if data is None and psbt_filename == "":
            # Both the camera and the file on SD card failed!
            self.flash_error(self._amigo_text("加载失败", t("Failed to load")))
            return MENU_CONTINUE

        # DISABLED to avoid false "Decrypt?" on normal PSBTs as KEF
        # try:
        #     from ..encryption_ui import decrypt_kef
        #
        #     data = decrypt_kef(self.ctx, data)
        # except KeyError:
        #     self.flash_error(t("Failed to decrypt"))
        #     return MENU_CONTINUE
        # except ValueError:
        #     # ValueError=not KEF or declined to decrypt
        #     pass

        # PSBT read OK! Will try to sign
        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(
            self._amigo_text("加载中…", t("Loading…"))
        )

        qr_format = FORMAT_PMOFN if qr_format == FORMAT_NONE else qr_format
        from ...psbt import PSBTSigner

        signer = PSBTSigner(self.ctx.wallet, data, qr_format, psbt_filename)

        # memory management
        del data
        gc.collect()

        # post load warns
        if not self._post_load_psbt_warn(signer):
            return MENU_CONTINUE

        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(
            self._amigo_text("处理中…", t("Processing…"))
        )
        outputs, fee_percent = signer.outputs()

        if not self._fees_psbt_warn(fee_percent):
            return MENU_CONTINUE

        self._display_transaction_for_review(outputs)

        # sign menu
        return self._sign_menu(signer, psbt_filename, outputs)

    def sign_message(self):
        """Handler for the 'sign message' menu item"""
        from .sign_message_ui import SignMessage

        message_signer = SignMessage(self.ctx)
        return message_signer.sign_message()

    def web3(self):
        """Handler for the 'chain' menu item"""
        from .web3_ui import Web3

        web3_page = Web3(self.ctx)
        return web3_page.web3()

    def self_check(self):
        """Handler for the self-check menu item"""
        from ..self_check import SelfCheck

        return SelfCheck(self.ctx).self_check()
