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
from .display import display, Display
from .input import Input
from .camera import Camera
from .light import Light
from .kboard import kboard


class Context:
    """Context is a singleton containing all 'global' state that lives throughout the
    duration of the program, including references to all device interfaces.
    """

    def __init__(self):
        self.display = display  # type: Display
        self.input = Input()  # type: Input
        self.camera = Camera()  # type: Camera
        self.light = Light() if kboard.has_light else None
        self.power_manager = None
        self.wallet = None
        self.wallet_slots = []
        self.wallet_secrets = {}
        self.tc_code_enabled = False

    def clear(self):
        """Clears all sensitive data from the context, resetting it"""
        self.wallet = None
        self.wallet_slots = []
        self.wallet_secrets = {}
        gc.collect()

    def is_logged_in(self):
        """Returns True if user is logged-in with private key material"""
        return bool(self.wallet is not None and self.wallet.key)

    def _wallet_secret_id(self, wallet):
        """Return a stable in-memory key for the current wallet secret."""
        try:
            return wallet.key.fingerprint_hex_str(False)
        except Exception:
            return None

    def remember_wallet(self, wallet, mnemonic=None, passphrase=None):
        """Keep an in-memory wallet slot for SeedSigner-style seed switching."""
        if wallet is None or wallet.key is None:
            return
        secret_id = self._wallet_secret_id(wallet)
        if secret_id:
            if mnemonic is None:
                mnemonic = getattr(wallet.key, "mnemonic", None)
            if passphrase is None:
                passphrase = getattr(wallet.key, "passphrase", None)
            if mnemonic:
                self.wallet_secrets[secret_id] = (mnemonic, passphrase or "")
        for index, saved_wallet in enumerate(self.wallet_slots):
            saved_id = self._wallet_secret_id(saved_wallet)
            if (secret_id and saved_id == secret_id) or saved_wallet.key == wallet.key:
                self.wallet_slots[index] = wallet
                return
        self.wallet_slots.append(wallet)

    def secret_for_wallet(self, wallet):
        """Return the RAM-only mnemonic/passphrase tuple for a wallet, if present."""
        secret_id = self._wallet_secret_id(wallet)
        if not secret_id:
            return None, None
        return self.wallet_secrets.get(secret_id, (None, None))


ctx = Context()  # Singleton instance
