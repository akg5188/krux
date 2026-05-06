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

As of 2026-05-06:

- Screenshot regression: `bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
- Screenshot output: `173` Chinese screenshots
- Core regression: `209 passed`
- Code hygiene: `git diff --check` passed
- Snapshot branch: `backup/amigo-snapshot`

## Handoff order

If you continue this line later, read in this order:

1. [Repository structure and handoff guide](getting-started/installing/repo-structure.zh-CN.md)
2. [Chinese newcomer entry](getting-started/index.en.md)
3. [Commercial release notes](amigo-commercial-release.en.md)
4. [FAQ](faq.en.md)
5. [Amigo migration plan / handoff record](amigo-tp-web3-port-plan.zh-CN.md)

## Maintenance principles

- Prefer touchscreen-first flows for Amigo mainline features
- Write support boundaries clearly
- Put repeated questions into FAQ and newcomer entry pages
- Keep test and screenshot paths as evidence for shipping
