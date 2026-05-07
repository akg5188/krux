# Amigo Commercial Release Notes

This page is for future maintainers, release packaging, shipping, and support. The goal is to turn the `Sipeed Matrix Amigo` build into a shippable, verifiable, and maintainable product release.

## What this release includes

- Chinese UI and Chinese newcomer entry points
- Amigo large-button touchscreen home layout
- Mnemonic creation, import, backup, and recovery
- BTC / PSBT / xpub / wallet descriptor features
- Web3 / TP / EVM wallet connection and signing
- Firmware self-check, touch test, SD card check, and device tests
- TTL serial thermal printer support
- 15 / 18 / 21 / 24-word flows
- BIP85, steel punch numbers, mnemonic XOR, and raw entropy tools

## What this release does not include

- Smartcard mainline features
- Direct ACR39U / PC/SC / pyscard / pcscd reader support
- Android firmware delivery
- Direct USB office printer driver support

## Commercial acceptance criteria

At minimum, a shippable build should satisfy:

1. Users can reach flashing, building, FAQ, and handoff docs from the Chinese start pages
2. High-frequency pages fit the Amigo 3.5" touchscreen without relying on small-screen button layouts
3. Chinese text does not contain obvious punctuation noise or misleading translations
4. Key functional regressions pass
5. Screenshot regression can run reliably for manual review
6. Unsupported features are clearly documented as unsupported

## Validation snapshot

As of 2026-05-07:

- Continued Amigo deep-page Chinese polish and 3.5-inch touch layout cleanup, with another pass on the highest-frequency KEF, passphrase, and message-signing prompts
- Targeted regression: `PYTHONPATH=src .venv/bin/pytest -q tests/pages/test_encryption_ui.py tests/pages/home_pages/test_sign_message_ui.py tests/pages/test_wallet_settings.py tests/pages/home_pages/test_home.py tests/pages/home_pages/test_mnemonic_backup.py`
- Targeted regression result: `111 passed`
- Follow-up Chinese-first polish: `MnemonicLoader`, `Mnemonic XOR`, `BIP85`, `mnemonic backup`, and `message signing`
- Screenshot regression: `bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
- Screenshot output: `176` Chinese screenshots
- Follow-up Amigo polish: `wallet descriptor`, `address list`, and `QR viewer` menu text and touchscreen layout, plus a new `maixpy.bin` direct-flash handoff page for maintainers who only update the lower-level image
- Web3 top-level menu and wallet connection/signing flow recheck: `tests/pages/home_pages/test_web3_ui.py -q` -> `10 passed`
- Wallet descriptor / file operations follow-up: `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/home_pages/test_wallet_descriptor.py tests/pages/test_file_operations.py -q` -> `22 passed`
- Targeted regression: `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_qr_view.py tests/pages/home_pages/test_addresses.py tests/pages/home_pages/test_wallet_descriptor.py tests/pages/home_pages/test_mnemonic_backup.py -q`
- Targeted regression result: `58 passed`
- Latest combined regression: `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest -q tests/pages/test_encryption_ui.py tests/pages/test_wallet_settings.py tests/pages/home_pages/test_bip85.py tests/pages/home_pages/test_wallet_descriptor.py tests/pages/test_file_operations.py`
- Latest combined regression result: `83 passed`
- Core regression: `209 passed`
- Code hygiene: `git diff --check` passed
- Amigo firmware build: `make -C firmware/MaixPy/projects/maixpy_amigo/build -j2`
- Firmware outputs: `maixpy.bin`, `firmware.bin`, and `maixpy.elf`
- `maixpy.bin` SHA256: `04a59041f4d20dd9a6ac79d82807325c1d5db38d8ef1e787af820555722ead4b`
- Snapshot branch: `backup/amigo-snapshot`

## Handoff order

If you continue this line later, read in this order:

1. [Repository structure and handoff guide](getting-started/installing/repo-structure.zh-CN.md)
2. [Chinese newcomer entry](getting-started/index.zh-CN.md)
3. [Commercial release notes](amigo-commercial-release.en.md)
4. [FAQ](faq.en.md)
5. [Amigo migration plan / handoff record](amigo-tp-web3-port-plan.zh-CN.md)

## Maintenance principles

- Prefer touchscreen-first flows for Amigo mainline features
- Write support boundaries clearly
- Put repeated questions into FAQ and newcomer entry pages
- Keep test and screenshot paths as evidence for shipping
