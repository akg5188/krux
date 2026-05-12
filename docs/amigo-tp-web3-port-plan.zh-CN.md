# Sipeed Matrix Amigo 的 TP / Web3 迁移计划

这份文档记录把 `satochip-signer` 里的 TP / Web3 / 连接钱包 / 签名请求能力，迁移到 `krux` 的 Amigo 目标上的执行计划。

## 2026-05-12 06:35 原厂救机尝试状态

- 当前优先级：先把 Amigo 救活，能刷回原厂/官方可启动固件后，再刷本仓库定制固件。
- 用户更换 USB 口后，电脑重新识别到 `0403:6010 Future Technology Devices International FT2232C/D/H Dual UART/FIFO IC`，并出现双串口：
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0 -> ../../ttyUSB0`
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 -> ../../ttyUSB1`
- 本轮目标救机文件：
  `build/sipeed-official/maixpy_v0.6.3_2_gd8901fd22_amigo_tft_defaults.bin`
  SHA256：`e3e15ea8dacff49751405f94215c1252653343f47823fba781990279b6473d56`
- 已尝试 `ktool.py`：
  `kd233/goE` + `if01/if00`，低速 `115200`，未出现 `ROM ISP detected`。
- 已尝试 `kflash_py`：
  `kd233/goE/dan/goD` + `/dev/ttyUSB1`、`/dev/ttyUSB0`，低速 `115200`，均停在 `Greeting fail`。
- 已尝试无复位 ROM ISP greeting：`/dev/ttyUSB1` 只返回 `0x00`，`/dev/ttyUSB0` 无响应，不是有效 K210 ROM ISP 响应。
- 结论：电脑能看到 USB 转双串口，但 K210 没有进入下载模式；截至本记录，没有成功写入、擦除或覆盖 Flash。
- 下一步救机办法：必须让 K210 在 `IO16/BOOT` 低电平时复位，进入 ROM ISP。由于用户的部分实体按键已损坏，可能需要打开后盖，用镊子短接 `BOOT/IO16` 到 `GND`，保持短接时重新插入底部 USB-C 数据口或触发 RESET；电脑端看到双串口后再执行原厂刷入命令。

如果你是以后接手的人，建议先按这个顺序看：

1. [Krux 仓库结构与接手说明](getting-started/installing/repo-structure.zh-CN.md)
2. [Amigo 中文新手入口](getting-started/index.zh-CN.md)
3. 本页
4. [Amigo 固定快照重编译教程](getting-started/installing/from-github-snapshot.zh-CN.md)
5. [Amigo 固件从源码编译并烧录](getting-started/installing/from-source.zh-CN.md)

当前这轮能直接接手的最新快照分支是 `amigo-snapshot`，如果你是从备份仓库接手，请优先看这个分支。

## 目标

- 在 Amigo 上保留 `krux` 现有的比特币功能。
- 增加一条面向 EVM / Web3 的软件签名路径。
- 按 Amigo 的 3.5 寸触摸屏重新整理按钮、菜单和信息排版。
- 让桌面模拟器先跑通，再进入 Amigo 固件构建。
- 生成可截图、可复核的中间结果，方便确认 UI 和流程。

## 设备前提

- 目标硬件：`Sipeed Matrix Amigo`
- 交互前提：这是 `3.5` 寸触摸屏设备，不应该按树莓派的小屏按键布局硬搬
- 当前方向：优先把树莓派功能迁成更适合 Amigo 触摸屏的大按钮、大字距、少层级流程
- 驱动结论：
  - Amigo 的屏幕、触摸、相机、SD 卡属于 Krux 已支持的设备能力
  - 树莓派使用的 `ACR39U / PC/SC / pyscard / pcscd` 智能卡读卡器链路，当前 Amigo 固件没有对应驱动
  - Amigo 当前不能按树莓派方式直接插 USB 智能卡读卡器工作
  - 用户已决定 Amigo 固件不要智能卡功能，当前主线不再做智能卡桥接菜单
  - 如果必须做到 Amigo 直连智能卡，需要另开硬件驱动适配：确认 USB Host 或可用串口/I2C/SPI 读卡模块、移植 CCID/T=0/T=1/APDU 层、再接 Satochip / SeedKeeper 协议

## 这次先做的功能

1. Web3 钱包连接二维码
1. TP / Web3 签名请求解析
1. EVM 地址派生
1. EIP-191 `personal_sign`
1. EIP-712 typed data 签名
1. 兼容 TokenPocket 风格的 `tp:` 请求
1. 兼容 `ur:eth-sign-request` 请求

## 当前进度

- 2026-05-12 06:14 早晨第二次自动刷机尝试仍未写入：用户再次重新插上后，电脑成功识别 `0403:6010 Future Technology Devices International FT2232C/D/H Dual UART/FIFO IC`，固定串口为 `usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0 -> ../../ttyUSB0` 和 `usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 -> ../../ttyUSB1`。自动脚本先校验 `00:40` 最新包哈希：Kboot 包 `37292f7919bb1a5dcc8a48045234b6605bb9dfb2b781f4a7d21af3f04c10a4e5`，raw 固件 `c816886788e8e48e48216ab845c01c4c4e81a02138f3c8aee21de814d746360f`；随后释放 DTR/RTS 控制线，并依次尝试 `kd233 + if01`、`kd233 + if00`、`goE + if01`、自动板型 + `if01`。所有尝试均停在 `Trying to Enter K210 ROM ISP Mode...` 后的 `Greeting fail, check serial port (SLIP receive timeout (wait frame start))`，没有出现 `ROM ISP detected`，因此没有写入 Flash。最后已再次释放 `if00/if01/ttyUSB0/ttyUSB1` 的 DTR/RTS 控制线。日志文件：`build/amigo-auto-flash-20260512-061342.log`。判断：电脑能看到 USB 双串口，但 K210 没有被拉进 ROM ISP；按键已坏时，需要修复/短接 `BOOT/IO16 -> GND` 后上电，或找到可用 BOOT/RST 焊盘进入救砖模式，再刷当前 Kboot 包。
- 2026-05-12 06:05 早晨自动刷机尝试未执行写入：用户表示已重新插上并要求全自动处理。电脑端先校验 `00:40` 最新修复包，Kboot 包 SHA256 仍为 `37292f7919bb1a5dcc8a48045234b6605bb9dfb2b781f4a7d21af3f04c10a4e5`，raw 固件 SHA256 仍为 `c816886788e8e48e48216ab845c01c4c4e81a02138f3c8aee21de814d746360f`。随后等待固定串口 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 共 `180s`，结果 `NO_SIPEED_SERIAL_AFTER_180S`；`lsusb` 未出现 `0403:6010 Future Technology Devices International FT2232C/D/H Dual UART/FIFO IC`；`/dev/serial/by-id`、`/dev/ttyUSB0`、`/dev/ttyUSB1`、`/dev/ttyACM0`、`/dev/ttyACM1` 均不存在。因此本轮没有执行 ktool 刷机命令，Flash 没有被写入。判断：当前线/接口/板子状态没有枚举出刷机用 Sipeed 双串口，可能插在供电口、数据线不通、USB 口接触不稳，或按键/BOOT/RESET 损坏导致板子状态异常。下一步必须先让电脑看到 `Sipeed USB to Dual Uart` 双串口，若按键坏且仍无法进入 K210 ROM ISP，需要用 `BOOT/IO16 -> GND` 短接救砖方式上电后再刷。
- 2026-05-12 00:40 本轮真机反馈修复已完成源码、测试和低负载编译，但当前电脑未检测到 Amigo 串口，所以尚未刷机。修复内容：`src/krux/web3.py` 新增 `_json_dumps_compact()`，统一替换 Web3 主线里直接调用 `json.dumps(..., ensure_ascii=False, separators=...)` 的位置，避免 Amigo MicroPython `ujson` 抛 `TypeError("function doesn't take keyword arguments")` 导致链上签名失败；`src/krux/context.py` 新增 RAM-only `wallet_secrets`，导入助记词后只在本次开机会话内按钱包指纹保存助记词/密码短语，不写 Flash/SD；`src/krux/pages/login.py` 在清空 `key.mnemonic/key.passphrase` 前把明文交给 `Context.remember_wallet()`；`src/krux/pages/boot_lock.py` 新增 `verify_before_secret_access()`，助记词明文相关功能要求先设置开机口令并输入 PIN，错 3 次返回 `MENU_SHUTDOWN`；`src/krux/pages/home_pages/home.py` 将备份助记词、BIP85、二次助记词、助记词异或、密码短语、钱包设置改为 PIN 门禁入口，PIN 通过后临时恢复助记词明文，退出功能后再次清空，并临时关闭 `hide_mnemonic` 让 BIP85/备份页面真正显示内容；`src/krux/pages/home_pages/addresses.py` 的任意派生地址预览已显示 BTC 地址类型：`Legacy P2PKH / Nested SegWit P2SH-P2WPKH / Native SegWit P2WPKH / Taproot P2TR`，以及主网/测试网，EVM 显示 `EVM 以太坊地址`；SeedSigner 菜单文案由 `派生地址查看\n输入任意路径` 缩短为 `任意路径\nBTC/EVM 地址`，避免 Amigo 上“任意”的字被截掉。轻量验证：`py_compile` 通过；定向回归 `87 passed in 9.75s`，覆盖 Web3、菜单、派生地址、BootLock、登录无状态；`git diff --check` 通过。低负载编译命令：`timeout 25m env MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 19 firmware/scripts/build-amigo-official-base.sh --official-shell`，构建成功，MaixPy 耗时约 `91.65s`。输出 raw 固件 `build/amigo-official-base-firmware.bin` 大小 `1672896 bytes`，SHA256 `c816886788e8e48e48216ab845c01c4c4e81a02138f3c8aee21de814d746360f`；输出官方壳 Kboot 包 `build/amigo-official-base-official-shell-kboot.kfpkg` 大小 `874895 bytes`，SHA256 `37292f7919bb1a5dcc8a48045234b6605bb9dfb2b781f4a7d21af3f04c10a4e5`。`unzip -l` 确认包内仍是官方壳 5 文件，包内 `firmware.bin` 为 `1672896 bytes`。当前 `/dev/serial/by-id` 不存在，未执行刷机。下一步：用户重新插上 Amigo 并出现固定串口 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 后，使用 `-B kd233` 刷入当前 Kboot 包。
- 2026-05-11 23:54 签名前 PIN 保护版已真机刷入成功：用户重新插上 Amigo 后，电脑识别固定串口 `usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0 -> ../../ttyUSB0` 和 `usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 -> ../../ttyUSB1`。刷入包为 `build/amigo-official-base-official-shell-kboot.kfpkg`，SHA256 `b60d66ce9becb1c8f2a7d79e3f59bc799c7c4a998626042a7fb7ded3629ff8da`；raw 固件 SHA256 `c24474a8d7873185d8882f7f92c3a4b09de33ad08c567f89d75537efa869c43a`。刷机命令：`printf '[sudo-password]\n' | sudo -S -p '' timeout 8m nice -n 19 python3 firmware/Kboot/build/ktool.py -B kd233 -b 115200 -p /dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 build/amigo-official-base-official-shell-kboot.kfpkg`。Ktool 成功进入 K210 ROM ISP，Flash ID `0xEF6018`，容量 `16 MB`；`bootloader_lo.bin`、`bootloader_hi.bin`、两个 `config.bin` 写入完成；主固件写入结果：`Flashed 1669861 B [26 chunks of 65536B] (00080000~0021FFFF) in 164.784s`，最后显示 `Rebooting...`，退出码 `0`。刷后固定串口仍存在。请真机重点验证：开机显示是否正常；设置里开启/修改 `开机口令锁` 后，BTC PSBT、BTC 消息和 Web3/TP 链上签名是否在真正签名前要求输入 PIN；连续输错 3 次是否自动进入关机流程；连接钱包、查看地址、导出 xpub 是否不额外要求 PIN。
- 2026-05-11 23:34 签名前 PIN 保护版已完成低负载编译但未刷机：命令 `timeout 25m env MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 19 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功退出，MaixPy 构建耗时约 `89.75s`。输出 raw 固件 `build/amigo-official-base-firmware.bin` 大小 `1669824 bytes`，SHA256 `c24474a8d7873185d8882f7f92c3a4b09de33ad08c567f89d75537efa869c43a`；输出官方壳 Kboot 包 `build/amigo-official-base-official-shell-kboot.kfpkg` 大小 `873579 bytes`，SHA256 `b60d66ce9becb1c8f2a7d79e3f59bc799c7c4a998626042a7fb7ded3629ff8da`。`unzip -l` 校验包内仍是官方壳 5 文件：`flash-list.json / bootloader_lo.bin / bootloader_hi.bin / config.bin / firmware.bin`，包内 `firmware.bin` 为 `1669824 bytes`。当前电脑未检测到固定串口 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`，等待 `60s` 结果 `NO_SIPEED_SERIAL_AFTER_60S`，`/dev/ttyUSB*`、`/dev/ttyACM*` 不存在，`lsusb` 也没有 Sipeed USB 双串口；因此没有执行刷机，避免误刷。下一步：用户重新插上 Amigo，电脑出现固定串口后，使用 `-B kd233` 刷入当前 Kboot 包。
- 2026-05-11 签名前 PIN 保护已补齐：复用现有 `开机口令锁` 作为签名前验证口令。未设置开机口令时，签名流程保持原样；设置口令后，连接钱包、查看地址、导出 xpub、查看派生地址不要求输入口令，但 BTC PSBT 签名、BTC 消息签名和 Web3/TP 链上签名会在用户确认请求后、真正执行签名前要求输入口令。签名前验证最多允许 `3` 次错误，连续输错后显示 `口令错误 3 次\n设备即将关机` 并返回 `MENU_SHUTDOWN`，由现有菜单/页面流程执行关机。实现位置：`src/krux/pages/boot_lock.py` 新增 `BOOT_LOCK_SIGN_ATTEMPTS = 3` 和 `verify_before_signing()`；`src/krux/pages/home_pages/home.py` 接入 PSBT 签名；`src/krux/pages/home_pages/sign_message_ui.py` 接入 BTC 消息签名；`src/krux/pages/home_pages/web3_ui.py` 接入 Web3 签名。轻量验证已通过：`tests/pages/test_boot_lock.py` 结果 `8 passed in 2.25s`；`git diff --check` 覆盖本轮相关文件通过。
- 2026-05-11 无状态安全模式收敛：用户明确不要显示私钥，也不要把助记词加密保存在机器里；目标改为“内部 Flash 固件启动，助记词只在本次开机会话使用，关机/断电后消失”。硬件判断：Matrix Amigo/K210 不能像树莓派那样从 SD 卡启动完整系统，SD 卡只能作为临时文件/升级介质，正式固件仍从内部 SPI Flash 启动。源码处理：`src/krux/pages/home_pages/addresses.py` 已移除“显示私钥/高级危险功能”入口，派生地址流程只显示类型、路径、文字地址和地址二维码；`src/krux/pages/mnemonic_loader.py` 在 Amigo 上隐藏“从已保存记录加载”；`src/krux/pages/encryption_ui.py` 在 Amigo 上不再提供“保存到闪存/保存到 SD 卡”的加密助记词存储入口，只保留加密二维码备份；`src/krux/krux_settings.py` 将 Amigo 默认 `hide_mnemonic` 设为 `True`；`src/krux/key.py` 新增 `forget_plaintext_secret()`；`src/krux/pages/login.py` 在 Amigo 加载钱包后调用该方法清空 `key.mnemonic` 和 `key.passphrase` 明文字符串并 `gc.collect()`。功能边界：签名、派生地址、xpub、Web3 仍通过内存中的 HD 根私钥对象工作；需要改密码短语、切换钱包策略、做二次助记词/XOR/明文备份时，需要重新导入助记词并在加载确认阶段完成，默认加载后的会话不再保留明文助记词文本。创建新助记词例外：Amigo 保留 `新助记词/创建钱包` 入口，按 BIP39 标准生成后只显示一次让用户离线抄写备份，确认加载后同样清空明文字符串。轻量验证已通过：`py_compile` 覆盖无状态相关文件；`pytest -q tests/pages/test_login.py::test_amigo_load_key_menu_is_stateless tests/pages/test_login.py::test_load_key_from_text_on_amigo_tft_with_touch tests/pages/test_encryption_ui.py::test_amigo_encrypt_menu_does_not_offer_storage` 结果 `3 passed in 0.50s`；后续新增创建钱包回归 `pytest -q tests/pages/test_login.py::test_amigo_new_mnemonic_entry_stays_enabled tests/pages/test_login.py::test_amigo_new_mnemonic_is_shown_once_then_forgotten tests/pages/test_login.py::test_load_key_from_text_on_amigo_tft_with_touch` 结果 `3 passed in 0.61s`。
- 2026-05-11 21:58 本轮修复包已真机刷入成功：用户重新插上 Amigo 后，电脑识别固定串口 `usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0 -> ../../ttyUSB0` 和 `usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 -> ../../ttyUSB1`。刷入包为 `build/amigo-official-base-official-shell-kboot.kfpkg`，SHA256 `329c9e3fcaac4f7a852d645f92d195dec9cc977150dff7654eb57f569282bba1`；raw 固件 SHA256 `7bd36a4bb043a54809f68b8f62d5d352ba135cc9656eae5e01ab552c2ac7dbc2`。刷机命令：`printf '[sudo-password]\\n' | sudo -S -p '' timeout 8m nice -n 19 python3 firmware/Kboot/build/ktool.py -B kd233 -b 115200 -p /dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 build/amigo-official-base-official-shell-kboot.kfpkg`。Ktool 成功进入 K210 ROM ISP，Flash ID `0xEF6018`，容量 `16 MB`；`bootloader_lo.bin`、`bootloader_hi.bin`、两个 `config.bin` 写入完成；主固件写入结果：`Flashed 1666533 B [26 chunks of 65536B] (00080000~0021FFFF) in 164.804s`，最后显示 `Rebooting...`，退出码 `0`。刷后固定串口仍存在。请真机重点验证：显示是否正常；首页/登录顶层是否不再出现 `开机密码`，设置安全里是否有 `开机密码 设置/修改`；`SeedSigner -> 助记词工具 -> 派生地址查看` 是否显示 `输入任意路径`，BTC/EVM 路径是否能出地址二维码；链上签名是否还报 `中转二维码解压失败`。
- 2026-05-11 21:46 本轮修复包已完成低负载编译但未刷机：命令 `timeout 25m env MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 19 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功退出，耗时约 `106.14s`。输出 raw 固件 `build/amigo-official-base-firmware.bin` 大小 `1666496 bytes`，SHA256 `7bd36a4bb043a54809f68b8f62d5d352ba135cc9656eae5e01ab552c2ac7dbc2`；输出官方壳 Kboot 包 `build/amigo-official-base-official-shell-kboot.kfpkg` 大小约 `852K`，SHA256 `329c9e3fcaac4f7a852d645f92d195dec9cc977150dff7654eb57f569282bba1`。`unzip -l` 校验包内 5 文件完整：`flash-list.json / bootloader_lo.bin / bootloader_hi.bin / config.bin / firmware.bin`，包内 `firmware.bin` 为 `1666496 bytes`。当前电脑没有 `/dev/serial/by-id`，`/dev/ttyUSB*`、`/dev/ttyACM*` 不存在，`lsusb` 也没有 Sipeed USB 双串口，因此未刷机，避免误刷。下一步：用户重新插上 Amigo，电脑出现固定串口 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 后，用 `-B kd233` 刷这个新包。
- 2026-05-11 21:42 本轮用户反馈修复已完成源码和低负载回归，尚未重新编译/刷机，旧 `21:25` 包已不包含本轮修复，不能继续刷旧包。处理范围：`src/krux/web3.py` 增强 `tpr1:/w3r1:` 中转二维码解包，新增多轮 URL 解码、URL 编码 Base64、Base64 内部 URL 编码文本、gzip/zlib/raw deflate 解析顺序，并用 `derive_web3_address()` 按完整 EVM 地址路径签名，避免请求使用 `m/44h/60h/0h/0/1` 等非默认地址时仍按 `/0/0` 校验；`src/krux/pages/login.py` 和 `src/krux/pages/home_pages/home.py` 删除顶层 `开机密码` 入口，只保留 `设置 -> 安全 -> 开机密码\n设置/修改`；`SeedSigner -> 助记词工具 -> 派生地址查看` 改为 `派生地址查看\n输入任意路径`，进入后可从当前 BTC 路径或 EVM 默认路径开始手动编辑完整路径，支持 BTC `44/49/84/86` 和 EVM `m/44h/60h/...` 地址二维码。新增/更新测试：`tests/test_web3.py` 覆盖完整 EVM 派生路径签名、URL 编码 Base64 中转包、Base64 内 URL 编码文本中转包；`tests/pages/home_pages/test_addresses.py` 覆盖 BTC 任意路径和 EVM 默认地址 `0x9858EfFD232B4033E47d90003D41EC34EcaEda94`；菜单测试同步确认顶层不再出现 `开机密码`。验证命令：`timeout 60s nice -n 19 .venv/bin/python -m py_compile ...` 通过；关键专项 `10 passed in 0.43s`；低负载回归 `timeout 240s env PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src nice -n 19 .venv/bin/python -m pytest -q tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/home_pages/test_addresses.py tests/pages/test_self_check.py` 结果 `74 passed in 11.26s`；`timeout 30s git diff --check -- src/krux tests docs/amigo-tp-web3-port-plan.zh-CN.md` 通过。下一步若要上真机：用低负载单任务重新编译 `timeout 25m env MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 19 firmware/scripts/build-amigo-official-base.sh --official-shell`，再用固定串口和 `-B kd233` 刷新包。
- 2026-05-11 21:25 新反馈修复版真机刷入成功：用户重新插入 Amigo 后，电脑识别到固定串口 `usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 -> ../../ttyUSB1` 和 `if00 -> ../../ttyUSB0`。第一次用 `-B goE` 进入 ROM ISP 超时，没有写入；随后测试板型时 `-B kd233` 成功进入 ROM ISP，但探测命令的 `20s` timeout 在主固件写入约 `3.8%` 后中断。已立即使用 `-B kd233` 重新完整刷入同一个新包，覆盖前一次中断写入。最终刷入命令：`printf '518998\n' | sudo -S -p '' timeout 8m nice -n 19 python3 firmware/Kboot/build/ktool.py -B kd233 -b 115200 -p /dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 build/amigo-official-base-official-shell-kboot.kfpkg`。Ktool 检测到 ROM ISP，Flash ID `0xEF6018`，容量 `16 MB`；`bootloader_lo.bin`、`bootloader_hi.bin`、两个 `config.bin` 均写入完成；主固件写入结果：`Flashed 1662437 B [26 chunks of 65536B] (00080000~0021FFFF) in 164.931s`，最后 `Rebooting...`，退出码 `0`。刷入包 SHA256 `5bda9e662147cd07b01bf96ea10d20f0c5336b26559dd454b654b19638b42f96`，raw 固件 SHA256 `57e38481e97678f669ab7ce54aa00a8db7285d9691ebb53b12f0ca70d073f01c`。刷后固定串口仍存在。下一步请用户真机确认：显示是否正常、首页是否为 `开机密码`、`SeedSigner -> 助记词工具 -> 派生地址查看` 是否可见、Web3 签名是否不再报 `无法识别的链上请求`。
- 2026-05-11 21:15 新反馈修复版已完成低负载编译但未刷机：本轮包含 `开机密码` 文案、`SeedSigner -> 助记词工具 -> 派生地址查看`、Web3 原始中转 JSON / URL 编码 TP / Ethereum JSON-RPC 解析增强，以及 Amigo 点阵备份双层列标。编译命令：`timeout 25m env MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 19 firmware/scripts/build-amigo-official-base.sh --official-shell`。构建成功，耗时约 `103.31s`；raw 固件 `build/amigo-official-base-firmware.bin` 大小 `1662400 bytes`，SHA256 `57e38481e97678f669ab7ce54aa00a8db7285d9691ebb53b12f0ca70d073f01c`；Kboot 包 `build/amigo-official-base-official-shell-kboot.kfpkg` 大小 `869972 bytes`，SHA256 `5bda9e662147cd07b01bf96ea10d20f0c5336b26559dd454b654b19638b42f96`。`unzip -l` 校验包内 5 文件完整：`flash-list.json / bootloader_lo.bin / bootloader_hi.bin / config.bin / firmware.bin`，包内 `firmware.bin` 为 `1662400 bytes`。`strings` 可见 `JSON-RPC` 和 `SeedSigner`，说明新 Web3 解析和入口字符串已进入固件。刷机状态：已等待固定串口 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 约 90 秒，电脑未检测到 Sipeed 串口，因此没有刷机，避免误刷。下一步：用户重新插上 Amigo 并出现固定串口后，直接刷此 Kboot 包，不需要重新编译。
- 2026-05-11 当前反馈补齐：用户确认还需要三项一起处理：`密码` 文案改成 `开机密码`、Web3 签名不再轻易报 `无法识别的链上请求`、`助记词工具` 能找到按派生编号查看钱包地址。当前源码状态：`src/krux/pages/login.py` 和 `src/krux/pages/home_pages/home.py` 的入口已统一为 `开机密码`；`SeedSigner -> 助记词工具` 已新增 `派生地址查看\n按编号显示地址`，调用 `Home.receive_address_by_index()`；`src/krux/web3.py` 已增强 `parse_scanned_web3_request()`，支持原始中转 JSON、URL 编码 TP 请求，以及常见 Ethereum JSON-RPC `personal_sign / eth_sign / eth_signTypedData / eth_sendTransaction` 请求，避免钱包扫码内容不是 `tp:` 或 `ur:` 时直接进入 `无法识别的链上请求`。新增/更新测试：`tests/pages/home_pages/test_web3_ui.py`、`tests/pages/test_self_check.py`、`tests/test_web3.py`。低负载回归结果：`py_compile` 通过；关键专项 `6 passed`；Web3/菜单/自检小范围回归 `53 passed in 1.17s`；`git diff --check` 通过。下一步如果要上真机，需要重新低负载编译并刷入 Amigo。
- 2026-05-11 点阵备份排版补充：按用户最新确认，Amigo `点阵备份` 页面顶部继续保留位权行 `1 / 2 / 4 / 8 / 16 / 32 / 64 / 128 / 256 / 512 / 1024`，并在下面新增第二行列号 `1 / 2 / 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10 / 11`，方便直接数 11 格做标记。实现位置为 `src/krux/pages/tiny_seed.py`：只对 Amigo 增加一行标签和额外顶部空间，其他机型保持原布局；对应测试为 `tests/pages/test_tiny_seed.py::test_amigo_tiny_seed_shows_bit_weights_and_column_numbers`。
- 2026-05-11 20:21 最新包真机刷入成功：用户重新插 USB 后，电脑识别到 `Sipeed USB to Dual Uart`，`if00 -> /dev/ttyUSB0`、`if01 -> /dev/ttyUSB1`。本次刷入包为 `build/amigo-official-base-official-shell-kboot.kfpkg`，SHA256 `7133d2af884252fce0619db9ea9e3d40932e8f69081b765f924553eefbcf230e`；对应 raw 固件 SHA256 `ea012fd16974091da90d604a8b928494629ea9bf9db508c08e17af64c97fc655`。刷入命令：`printf '518998\n' | sudo -S -p '' nice -n 19 python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 build/amigo-official-base-official-shell-kboot.kfpkg`。Ktool 检测到 K210 ROM ISP，Flash ID `0xEF6018`，容量 `16 MB`；bootloader 和 config 写入完成，主固件写入结果：`Flashed 1658085 B [26 chunks of 65536B] (00080000~0021FFFF) in 164.829s`，最后 `Rebooting...`，退出码 `0`。刷后固定串口仍存在。下一步请用户真机确认：显示是否清晰、触摸是否准确；重点测试 `SeedSigner -> 连接钱包` 的 TP/OKX/Rabby/MetaMask、TP 中转签名是否还报 `中转二维码解压失败`、首页是否显示 `开机密码`、`SeedSigner -> 助记词工具 -> 多助记词` 是否能加载/切换、`SeedSigner -> 助记词工具 -> 派生地址查看` 是否能按编号显示收款地址二维码。
- 2026-05-11 19:57 最新可刷包重新生成：发现 `build/` 里旧包时间为 `18:23`，早于本轮 `19:12` 之后的 Web3 中转、多助记词、按编号收款地址源码修改，所以明确禁止刷旧包。已用低负载单任务重新编译，命令为 `timeout 25m env MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 19 firmware/scripts/build-amigo-official-base.sh --official-shell`；MaixPy 主固件编译成功，最新 `firmware/MaixPy/projects/maixpy_amigo/build/firmware.bin` 为 `1658048 bytes`。打官方壳时 `/tmp/krux-official-v26.04.0/.../kboot.kfpkg` 因重启丢失，未刷旧包；随后使用仓库 `build/` 里的既有官方壳包只提取 `flash-list.json / bootloader_lo.bin / bootloader_hi.bin / config.bin`，把最新 `firmware.bin` 重新封装成 `build/amigo-official-base-official-shell-kboot.kfpkg`。最新 raw 固件 SHA256：`ea012fd16974091da90d604a8b928494629ea9bf9db508c08e17af64c97fc655`；最新 Kboot 包 SHA256：`7133d2af884252fce0619db9ea9e3d40932e8f69081b765f924553eefbcf230e`；`unzip -l` 显示官方壳 5 文件完整，包内 `firmware.bin` 为 `1658048 bytes`。`firmware/scripts/build-amigo-official-base.sh` 已补强：`--official-shell` 会优先用 `AMIGO_OFFICIAL_KBOOT`，否则尝试 `/tmp` 官方包、`build/amigo-official-shell-template.kfpkg` 和既有 official-shell 包；如果输入壳和输出包相同，会先复制临时壳再写，避免覆盖自己。当前电脑没有检测到 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`，尚未刷机。
- 2026-05-11 19:45 实机二次反馈修复：用户反馈签名仍显示 `中转二维码解压失败`，首页 `登录密码` 少字且希望改为 `登陆密码`，还需要像树莓派固件那样加载多个助记词，并能按派生编号查看收款地址。处理：`src/krux/web3.py` 的中转解码改成优先兼容固件内置 `deflate.DeflateIO`，并继续兼容 CPython `zlib`、raw deflate、gzip、纯 Base64 文本和 URL 编码纯文本，避免电脑测试可过但 Amigo 真机缺少 `zlib.decompress` 时失败；`src/krux/pages/login.py` 和 `src/krux/pages/home_pages/home.py` 的入口文字统一改为 `登陆密码`；`src/krux/context.py` 新增内存钱包槽 `wallet_slots` 和 `remember_wallet()`，加载钱包后把当前助记词放入内存槽；`SeedSigner -> 助记词工具` 新增 `多助记词`，可继续加载另一组助记词或在已加载槽之间切换，断电不保存；`SeedSigner -> 连接钱包 -> BTC 钱包连接` 新增 `按编号收款地址`，输入编号后直接按当前钱包描述符的收款分支显示对应地址二维码。保守验证：`py_compile` 覆盖关键文件通过；中转解压专项测试 `6 passed`；菜单/地址专项测试 `4 passed`；`git diff --check` 通过。注意：用户反馈电脑曾死机，本轮后续测试和编译必须使用 `timeout`、`nice -n 19` 和单任务构建，不要再跑大范围测试。
- 2026-05-11 18:55 新 Web3/TP 修复包已刷入真机：用户重新插 USB 后，电脑识别到 `Sipeed USB to Dual Uart`，`if00 -> /dev/ttyUSB0`、`if01 -> /dev/ttyUSB1`。执行固定串口刷机命令 `sudo nice -n 10 python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 build/amigo-official-base-official-shell-kboot.kfpkg` 成功。刷机结果：bootloader 和 config 写入完成；主固件写入 `Flashed 1653989 B [26 chunks of 65536B] (00080000~0021FFFF) in 164.782s`，最后显示 `Rebooting...`。刷后固定串口仍存在。请用户真机重点测试：`SeedSigner -> 连接钱包 -> TokenPocket` 是否只显示一张静态地址二维码；OKX 是否能超过旧的 `57%`；Rabby/MetaMask 是否能响应；TP 签名中转是否不再报 `中转二维码解压失败`；签名失败或取消后是否恢复竖屏；首页/登录页是否能看到 `登录密码` 入口。
- 2026-05-11 18:27 刷机前设备状态：新固件包已生成，但电脑当前没有识别到 Amigo 固定串口。检查 `/dev/serial/by-id`、`/dev/ttyUSB*`、`/dev/ttyACM*` 和 `lsusb` 均未看到 Sipeed/FTDI 双串口；自动等待固定路径 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 120 秒后结果为 `NO_SIPEED_SERIAL_AFTER_120S`，没有执行刷机命令。`dmesg` 显示 Sipeed 曾经被识别为 `Sipeed USB to Dual Uart` 并挂载到 `ttyUSB0/ttyUSB1`，但随后出现 `USB disconnect`，当前已不在系统里。下一步必须先让电脑重新识别该固定串口，再执行刷机；不要在没有固定串口时尝试刷其他设备。
- 2026-05-11 18:23 本轮 Web3/TP/Rabby/OKX/登录密码修复包已完成低负载复测和编译：Web3/二维码/登录密码回归 `81 passed`；BTC PSBT 和首页签名流程回归 `29 passed, 44 deselected`；关键文件 `py_compile` 通过；相关文件 `git diff --check` 通过。低负载编译命令 `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功，输出 `build/amigo-official-base-firmware.bin` 大小 `1653952` 字节，SHA256 `d53e708e7c266fe26ab5933bffd83e23313a152f89069854c01e99d41db1b505`；输出 `build/amigo-official-base-official-shell-kboot.kfpkg` 大小约 `846K`，SHA256 `3b3ab8352f005e56a35f8cf01f64b3c36aa7a3d88534976c6f947af549a84e90`。`unzip -l` 显示官方壳 5 文件完整：`flash-list.json / bootloader_lo.bin / bootloader_hi.bin / config.bin / firmware.bin`，包内 `firmware.bin` 为 `1653952` 字节。下一步只做固定串口刷机：`/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`，不要刷其他串口。
- 2026-05-11 Web3 钱包连接和中转签名实机修复：用户反馈 OKX 连接二维码卡在 `57%`、Rabby 扫描无反应、TP 钱包地址导入卡在 `74%`、TP 地址导入实际只需要一个静态地址二维码；签名时报 `中转二维码解压失败`，之后屏幕停在横屏；还需要在菜单里直接提供 `修改登录密码`。处理：`src/krux/web3.py` 将 UR 分片序号改为从 `1-N` 形态输出，并为多分片 UR 增加冗余轮播；OKX 连接二维码现在输出更多 fountain 帧，MetaMask/Rabby 也输出冗余帧，降低钱包只扫到部分帧时卡住的概率；TokenPocket 连接改为单张静态 EVM 地址二维码，固定助记词 `abandon ... about` 对应测试地址为 `0x9858EfFD232B4033E47d90003D41EC34EcaEda94`；中转二维码解码兼容 zlib、raw deflate、gzip 和纯 Base64 UTF-8 文本，避免安卓中转器未压缩或压缩格式不同就失败；`QRCodeCapture` 用 `try/finally` 保证扫码或解析异常后关闭摄像头并恢复竖屏，`Web3` 页面显示错误前也强制回到竖屏；登录页和加载钱包后的首页都新增 `登录密码` 入口，进入现有 `开机口令锁` 管理页，可用于开启、修改或关闭登录口令。验证：`python3 -m py_compile` 覆盖 Web3、二维码扫码、Web3 UI、登录页和首页关键文件通过；`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src nice -n 10 .venv/bin/python -m pytest -q tests/test_web3.py tests/test_qr.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py tests/pages/test_self_check.py tests/pages/test_boot_lock.py` 结果 `81 passed`。下一步：重新跑 BTC 签名回归，低负载编译 Amigo 官方壳固件，刷入固定串口后让用户真机确认 OKX/Rabby/TP、签名错误后的竖屏恢复和 `登录密码` 菜单。
- 2026-05-11 Web3 连接钱包二维码真机修复：用户实机进入 `连接钱包` 时无法显示二维码，屏幕报错 `AttributeError("'bytes' object has no attribute 'hex'")`。原因是电脑 CPython 支持 `bytes.hex()`，但 Amigo 当前 MaixPy/MicroPython 不支持该方法。处理：`src/krux/web3.py` 新增 `_bytes_hex()` 和 `_bytes_from_hex()`，Web3 模块内所有二进制十六进制转换改走 `binascii.hexlify/unhexlify`，并清掉 Web3 模块里的 `.hex()` / `bytes.fromhex()` 调用，避免 OKX、Bitget、MetaMask、Rabby、TokenPocket 不同连接分支再次触发同类错误。验证：`python3 -m py_compile src/krux/web3.py src/krux/pages/home_pages/web3_ui.py tests/test_web3.py tests/pages/home_pages/test_web3_ui.py` 通过；`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/python -m pytest -q tests/test_web3.py tests/pages/home_pages/test_web3_ui.py` 结果 `34 passed`；`git diff --check` 通过；`rg -n "\.hex\(|bytes\.fromhex|fromhex\(" src/krux` 无结果。低负载编译命令 `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功；`build/amigo-official-base-firmware.bin` 大小 `1652928` 字节，SHA256 `316124b3e85db06d34bc3d41c661a2e225be669bdf373eeae1c755ac373cb1cb`；`build/amigo-official-base-official-shell-kboot.kfpkg` 大小约 `846K`，SHA256 `ad25b22e52b00bbef3e8843e022d71bc0901cd60c1432079f1d57f4581d99796`。`unzip -l` 显示官方壳 5 文件完整，包内 `firmware.bin` 为 `1652928` 字节。当前电脑未识别到 Amigo 固定串口 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`，`/dev/ttyUSB*`、`/dev/ttyACM*` 和 `lsusb` 也没有 Sipeed/USB-UART，因此尚未刷入；等用户重新插 USB 后只刷固定 if01 串口，不要刷其他端口。
- 2026-05-11 00:18 显示修复版：用户反馈“文字显示不完整、断断续续，横线也像虚线”。处理：撤销上一轮高风险字库实验，只保留 `hextokff.py` 扫描 `src` 中中文字符，去掉 BDF x 偏移重排和中文位图加粗扩张；重新生成 Amigo 24px 字库后检查 `source_wide_chars=1088 / missing=0`；同时移除 Amigo 触摸菜单中的 1 像素浅色横向分隔线，减少真机上虚线干扰。验证：`python3 -m py_compile firmware/font/bdftohex.py firmware/font/hextokff.py src/krux/pages/__init__.py src/krux/pages/login.py src/krux/pages/home_pages/home.py` 通过；`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/python -m pytest -q tests/pages/test_self_check.py tests/pages/home_pages/test_web3_ui.py` 结果 `16 passed`；`git diff --check` 通过。低负载编译命令 `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功；`build/amigo-official-base-firmware.bin` 大小 `1654464` 字节，SHA256 `898ac47a0d36cca22c34f1c7b37d83e10da56aca6e190f20e69e199e14811f1d`；`build/amigo-official-base-official-shell-kboot.kfpkg` SHA256 `1213d5726163248e4d586aae4b544e6108718ef0ac0e69845ff051d0636349a3`，包内 `firmware.bin` 为 `1654464` 字节。已刷入固定串口 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`，Ktool 显示主固件写入 `Flashed 1654501 B [26 chunks of 65536B] (00080000~0021FFFF) in 165.185s` 并 `Rebooting...`。下一步只看用户肉眼确认：如果横画仍断，优先检查 MaixPy `font.c` 位图读取/字体 stride 或 LCD 数据宽度，不要再做字体加粗/偏移实验。
- 2026-05-11 真机显示确认后菜单命名回退：用户确认本轮显示终于正常，但反馈 `SeedSigner` 里面的功能名称和树莓派固件不同、不认识。处理：保留官方首页只增加 `SeedSigner` 一个入口，但把 `SeedSigner` 第一层菜单改回树莓派式四项：`扫码签名 / 助记词工具 / 连接钱包 / 固件自检`。细分功能放进二级菜单：`扫码签名` 里再选 BTC PSBT、比特币消息、链上扫码；`连接钱包` 里再选 BTC 钱包连接和链上钱包连接。登录前的 `SeedSigner` 也使用同样四项名称，其中 `扫码签名` 和 `连接钱包` 会先加载助记词再进入对应中心。验证：`python3 -m py_compile src/krux/pages/login.py src/krux/pages/home_pages/home.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_self_check.py` 通过；`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/python -m pytest -q tests/pages/home_pages/test_web3_ui.py tests/pages/test_self_check.py` 结果 `16 passed`。
- 2026-05-11 触摸关机入口：用户确认实体关机键已坏，需要触摸关机。处理：Amigo 未加载助记词的首页新增固定 `关机` 触摸菜单项；加载钱包后的首页最后一项也固定显示 `关机`，不再因为没有电池而显示成 `重启`。关机确认提示改为 `确认关机?`，执行提示改为 `正在关机...`。验证：`python3 -m py_compile src/krux/pages/__init__.py src/krux/pages/login.py src/krux/pages/home_pages/home.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_self_check.py` 通过；`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/python -m pytest -q tests/pages/home_pages/test_web3_ui.py tests/pages/test_self_check.py` 结果 `16 passed`。
- 2026-05-11 触摸关机版低负载构建与刷入：命令 `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功退出；`build/amigo-official-base-firmware.bin` 大小 `1652928` 字节，SHA256 `b0523613eb239392ec1c012643dae1d4e257f1f277b2d122e77ac25c570dd092`；`build/amigo-official-base-official-shell-kboot.kfpkg` 大小 `865365` 字节，SHA256 `d00f431b9b70cc7b302fd3713164d61616608908fd073301cf2adda76bd0e5ad`。`unzip -l` 显示包内仍是官方壳 5 文件：`flash-list.json / bootloader_lo.bin / bootloader_hi.bin / config.bin / firmware.bin`，其中 `firmware.bin` 为 `1652928` 字节。已固定刷入 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`，Ktool 显示主固件写入 `Flashed 1652965 B [26 chunks of 65536B] (00080000~0021FFFF) in 165.036s` 并 `Rebooting...`；不要把这条记录对应的固件和旧的乱码/断字版本混用。
- 2026-05-10 晚间菜单补强：用户反馈在功能入口里找不到原树莓派的签名和连接钱包功能。本轮把 Amigo 顶层新增入口统一命名为 `SeedSigner`，并把 `SeedSigner` 子菜单改成直列功能：`BTC交易签名 / 消息签名 / 链上扫码签名 / 连接钱包 / 连接链上钱包 / 助记词工具 / 固件自检`。未加载钱包时，登录页 `SeedSigner` 也直列这些入口；点签名或连接钱包会先加载助记词，加载成功后直接进入对应功能。BTC 钱包连接入口当前聚合 `扩展公钥 xpub/zpub QR`、`地址核对`、`钱包描述符`；链上钱包连接仍走 `OKX / Bitget / MetaMask / Rabby / TokenPocket`。验证：`python3 -m py_compile src/krux/pages/login.py src/krux/pages/home_pages/home.py tests/pages/test_self_check.py tests/pages/home_pages/test_web3_ui.py` 通过；定向回归 `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/python -m pytest -q tests/pages/test_self_check.py tests/pages/home_pages/test_web3_ui.py` 结果 `16 passed`。菜单补强版曾成功编译并刷入，但用户随后反馈字体横画断续，因此 2026-05-11 00:18 已被上方显示修复版替换。
- 2026-05-10 晚间真机触摸修复：用户反馈“显示字体不完整、触摸还是乱”。本轮先停止叠加 UI 猜测，直接撤销 Amigo 自定义触摸坐标旋转：`src/krux/touch.py` 已恢复官方触摸坐标处理，`src/board.py` 和 `firmware/MaixPy/projects/maixpy_amigo/builtin_py/board.py` 已删除 `touch_transform: rotate_cw`；`rg -n "touch_transform|rotate_cw|_normalize_position" src firmware/MaixPy/projects/maixpy_amigo/builtin_py/board.py` 无结果。Amigo 字库硬校验通过：扫描 `src` 内全部宽字符，`font_device.h` 中 `missing=0`，因此当前不是缺中文字库。低负载构建命令 `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功；新包 `build/amigo-official-base-official-shell-kboot.kfpkg` 大小约 `846K`，SHA256 `8a96124d2f7fc120e384364c74104b73b4791dff2c1252015ba52a047f1228f3`，固件 `build/amigo-official-base-firmware.bin` SHA256 `c4dbb7a5dd1bd1c0613c434a9632a5675c14abaaa4f4c2ce0ec87be9e49f028f`。已刷入固定串口 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`，Ktool 显示主固件写入 `Flashed 1652709 B [26 chunks of 65536B] (00080000~0021FFFF) in 165.183s` 并 `Rebooting...`。验证：`python3 -m py_compile` 关键文件通过，`git diff --check` 通过，定向回归用 `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/python -m pytest -q tests/pages/test_self_check.py tests/pages/test_qr_view.py tests/pages/test_qr_capture.py tests/pages/home_pages/test_web3_ui.py` 结果 `49 passed`。下一位接手者注意：如果真机触摸仍乱，优先检查触摸排线/拨码开关/硬件坐标原始值，不要再启用 `rotate_cw`；如果真机字体仍缺损，优先排查 LCD 字体渲染/显示参数，而不是继续加字库。
- 2026-05-10 最新策略收敛：按用户新要求改成“官方 Amigo 顶层菜单保持不变，只增加一个 `SeedSigner` 入口”。登录页顶层现在是 `加载助记词 / 新助记词 / 设置 / 工具 / SeedSigner / 关于`；加载钱包后的首页顶层现在是 `备份助记词 / 扩展公钥 / 钱包 / 地址 / 签名 / SeedSigner / 重启或关机`。迁移功能统一收进 `SeedSigner` 子菜单，里面直列签名、连接钱包、助记词工具和固件自检；这样官方功能和新增功能边界清楚，后续真机排障先确认官方菜单，再确认新增入口。
- 2026-05-10 同步稳定性收敛：已清理 `_boot.py`、`context.py`、`input.py`、`display.py`、`login.py` 和 MaixPy `maixpy_main.c` 里的临时诊断打印，避免真机菜单循环和启动阶段刷串口日志；保留可见启动失败页，方便如果 Python 启动异常时屏幕直接显示失败阶段。
- 2026-05-10 截图脚本同步：新增 `simulator/sequences/_open-pi-features.txt`、`_open-pi-signing.txt`、`_open-pi-mnemonic-tools.txt`、`_open-pi-connect-wallet.txt`、`_open-pi-self-check.txt`，所有 Web3、扫码签名、助记词工具、自检相关截图序列都先进入 `树莓派功能`，避免旧脚本继续误拍官方首页。低负载验证结果：`python3 -m py_compile` 关键文件通过，`git diff --check` 通过，字库检查 `missing=0`，定向回归 `94 passed`；关键截图序列 `home-options / web3 / web3-connect-okx / web3-sign / self-check-home / bip85 / sign-psbt` 均可单独跑通。
- 2026-05-10 本策略固件已重新低负载编译：命令 `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功退出；`build/amigo-official-base-firmware.bin` 大小 `1653184` 字节，SHA256 `88b627994832c50b9fe2fda0f9841128b88f08bef77b742bece766196e1e6af0`；`build/amigo-official-base-official-shell-kboot.kfpkg` 大小 `865812` 字节，SHA256 `206d78fae4c2ff9621f123c6d8cf24683ae4c072da5910294824a2f464a184b8`。`unzip -l` 显示包内仍是官方壳 5 文件：`flash-list.json / bootloader_lo.bin / bootloader_hi.bin / config.bin / firmware.bin`，其中 `firmware.bin` 为 `1653184` 字节。
- 2026-05-07 更新：再次完整跑通 `bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`，总截图数维持在 `176` 张；抽查 `web3-home`、`home-options`、`backup-stackbit`、`wallet-descriptor-tr-minis-1`、`settings-options-appearance`、`print-qr-prompt`、`tools-create-QR` 等关键图，未见新的英文残留或 3.5 寸触摸排版回退。
- 2026-05-06 更新：新增 `Amigo 商用交付说明` 中文页，把支持范围、禁用范围、验证记录和接手顺序集中到一页，方便以后发货、售后和交接。
- 2026-05-06 更新：新增 `Amigo 常见问题` 中文页，并把它挂到 README、中文新手入口和安装教程里，补齐商业化交付最常被问到的支持入口。
  - 2026-05-07 更新：继续做 Amigo 深层页面中文润色和 3.5 寸触摸排版细化，重点收口 `KEF`、密码短语和消息签名的高频提示，把 `使用默认加密模式`、`更新标签`、`密码短语含非 ASCII 字符`、`消息 / 地址 / 签名 / 公钥` 等页面再压短一轮；最新针对性回归 `111 passed`。
- 2026-05-07 更新：恢复 `工具 -> 创建二维码` 入口，补齐中文提示、Amigo 触摸屏截图序列和单测，保证自定义文本二维码能从菜单进入、生成并导出。
- 2026-05-07 更新：继续收口 `MnemonicLoader`、`Mnemonic XOR`、`BIP85`、`助记词备份` 和 `消息签名` 的中文确认词与错误提示，避免 Amigo 深层页面再冒英文。
- 2026-05-07 更新：继续收口 `钱包描述符`、`地址列表` 和 `二维码查看器` 的 Amigo 中文菜单与触摸排版；新增 `Amigo 直接烧录 maixpy.bin` 维护者教程，方便以后只更新底层镜像的人直接接手。
- 2026-05-07 更新：重新跑了 `tests/pages/test_qr_view.py`、`tests/pages/home_pages/test_addresses.py`、`tests/pages/home_pages/test_wallet_descriptor.py`、`tests/pages/home_pages/test_mnemonic_backup.py`，结果 `58 passed`；完整 Amigo 中文截图回归再次通过，截图总数仍为 `176` 张。
- 2026-05-07 更新：钱包描述符 / 文件操作回归重新跑通，`tests/pages/home_pages/test_wallet_descriptor.py` 和 `tests/pages/test_file_operations.py` 结果 `22 passed`；确认保存页和导出页在最新中文文案下仍可用。
- 2026-05-07 更新：完整 Amigo 截图回归重新跑通，新增 3 张 `创建二维码` 截图后总数到 `176` 张；`tests/pages/test_tools.py` 结果 `7 passed`，`git diff --check` 通过。
- 2026-05-07 更新：最新组合回归重新跑通 `tests/pages/test_encryption_ui.py`、`tests/pages/test_wallet_settings.py`、`tests/pages/home_pages/test_bip85.py`、`tests/pages/home_pages/test_wallet_descriptor.py`、`tests/pages/test_file_operations.py`，结果 `83 passed`。
- 2026-05-07 更新：Amigo 固件最终编译链路已修正并成功生成产物，`make -C firmware/MaixPy/projects/maixpy_amigo/build -j2` 通过；输出文件为 `firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin`、`firmware/MaixPy/projects/maixpy_amigo/build/firmware.bin` 和 `firmware/MaixPy/projects/maixpy_amigo/build/maixpy.elf`。
- 2026-05-07 更新：`maixpy.bin` 的 SHA256 为 `04a59041f4d20dd9a6ac79d82807325c1d5db38d8ef1e787af820555722ead4b`，可作为后续刷机和交付校验基线。
- 2026-05-07 更新：`tests/pages/home_pages/test_web3_ui.py -q` 重新跑通，结果 `10 passed`，确认 Web3 顶层菜单、连接钱包子菜单和消息 / 交易签名结果标题仍正常。
- 当前准确结论：**除智能卡外，树莓派固件里的核心功能路线已经迁移或由 Krux 原生能力覆盖到 Amigo 第一版，但还不能宣称商业级全部完成**。Web3/TP/EVM、固件自检、首页大屏触摸排版、BTC/PSBT/xpub、助记词创建/导入/备份、`扑克牌创建`、`16进制创建`、`查看原始熵`、`钢板打孔数字`、`二次助记词`、`钢板二次还原`、`15/18/21词创建/导入` 和 `开机数字口令锁` 已进入第一版；当前阻塞项是真机乱码反馈、深层页面中文润色、3.5 寸触摸排版、截图回归和真机逐页验收。
- 2026-05-09 真机反馈修复：用户反馈“很多显示乱码、功能不完整”。本轮修复 `firmware/MaixPy/components/micropython/port/src/omv/img/font.c`，避免缺字时绘制未初始化字形缓存；新增 Amigo 显示层安全文本替换，把省略号、细空格和全角标点在绘制前替换为 LCD 更稳的 ASCII 字符；同时把开机首页改为 `加载钱包 / 创建钱包 / 助记词工具 / 功能总览 / 离线工具 / 固件自检 / 设置 / 关于`，并新增设备端 `功能总览` 页面，直接说明已支持和不支持的范围。
- 2026-05-09 验证：本轮仅跑轻量检查，未启动高负载固件编译。`python3 -m py_compile` 已覆盖启动、显示、首页、助记词、Web3、自检、二维码、加密、地址和设置等关键 Python 页面；`git diff --check` 通过；定向回归两组分别为 `162 passed` 和 `184 passed`；电脑负载和内存正常。下一步需要重新生成 Amigo 中文截图并真机刷入验证乱码是否消失。
- 2026-05-09 晚间继续收口：已重新跑完整 Amigo 中文截图回归，命令为 `nice -n 10 bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`，结果成功退出并生成 `176` 张中文截图；已修复 `print-qr` 截图误进红色 `加载失败`、打印确认页底层驱动名、Web3 长交易预览压按钮、QR 查看/扫码触摸提示和 Amigo 模拟器触摸坐标问题。
- 2026-05-09 晚间验证：`python3 -m py_compile src/krux/pages/__init__.py src/krux/pages/home_pages/mnemonic_backup.py src/krux/pages/home_pages/web3_ui.py src/krux/pages/qr_capture.py simulator/kruxsim/sequence.py simulator/kruxsim/mocks/touchscreen_common.py` 通过；`git diff --check` 通过；`tests/pages/home_pages/test_web3_ui.py tests/pages/test_print_page.py tests/pages/home_pages/test_mnemonic_backup.py tests/test_display.py` 结果 `93 passed`。
- 2026-05-09 晚间注意：完整截图回归中曾出现一次 `Exception in thread Thread-1 (run_krux):`，但脚本最终退出 `0` 且截图完整；单独复跑 `wallet-descriptor-wsh.txt`、`extended-public-key-wpkh.txt`、`extended-public-key-wsh.txt` 没有复现。下一位 AI 若再看到这行，优先保留日志并抓完整 traceback，不要直接删功能。
- 2026-05-09 晚间构建：低负载命令 `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh` 成功退出；新交付包 `build/amigo-official-base-kboot.kfpkg` 大小 `930231` 字节，SHA256 `3624fe149006f46be4d9da511239c70d728fb02790bdc9b1edd74bb078f8a048`；新固件镜像 `build/amigo-official-base-firmware.bin` 大小 `1885440` 字节，SHA256 `b19ac93a23de5fc82040dd263e2f5e693b881165f5fb455bd381e49dcc81d38e`。
- 2026-05-09 晚间包检查：`unzip -l build/amigo-official-base-kboot.kfpkg` 显示包内有 `flash-list.json`、`bootloader_lo.bin`、`bootloader_hi.bin`、`config.bin` 和 `firmware.bin`，其中 `firmware.bin` 为 `1885440` 字节，和官方 Amigo 主固件同量级；刷机只能用这个完整 `kboot.kfpkg`，不要交付旧的 `build/amigo-custom-kboot.kfpkg`。
- 2026-05-09 晚间真机刷入前检查：当前电脑没有识别到 Amigo 串口，`lsusb` 未出现 Sipeed/USB-UART 设备，`/dev/serial/by-id`、`/dev/ttyUSB*`、`/dev/ttyACM*` 均为空；因此不要盲刷其他设备。等串口出现后再用低速命令 `sudo python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/ttyUSB1 build/amigo-official-base-kboot.kfpkg`，实际端口以 `/dev/serial/by-id` 或新出现的 `/dev/ttyUSB*` 为准。
- 2026-05-09 晚间真机刷入成功：用户重新插 USB 后电脑识别到 `Sipeed USB to Dual Uart`，`if00 -> /dev/ttyUSB0`、`if01 -> /dev/ttyUSB1`；执行 `sudo python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/ttyUSB1 build/amigo-official-base-kboot.kfpkg` 成功，主固件区写入 `Flashed 1885477 B [29 chunks of 65536B] (00080000~0024FFFF) in 183.144s`，最后显示 `Rebooting...`。刷后双串口仍存在，下一步需要人工确认真机屏幕是否进入中文首页和触摸是否可用。
- 2026-05-09 晚间黑屏复测：较新的自定义官方底座包刷入后仍黑屏。该包 `build/amigo-official-base-kboot.kfpkg` 大小 `842K`，SHA256 `35e309d6500fd1cc58bc86d9155ccd0ac4b357a6fbb3a1eab9dfadece85dfd1f`；包内 `firmware.bin` 大小 `1644800` 字节，SHA256 `aa4ab1606145ede745e2d41c96eda7b81ea0e6ccf1b7c159ee8e8a7212aea675`。不要把这份包作为交付固件。
- 2026-05-09 晚间官方救机：已再次刷回官方包 `/tmp/krux-official-v26.04.0/krux-v26.04.0/maixpy_amigo/kboot.kfpkg`，SHA256 `2f6afc012978f460b1656a4d8e79271eb65a643551fcbe5f57194a2a76de58f2`；Ktool 显示写入 `1746725 B (00080000~0022FFFF)` 并 `Rebooting...`。官方包此前已由用户确认能亮屏，是当前救机基线。
- 2026-05-09 晚间新增最小诊断包：新增 `firmware/scripts/amigo-diag-boot.py` 和构建参数 `firmware/scripts/build-amigo-official-base.sh --diag-boot`。该包只冻结 `_boot.py / board.py / fpioa_manager.py / pmu.py`，只测试 LCD 初始化和背光，不加载 Krux。第一版静态诊断包产物 `build/amigo-diag-kboot.kfpkg` 大小 `559K`，SHA256 `668388d88713c10b216d189854ab0ec625c734014bca51256d93484449670004`；后续升级成自动轮询 LCD 参数的诊断包产物 `build/amigo-diag-kboot.kfpkg` 大小 `560K`，SHA256 `54dc7c9366ae2481fb5cc771ec64e02afc10afeeecb7757ecfea519174c5a2bc`；对应诊断 `firmware.bin` 大小 `908032` 字节，SHA256 `de00bbae419f741ccce930bd95e33a4ba10c06e7b245bf87be642c29e582aad2`。包内结构仍是官方 Kboot 5 文件，`.mpy` 残留为 `0`。
- 2026-05-09 晚间当前状态：电脑已重新识别到 Amigo USB 串口，`/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0`、`/dev/ttyUSB0` 和 `/dev/ttyUSB1` 均存在。第二版自动轮询诊断包已经刷入并重启，接下来只看用户肉眼屏幕结果。
- 2026-05-10 继续黑屏诊断：补齐 Amigo `firmware/MaixPy/projects/maixpy_amigo/builtin_py/pmu.py` 的 `set_screen_brightness()`，诊断 `_boot.py` 改为调用公开 PMU 接口；同时把 Amigo LCD 默认设置改为读取板级 `board.config["lcd"]`，避免 Krux 默认值覆盖官方可亮屏参数。
- 2026-05-10 新增官方启动壳打包：`firmware/scripts/build-amigo-official-base.sh` 支持 `--official-shell`，会复用官方 Amigo `kboot.kfpkg` 里的 `bootloader_lo.bin`、`bootloader_hi.bin`、`config.bin` 和 `flash-list.json`，只替换本机编译出的 `firmware.bin`。这用于排除本机 Kboot 构建变量，后续诊断优先刷这个包。
- 2026-05-10 新增安全诊断刷机脚本：`firmware/scripts/flash-amigo-diag.sh` 默认只使用 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 和 `build/amigo-diag-official-shell-kboot.kfpkg`。如果串口不存在会退出并拒绝回退到其他端口；需要等待设备时可用 `AMIGO_WAIT_SECONDS=300 firmware/scripts/flash-amigo-diag.sh`。
- 2026-05-10 最新诊断包：低负载命令 `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --diag-boot --official-shell` 成功；`build/amigo-diag-firmware.bin` 大小 `908288` 字节，SHA256 `bfef9eb127e75fe555ab264497f91cc07e4db94362fe0531248e63f753ec8647`；`build/amigo-diag-official-shell-kboot.kfpkg` 大小 `560K`，SHA256 `1053298f977a86843f8ed683433c59289dfc970eaae84c917e38201534aa82c3`。`unzip -l` 显示包内仍是官方 Kboot 5 文件，时间戳固定到 `2009-01-03 18:15`。
- 2026-05-10 当前刷机阻塞：`lsusb` 当前没有 `Sipeed USB to Dual Uart`，`/dev/serial/by-id`、`/dev/ttyUSB*`、`/dev/ttyACM*` 为空。系统日志显示 Amigo 在 `2026-05-10 06:15:31` 曾枚举成 `ttyUSB0/ttyUSB1`，但 `06:29:48` 已断开，之后没有重新连接记录。因此当前不能刷机，必须先让电脑重新看到 `Sipeed USB to Dual Uart` 和 `/dev/ttyUSB1`。
- 2026-05-10 自动等待结果：已用固定路径 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 等待 5 分钟；结束时间 `2026-05-10 06:57:52 CST`，结果 `NO_SIPEED_SERIAL_AFTER_5_MIN`。没有执行刷机命令，设备当前没有被新诊断包写入。
- 2026-05-10 二次确认：用户询问是否刷好后，再次检查 `lsusb`、`/dev/serial/by-id`、`/dev/ttyUSB*` 均未发现 Sipeed/FTDI/Amigo 串口；随后固定等待 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 2 分钟，结束时间 `2026-05-10 07:30:54 CST`，结果 `NO_SIPEED_SERIAL_AFTER_2_MIN`。没有执行刷机命令。
- 2026-05-10 诊断包真机刷入成功：用户重新插上 USB 后，电脑识别到 `Sipeed USB to Dual Uart`，`if00 -> /dev/ttyUSB0`、`if01 -> /dev/ttyUSB1`。执行 `sudo python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 build/amigo-diag-official-shell-kboot.kfpkg` 成功；主固件区写入 `Flashed 908325 B [14 chunks of 65536B] (00080000~0015FFFF) in 88.955s`，最后显示 `Rebooting...`。刷后电脑端双串口仍存在。下一步只看真机屏幕：如果看到彩色循环或 `AMIGO DIAG BOOT OK`，说明 LCD/背光底层可用；如果仍黑屏，先刷回官方救机包。
- 2026-05-10 诊断串口结果：`/dev/ttyUSB1` 有启动日志，显示 `App ok, ACTIVE`、`Loading app from flash at 0x00080000 (908288 B)`、`Starting at 0x80000000`，随后 MaixPy 启动并输出多轮 `[AMIGO DIAG] lcd init done width=480 height=320` 和 `screen drawn ...`。电脑端结论：Kboot、应用加载、MaixPy 启动、LCD 初始化和绘图命令都已经跑起来；若肉眼仍黑屏，优先怀疑背光/屏幕显示参数/排线或硬件侧显示，而不是固件没有启动。
- 2026-05-10 诊断屏幕肉眼确认：用户发图确认真机屏幕正在轮播诊断页，能看到 `AMIGO DIAG BOOT OK`、绿色边框和 LCD 参数文字。结论：Amigo 屏幕、背光、LCD 初始化和绘图底层可用；此前完整 Krux 黑屏应继续排查 Krux Python 启动层、默认显示参数和页面导入/内存问题，而不是硬件完全不亮。
- 2026-05-10 完整 Krux 白屏定位：刷入 `build/amigo-official-base-official-shell-kboot.kfpkg` 后用户反馈白屏；手动拉 DTR/RTS 复位并监听 `/dev/ttyUSB1`，串口显示已进入 MaixPy 和 `_boot.py`，但在 `draw_splash()` 中崩溃：`AttributeError: 'str' object has no attribute 'translate'`，位置为 `krux/display.py` 的 Amigo 安全文本替换。结论：白屏不是硬件或 Kboot 问题，而是 MaixPy 字符串 API 兼容问题。
- 2026-05-10 白屏修复：已把 `src/krux/display.py` 的 `_safe_text()` 从 CPython 专用 `str.translate()` 改为普通字符循环替换；同时把 `src/krux/web3.py` 的 `normalize_action()` 也去掉 `.translate()`，避免进入 Web3 后再触发同类兼容问题。`rg -n "\.translate\(" src/krux tests` 已无结果；本机 `pytest` 未安装，未临时安装依赖。
- 2026-05-10 修复版完整包：低负载命令 `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功；`build/amigo-official-base-firmware.bin` 大小 `1645568` 字节，SHA256 `5447d83c9b777f03d47eb279adfbfbd7c1a18cb2b363c35660b16ae307b297c4`；`build/amigo-official-base-official-shell-kboot.kfpkg` SHA256 `841ed1e577e7c67b0ad1515fc51e19118bddafd0e03f449ffa0384e06f9272ed`。包内仍为官方壳 5 文件，`firmware.bin` 大小 `1645568` 字节。
- 2026-05-10 修复版真机刷入和启动日志：使用固定串口 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`、`115200` 低速刷入成功，主固件区写入 `Flashed 1645605 B [26 chunks of 65536B] (00080000~0021FFFF) in 164.571s`。复位监听显示已经完成 `_boot.py`、电源、SD 卡检查、Context、触摸、摄像头、开机口令检查，并到达 `[KRUX BOOT] login page run start`；之后空闲监听 20 秒无新异常。电脑端结论：修复版已进入主菜单循环，若肉眼仍白屏，下一步应查菜单绘制颜色/刷新/方向，而不是继续查 Python 启动崩溃。
- 2026-05-10 15:00 用户反馈首页仍像乱码：照片显示完整 Krux 已进入首页，但两行灰底卡片、红色副标题、白色描边和右上角彩色状态图标在 Amigo LCD 上显示脏、缺笔画、毛刺明显。处理策略改为先收敛 UI：Amigo 顶层菜单改成白底黑字、单行入口、细分隔线；状态栏改成白底黑色电池图标；功能说明页改成更短的黑字分段，减少彩色和长句。
- 2026-05-10 15:20 界面收敛版已编译：模拟器 `login-options-300.zh.png` 已显示白底黑字单行菜单；`python3 -m py_compile src/krux/pages/__init__.py src/krux/pages/login.py` 和 `git diff --check` 通过。低负载命令 `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功；`build/amigo-official-base-firmware.bin` 大小 `1645312` 字节，SHA256 `0aa2e1a5213fd18846d8a227c14cb68bd7e67242c63e1578adaffbaf5071f0d9`；`build/amigo-official-base-official-shell-kboot.kfpkg` SHA256 `e1fc788f90db3cd4e0b8c8a2585a4fee752046c2e9a9a578f4c97cc8fd83d7ff`，包内 `firmware.bin` 大小 `1645312` 字节。
- 2026-05-10 15:23 当前刷机阻塞：编译完成后检查 `lsusb`、`/dev/serial/by-id`、`/dev/ttyUSB*`、`/dev/ttyACM*` 均未发现 Sipeed/Amigo 串口；随后自动等待固定路径 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 两分钟，结果 `NO_SIPEED_SERIAL_AFTER_120S`。因此界面收敛版尚未刷入真机，下一步是让电脑重新识别 Amigo USB 串口后，直接刷 `build/amigo-official-base-official-shell-kboot.kfpkg`，不需要重新编译。
- 继续确认：TinySeed 已经统一到 `0-2047 / 11 位` 编号体系，位权从左到右显示为 `1 / 2 / 4 / ... / 1024`，显示、手动输入、打印和扫描还原都要跟着同一套编号走，不能再沿用旧的 `1-2048 / 12 位` 假设。
- 已完成：已加载助记词后的 Amigo 首页已改回官方顶层结构，并只新增一个 `SeedSigner` 入口；进入该入口后第一层显示树莓派式 `扫码签名 / 助记词工具 / 连接钱包 / 固件自检`，其中 `扫码签名` 聚合 BTC PSBT、比特币消息和链上扫码，`连接钱包` 聚合 BTC xpub、地址核对、钱包描述符和链上钱包连接，已取消智能卡工具位置。
- 已完成：Web3 入口、连接钱包、消息签名、结构化数据签名、交易签名、结构化交易签名
- 已完成：`OKX / Bitget / MetaMask / Rabby / TokenPocket` 连接二维码
- 已完成：`tpr1:` / `w3r1:` 安卓低密度中转请求解析
- 已完成：Amigo 桌面模拟器中文截图验证
- 已完成：Web3 顶层菜单改成 3.5 寸触摸屏大按钮，两项入口分别带用途说明
- 已完成：继续收尾 Amigo 深层中文页面的标点统一，消息签名、钱包描述符、自检、设备测试、Web3 预览和开机口令相关页面改成更紧凑的 ASCII 冒号，减少 3.5 寸屏上的折行和视觉噪音
- 已完成：新增中文 `固件自检` 入口，登录前和加载助记词后的首页都能进入
- 已完成：Amigo 默认语言改为 `zh-CN`，首次启动和模拟器无设置时默认中文
- 已完成：加载助记词后的 Amigo 首页保留官方功能入口，树莓派功能集中到单独入口，降低官方功能和新增功能互相影响的风险。
- 已完成：`固件自检` 子菜单改为双行大按钮，包含 `状态总览`、`SD卡检查`、`测试套件`、`触摸测试`
- 已完成：`备份助记词 -> 其他格式 -> 钢板打孔数字` 第一版，按树莓派 `0-2047` BIP39 序号和 `1/2/4/8/16/32/64/128/256/512/1024` 位权显示，每屏 6 个词，适配 Amigo 大屏核对
- 已完成：`助记词工具 -> 二次助记词` 第一版，包含默认二次加密、默认二次还原、自定义二次加密、自定义二次还原；默认加密用树莓派同款 `+8 +7 +6 +7 +6 +7 +7 +3 +5 +2 +4 +2`
- 已完成：`加载助记词 -> 手动输入 -> 钢板二次还原` 第一版，可输入 12 组钢板打孔位或 12 个 0-based 序号，先恢复假助记词，再套默认或自定义二次还原参数得到真实助记词，并进入 Krux 原生助记词确认/加载流程
- 已完成：15/18/21 词第一版扩展，新建助记词长度菜单显示 `12/24/15/18/21`；拍照、骰子、扑克牌、16进制和手动单词创建支持 160/192/224 bit；二维码/SeedQR/CompactSeedQR 导入和加密助记词读取允许 15/18/21 词
- 已完成：Amigo 原生 `开机口令锁` 第一版，开机进入登录菜单前先输入 4-12 位数字口令；设置路径为 `设置 -> 安全 -> 开机口令锁`，支持开启、修改、关闭；口令哈希保存在 `/flash/boot_lock.json`，恢复出厂设置会删除该文件
- 已停用：`智能卡签名` 和 `智能卡工具` 不再出现在 Amigo Web3 菜单
- 不再迁移：Amigo 直连 PC/SC 智能卡读卡流程、外接读卡器驱动、SeedKeeper 卡管理、Satochip / SeedKeeper 完整硬件管理链路
- 已确认：当前仓库 `krux/` 里没有 `pyscard`、`pcscd`、`CardConnector`、`ACR39U` 直连实现；这些只存在于树莓派参考仓库 `satochip-signer/pi-signer-py/`
- 已清理：Amigo 主线中的智能卡桥接页面、专用模块、专用测试和专用截图序列已删除

## 树莓派功能迁移矩阵

| 树莓派功能 | Amigo 当前状态 | 说明 |
| --- | --- | --- |
| 开机口令锁 / 签名前 PIN | 已迁移并接入签名流程 | 已按 Amigo 原生固件重做：`设置 -> 安全 -> 开机口令锁` 可开启/修改/关闭；开机进入登录菜单前先显示大触摸数字键盘；支持 4-12 位数字；开机错误 5 次后返回失败并关机。设置口令后，BTC PSBT、BTC 消息和 Web3/TP 链上请求会在真正签名前再次要求输入同一个口令；签名前输错 3 次自动关机。注意：这是本机 Flash 中的便捷启动门禁和误签防护，不是硬件安全芯片，也不等同树莓派 Linux 启动分区加密方案 |
| 摄像头扫码 | 已具备 | Krux 原生支持 Amigo 摄像头扫码，已扩展识别 `tp:`、`ur:eth-sign-request`、`tpr1:`、`w3r1:` |
| TP 多分片扫码 | 已迁移 | 已支持 `tp:multiFragment` 拼接 |
| Web3 低密度中转码 | 已迁移 | 已支持 `tpr1:` / `w3r1:` |
| Web3 连接钱包 | 已迁移 | `OKX / Bitget / MetaMask / Rabby / TokenPocket` |
| EVM 地址派生 | 已迁移 | 使用 Krux 已加载助记词派生 |
| EIP-191 消息签名 | 已迁移 | Amigo 本机助记词签名 |
| EIP-712 结构化数据签名 | 已迁移 | Amigo 本机助记词签名 |
| EVM Legacy / EIP-1559 交易签名 | 已迁移 | Amigo 本机助记词签名 |
| 固件自检 | 已迁移 | 新增中文 `固件自检` / `自检` 入口，可查看设备、版本、屏幕、触摸、扫码、Web3 状态，并可进入 SD 检查、测试套件、触摸测试 |
| 导入助记词 | 已由 Krux 覆盖 | Krux 原生已有单词导入、BIP39 编号导入、SeedQR/二维码导入、存储导入 |
| 创建助记词：拍照/骰子/手输单词 | 已由 Krux 覆盖 | Krux 原生已有相机熵、D6/D20 骰子熵、手动单词创建；仍需继续中文化和大屏提示优化 |
| 创建助记词：扑克牌 | 已迁移第一版 | 登录前 `新助记词 -> 扑克牌创建` 已按树莓派/iancoleman `Card [A2-9TJQK][CDHS]` 规则实现：按顺序输入牌面和花色，按 Card 规则计算 bit，够位数后对规范化卡牌文本做 `SHA256` 并截取生成 BIP39；当前 UI 支持 12/15/18/21/24 词，24 词需要多副牌或额外输入 |
| 创建助记词：16进制 | 已迁移第一版 | 登录前 `新助记词 -> 16进制创建` 已按树莓派/iancoleman 普通 `Hex [0-9A-F]` 规则实现：过滤 HEX 文本、转小写做 `SHA256`、按 12/15/18/21/24 词截取 16/20/24/28/32 字节生成 BIP39 |
| 查看 BIP39 序号 | 已由 Krux 覆盖 | `Backup Mnemonic -> Other Formats -> Numbers` 可显示十进制/十六进制/八进制编号；还要改成更直观中文入口 |
| 查看原始熵 | 已迁移第一版 | `备份助记词 -> 其他格式 -> 查看原始熵` 已将当前 BIP39 助记词反推出原始熵，并以 HEX 字节和位数显示 |
| BIP85 子助记词 | 已由 Krux 覆盖 | `BIP85` 可派生 BIP39 子助记词和 Base64 密码；需要继续中文化提示 |
| 二次加密/二次还原助记词 | 已迁移第一版 | `助记词工具 -> 二次助记词` 已支持 12 词默认加密/还原和自定义 12 组运算；按树莓派当前规则“运算符按字面执行”，默认还原用 `-8 -7 -6 ...`；移位后的假助记词可能 BIP39 校验码无效，Amigo 不会强行把无效假助记词加载成 Krux 钱包 |
| 钢板/钛板打孔数字 | 已迁移第一版 | `备份助记词 -> 其他格式 -> 钢板打孔数字` 已按树莓派 0-based BIP39 序号和 11 个位权显示打孔位；现已和 Krux 原生 `数字` 备份统一为 0-based `0-2047` |
| 从钢板数字恢复二次助记词 | 已迁移第一版 | `加载助记词 -> 手动输入 -> 钢板二次还原` 可解析 12 组打孔位，恢复假助记词后可选择默认参数或自定义 12 组还原参数 |
| BTC PSBT 扫码签名 | 已由 Krux 覆盖 | Krux 原生已有 PSBT 扫码、UR/BBQR/PMOFN、签名、结果二维码/SD 导出 |
| BTC xpub / zpub 导出 | 已由 Krux 覆盖 | `Extended Public Key` 页面已支持文本、二维码和 SD 导出 |
| 中文大屏首页 | 已迁移并收敛 | Amigo 默认 `zh-CN`；顶层首页保留官方结构，只增加 `SeedSigner` 入口。进入该入口后第一层使用树莓派式 `扫码签名 / 助记词工具 / 连接钱包 / 固件自检`，其中 `扫码签名` 聚合 BTC PSBT、比特币消息和链上扫码，`连接钱包` 聚合 BTC xpub、地址核对、钱包描述符和链上钱包连接，已取消智能卡工具位置 |
| 全固件中文化 | 部分完成 | 默认语言、首页、Web3、自检已中文化；Krux 原生深层页面仍有英文或混合文案，需要继续逐页处理 |
| 大屏触摸 UI 优化 | 部分完成 | 首页、Web3、自检已经按大屏双行按钮处理；助记词、BIP85、备份、PSBT 复核等深层页面还需要继续为 3.5 寸屏优化 |
| Satochip Web3 签名 | 停用 | 用户决定 Amigo 固件不要智能卡功能 |
| Satochip EVM 地址 | 停用 | 用户决定 Amigo 固件不要智能卡功能 |
| Satochip BTC xpub / zpub | 停用 | 用户决定 Amigo 固件不要智能卡功能 |
| Satochip 卡信息 | 停用 | 用户决定 Amigo 固件不要智能卡功能 |
| SeedKeeper 状态 | 停用 | 用户决定 Amigo 固件不要智能卡功能 |
| Satochip / SeedKeeper PIN 修改 | 不做 | ACR39U 无法直接在 Amigo 上按树莓派方式工作 |
| Satochip / SeedKeeper 重置 | 不做 | 高风险操作，且当前硬件链路不成立 |
| 写入助记词到 Satochip / SeedKeeper | 不做 | 用户已取消智能卡方向，避免助记词跨设备传输风险 |
| Satochip PSBT 签名 | 不做 | 树莓派靠 `pyscard + pcscd + pysatochip + embit`，Amigo 当前没有 PC/SC 读卡器驱动 |

## 截图清单

- 已有或正在生成：
  - `simulator/screenshots/web3-home-300.zh.png`
  - `simulator/screenshots/web3-menu-300.zh.png`
  - `simulator/screenshots/web3-connect-wallets-300.zh.png`
  - `simulator/screenshots/self-check-home-entry-300.zh.png`
  - `simulator/screenshots/self-check-home-menu-300.zh.png`
  - `simulator/screenshots/self-check-home-status-300.zh.png`
  - `simulator/screenshots/new-mnemonic-via-cards-prompt-300.zh.png`
  - `simulator/screenshots/new-mnemonic-via-cards-rank-input-300.zh.png`
  - `simulator/screenshots/new-mnemonic-via-cards-suit-input-300.zh.png`
  - `simulator/screenshots/new-mnemonic-via-hex-prompt-300.zh.png`
  - `simulator/screenshots/new-mnemonic-via-hex-input-300.zh.png`
  - `simulator/screenshots/backup-mnemonic-raw-entropy-300.zh.png`
  - `simulator/screenshots/backup-mnemonic-steel-punch-1-300.zh.png`
  - `simulator/screenshots/backup-mnemonic-steel-punch-2-300.zh.png`
  - `simulator/screenshots/secondary-mnemonic-wallet-menu-300.zh.png`
  - `simulator/screenshots/secondary-mnemonic-menu-300.zh.png`
  - `simulator/screenshots/secondary-mnemonic-default-encrypt-result-300.zh.png`
  - `simulator/screenshots/load-mnemonic-manual-options-300.zh.png` 中已显示 `钢板二次还原`
  - `simulator/screenshots/secondary-steel-restore-menu-300.zh.png`
  - `simulator/screenshots/new-mnemonic-length-options-300.zh.png`
  - `simulator/screenshots/boot-lock-security-menu-300.zh.png`
  - `simulator/screenshots/boot-lock-menu-disabled-300.zh.png`
  - `simulator/screenshots/boot-lock-info-300.zh.png`
  - `simulator/screenshots/boot-lock-warning-300.zh.png`
  - `simulator/screenshots/boot-lock-new-pin-300.zh.png`
  - `simulator/screenshots/boot-lock-confirm-pin-300.zh.png`
  - `simulator/screenshots/boot-lock-saved-300.zh.png`
  - `simulator/screenshots/boot-lock-unlock-300.zh.png`
  - `simulator/screenshots/boot-lock-wrong-pin-300.zh.png`
  - `simulator/screenshots/boot-lock-unlocked-300.zh.png`
  - `simulator/screenshots/boot-lock-login-after-unlock-300.zh.png`
  - 普通 Web3 连接和签名截图
- 智能卡截图已经停止作为 Amigo 主线生成。

## 交接状态

- 2026-05-06 交接补充：
  - 当前主要工作已经转成 Amigo 中文界面精修，不再碰 Android 侧。
  - 最近一次针对性回归测试为 `PYTHONPATH=src .venv/bin/pytest tests/test_i18n.py tests/pages/test_login.py tests/pages/home_pages/test_home.py tests/pages/home_pages/test_mnemonic_backup.py tests/pages/home_pages/test_bip85.py tests/pages/test_self_check.py`，结果 `101 passed`。
  - 这次更新重点是中文标点统一、`BIP85` 文案收口，以及 `固件自检` 菜单项的 Amigo 双行显示。
- 当前用户明确要求：先做 `Amigo 固件`，不要继续花额度在 `Android` 软件上
- 所以下一位接手者默认只动：
  - `krux/` 仓库
  - Amigo 触摸屏 UI
  - 模拟器截图
  - 固件构建与验证
- 当前固件交付物已经可以直接从 `firmware/MaixPy/projects/maixpy_amigo/build/` 取走，先看 `maixpy.bin` 再看 `maixpy.elf`
- 除非用户重新点名，否则不要继续扩展 `app/` 或 `wallet/`
- 最近一次 Web3/QR/自检/i18n 回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py tests/pages/test_self_check.py tests/test_i18n.py -q`
- 最近一次结果：`57 passed`
- 最近一次登录/首页回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_home.py -q`
- 最近一次结果：`75 passed`
- 最近一次完整 Amigo 中文截图：`bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
- 最近一次结果：成功生成 `147` 张中文截图，`simulator/screenshots/` 中没有 `*smartcard*` 截图残留
- 2026-05-05 接手后更新：
  - 明确记录 Amigo 当前没有 `PC/SC / ACR39U` 智能卡读卡器驱动
  - 补全树莓派功能迁移矩阵
  - 最新回归结果：`64 passed`
- 2026-05-05 用户确认取消智能卡方向：
  - Amigo Web3 顶层菜单只保留 `连接钱包`、`扫码签名`
  - `智能卡签名`、`智能卡工具` 已从可见菜单撤掉
  - 自动截图脚本不再运行 `web3-smartcard-*.txt`
  - 普通 Web3 回归：`57 passed`
  - 含历史桥接底层代码的回归：`62 passed`
  - 已重新生成并确认 `simulator/screenshots/web3-menu-300.zh.png`
- 2026-05-05 本轮继续清理：
  - 删除 `src/krux/smartcard_bridge.py`
  - 删除 `tests/test_smartcard_bridge.py`
  - 删除 `web3_ui.py` 内部智能卡桥接页面方法
  - 删除 `tests/pages/home_pages/test_web3_ui.py` 中的智能卡桥接测试
  - 删除 `simulator/sequences/web3-smartcard-*.txt`
  - 删除智能卡桥接专用二维码素材
  - 删除 `web3.py` 中专门用于智能卡桥接的 TP 回传封装函数
- 2026-05-05 本轮继续迁移非智能卡功能和大屏 UI：
  - 新增 `src/krux/pages/self_check.py`
  - 登录菜单新增 `固件自检`
  - 已加载助记词后的首页新增 `自检`
  - 自检页显示设备、固件版本、3.5 寸屏幕、触摸、扫码和 Web3 状态
  - 自检页复用 Krux 原生 `SD卡检查`、`测试套件`、`触摸测试`
  - Web3 顶层菜单改成两块大触摸按钮：`连接钱包\nOKX / Bitget / MetaMask`、`扫码签名\n消息 / 交易 / TP中转`
  - 钱包连接子菜单中文化为 `OKX钱包`、`Bitget钱包`、`MetaMask`、`Rabby`、`TokenPocket`
  - 新增 `tests/pages/test_self_check.py`
- 2026-05-05 本轮继续迁移非智能卡功能和默认中文：
  - `src/krux/krux_settings.py`：Amigo 默认语言改为 `zh-CN`
  - `src/krux/pages/home_pages/home.py`：加载助记词后的首页改为中文双行大按钮
  - `src/krux/pages/self_check.py`：自检菜单改为中文双行大按钮
  - `tests/pages/home_pages/test_web3_ui.py`、`tests/pages/test_self_check.py`、`tests/pages/test_qr_capture.py`、`tests/pages/test_login.py`、`tests/pages/home_pages/test_home.py` 已按中文默认界面更新断言
  - 重新生成关键截图：`web3-home`、`web3-menu`、`web3-connect-wallets`、`self-check-home-entry`、`self-check-home-menu`、`self-check-home-status`
  - 已删除 `simulator/screenshots/` 里旧的 `web3-smartcard-*` 截图残留
- 2026-05-05 本轮完整截图回归：
  - 命令：`bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
  - 结果：命令成功退出
  - 产物：`simulator/screenshots/` 下生成 `147` 张 `300.zh.png` 中文截图
  - 已核对：`simulator/screenshots/` 下无 `*smartcard*` 截图
- 2026-05-05 本轮重新核对树莓派非智能卡功能：
  - 参考文件：`/home/ak/123/satochip-signer/docs/树莓派菜单逐项说明.zh-CN.md`
  - 参考文件：`/home/ak/123/satochip-signer/docs/全功能操作总手册.zh-CN.md`
  - 参考文件：`/home/ak/123/satochip-signer/pi-appliance/app/kiosk.py`
  - 当时结论：非智能卡功能还没有全部迁完，不能对用户说“已经全迁完”；后续已继续补齐开机数字口令锁，现在核心功能路线见上方“当前进度”和迁移矩阵
  - 已完成或已有：Web3/TP/EVM、BTC PSBT、xpub/zpub、BIP39 编号导入/显示、BIP85、相机熵、骰子熵、SeedQR/二维码导入、自检入口
  - 当时待继续：Amigo 原生开机数字口令、深层页面全中文化、大屏触摸排版、15/18/21 词在 Tinyseed/Stackbit 等专用金属格式中的兼容性评估；其中开机数字口令已在后续完成
- 2026-05-05 本轮继续迁移非智能卡助记词功能：
  - `src/krux/pages/login.py`：新增 `新助记词 -> 16进制创建`
  - HEX 创建规则：匹配树莓派参考的 iancoleman 普通 HEX 模式，不是直接把 HEX 当 raw entropy；设备会对过滤后的 HEX 文本转小写做 `SHA256`，再截取 16/32 字节生成 12/24 词 BIP39
  - HEX 输入 UI：按 Amigo 触摸屏逐字符输入，显示 `已输入/总数` 和末尾预览，支持删除，满长度后才允许继续确认
  - `src/krux/pages/home_pages/mnemonic_backup.py`：新增 `其他格式 -> 查看原始熵`
  - 原始熵显示：使用 `embit.bip39.mnemonic_to_bytes()` 从当前助记词反推 BIP39 熵，按 HEX 字节显示并标注 `128位/256位`
  - 新增测试：`tests/pages/test_login.py::test_new_key_from_hexadecimal_entropy`
  - 新增测试：`tests/pages/home_pages/test_mnemonic_backup.py::test_display_raw_entropy`
  - 同步修正：备份二维码测试改为用翻译函数断言标题，兼容 Amigo 默认中文 `明文二维码`
  - 新增截图序列：`simulator/sequences/new-mnemonic-hex.txt`
  - 更新截图序列：`simulator/sequences/new-mnemonic-options.txt` 中 D6 入口位置随 `16进制创建` 后移
  - 更新截图序列：`simulator/sequences/home-options.txt` 中 `其他格式` 增加 `查看原始熵` 截图，并修正 Stackbit/Tinyseed 后续位置
  - 已生成新截图：`new-mnemonic-via-hex-prompt-300.zh.png`、`new-mnemonic-via-hex-input-300.zh.png`、`backup-mnemonic-raw-entropy-300.zh.png`
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/new-mnemonic-hex.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，HEX 提示页和输入页截图已生成
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/home-options.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，原始熵、Stackbit、Tinyseed 截图位置正确
  - 定向回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_mnemonic_backup.py -q`
  - 结果：`60 passed`
  - Web3/QR 回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py -q`
  - 结果：`53 passed`
  - 自检/i18n 回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_self_check.py tests/test_i18n.py -q`
  - 结果：`4 passed`
- 2026-05-05 本轮继续迁移 `扑克牌创建`：
  - `src/krux/pages/login.py`：新增 `新助记词 -> 扑克牌创建`
  - 卡牌规则：匹配树莓派参考的 iancoleman `Card [A2-9TJQK][CDHS]` 模式，识别 `A23456789TJQK` 点数和 `C/D/H/S` 花色
  - 熵计算：使用树莓派参考的 `CARD_EVENT_BITS` 计算可用 bit；够目标词数所需 bit 后，对规范化卡牌文本做 `SHA256`，再截取 16/32 字节生成 12/24 词 BIP39
  - UI：按 Amigo 触摸屏重做两步输入，先选点数，再选花色；页面显示 `当前bit/所需bit`、支持删除、支持继续编辑和核对页
  - 24 词注意：单副 52 张牌约 232 bits，不够 24 词的 256 bits；当前固件允许继续输入多副牌/额外牌序，但文档仍提醒不建议单副牌做 24 词
  - 新增测试：`tests/pages/test_login.py::test_new_key_from_card_entropy`
  - 新增截图序列：`simulator/sequences/new-mnemonic-cards.txt`
  - 更新截图序列：`simulator/sequences/new-mnemonic-hex.txt` 随 `扑克牌创建` 入口后移
  - 更新截图序列：`simulator/sequences/new-mnemonic-options.txt` 中 D6 入口位置随 `扑克牌创建` 后移
  - 已生成新截图：`new-mnemonic-via-cards-prompt-300.zh.png`、`new-mnemonic-via-cards-rank-input-300.zh.png`、`new-mnemonic-via-cards-suit-input-300.zh.png`
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/new-mnemonic-cards.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，扑克牌提示页、点数输入页、花色输入页截图已生成
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/new-mnemonic-hex.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，HEX 入口随新菜单位置更新后仍正确
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/new-mnemonic-options.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，拍照、D6、D20 旧截图路径在新增 `扑克牌创建` 后仍正确
  - 合并回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_mnemonic_backup.py tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py tests/pages/test_self_check.py tests/test_i18n.py -q`
  - 结果：`118 passed`
- 2026-05-05 本轮继续迁移 `钢板打孔数字`：
  - `src/krux/pages/home_pages/mnemonic_backup.py`：新增 `备份助记词 -> 其他格式 -> 钢板打孔数字`
  - 打孔规则：按树莓派 `mnemonic_steel.py` 的 0-based BIP39 序号规则实现，序号范围 `0-2047`
  - 位权规则：使用 `1 2 4 8 16 32 | 64 128 256 512 1024`，对每个单词的 0-based 序号拆出需要打孔的权重
  - 显示规则：Amigo 每屏显示 6 个词，每个词显示 `词序 单词 #0000`、`前6位`、`后5位`，方便对照 3.5 寸触摸屏实际打孔
  - 注意：现在 `数字` 备份和 `钢板打孔数字` 都已经是 0-based `0-2047`，只是显示形式不同
  - 新增测试：`tests/pages/home_pages/test_mnemonic_backup.py::test_display_steel_punch_numbers`
  - 更新截图序列：`simulator/sequences/home-options.txt` 增加 `backup-mnemonic-steel-punch-1.png` 和 `backup-mnemonic-steel-punch-2.png`
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/home-options.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，新增 `backup-mnemonic-steel-punch-1-300.zh.png` 和 `backup-mnemonic-steel-punch-2-300.zh.png`，已人工查看排版
  - 定向回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/home_pages/test_mnemonic_backup.py::test_display_steel_punch_numbers -q`
  - 结果：`1 passed`
  - 合并回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_mnemonic_backup.py tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py tests/pages/test_self_check.py tests/test_i18n.py -q`
  - 结果：`119 passed`
- 2026-05-06 本轮继续对齐 TinySeed：
  - `src/krux/pages/tiny_seed.py`：Amigo 侧 TinySeed 已按 `0-2047` / `11` 位重新分支，手动输入、自动校验、打印和扫描还原都共用同一套 Amigo 编号体系
  - `tests/pages/test_tiny_seed.py::test_scan_tiny_seed_24w`：补成 Amigo 兼容的 0-based 样本，避免扫描测试继续沿用树莓派 1-based 样本
  - 仍要继续看的点：深层页面里少量输入提示的中文标点和措辞再统一一轮
- 2026-05-05 本轮继续迁移 `二次助记词`：
  - 新增 `src/krux/pages/home_pages/secondary_mnemonic.py`
  - `src/krux/pages/home_pages/home.py`：`助记词工具` 菜单新增 `二次助记词`
  - 默认二次加密：使用树莓派默认移动数字 `+8 +7 +6 +7 +6 +7 +7 +3 +5 +2 +4 +2`
  - 默认二次还原：使用相反字面运算 `-8 -7 -6 -7 -6 -7 -7 -3 -5 -2 -4 -2`
  - 自定义运算：支持 12 组空格/逗号分隔输入，例如 `+8 -7 +6 ...`，支持 `+ - * /`，其中乘除会提示有信息丢失风险
  - 当前限制：第一版只支持树莓派同款 12 词路线；24 词会提示 `二次助记词第一版只支持12词`
  - 重要差异：移位后的假助记词可能 BIP39 checksum 无效，Krux `Key` 不能把无效假助记词当钱包加载；因此 Amigo 第一版会显示假助记词用于抄写/钢板备份，但不会强行加载无效假助记词
  - 新增测试：`tests/pages/home_pages/test_secondary_mnemonic.py`
  - 更新测试：`tests/pages/home_pages/test_home.py` 中 BIP85 / XOR 菜单导航随新增 `二次助记词` 调整
  - 新增截图序列：`simulator/sequences/secondary-mnemonic.txt`
  - 更新截图脚本：`simulator/generate-device-screenshots.sh` 增加 `secondary-mnemonic.txt`
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/secondary-mnemonic.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，已人工查看 `secondary-mnemonic-wallet-menu-300.zh.png`、`secondary-mnemonic-menu-300.zh.png`、`secondary-mnemonic-default-encrypt-result-300.zh.png`
  - 定向回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/home_pages/test_secondary_mnemonic.py tests/pages/home_pages/test_home.py::test_load_bip85_from_wallet_menu tests/pages/home_pages/test_home.py::test_load_xor_not_derive tests/pages/home_pages/test_home.py::test_load_xor_from_wallet_menu -q`
  - 结果：`6 passed`
  - 合并回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_home.py tests/pages/home_pages/test_mnemonic_backup.py tests/pages/home_pages/test_secondary_mnemonic.py tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py tests/pages/test_self_check.py tests/test_i18n.py -q`
  - 结果：`150 passed`
- 2026-05-05 本轮继续补齐 `钢板二次还原`：
  - `src/krux/pages/mnemonic_loader.py`：新增 `加载助记词 -> 手动输入 -> 钢板二次还原`
  - `src/krux/pages/home_pages/secondary_mnemonic.py`：新增钢板打孔位解析函数，可解析 12 组逗号分隔打孔位，也可解析 12 个 0-based BIP39 序号
  - 恢复流程：钢板数字 -> 0-based BIP39 序号 -> 假助记词 -> 默认二次还原 `-8 -7 -6 -7 -6 -7 -7 -3 -5 -2 -4 -2` -> 真实助记词 -> Krux 原生确认/加载流程
  - 已补齐：如果用户用自定义二次加密数字制作钢板，可以选择 `自定义参数还原`，再输入 12 组还原参数
  - 新增测试：`tests/pages/home_pages/test_secondary_mnemonic.py::test_restore_secondary_from_steel_plate_numbers`
  - 新增测试：`tests/pages/home_pages/test_secondary_mnemonic.py::test_restore_secondary_from_steel_plate_numbers_custom`
  - 更新截图序列：`simulator/sequences/load-mnemonic-options.txt` 中 Tinyseed 入口随 `钢板二次还原` 后移
  - 新增截图序列：`simulator/sequences/secondary-steel-restore.txt`
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/load-mnemonic-options.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，已人工查看 `load-mnemonic-manual-options-300.zh.png` 中显示 `钢板二次还原`
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/secondary-steel-restore.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，已人工查看 `secondary-steel-restore-menu-300.zh.png`
  - 定向回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/home_pages/test_secondary_mnemonic.py tests/pages/test_login.py -q`
  - 结果：`55 passed`
  - 合并回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_home.py tests/pages/home_pages/test_mnemonic_backup.py tests/pages/home_pages/test_secondary_mnemonic.py tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py tests/pages/test_self_check.py tests/test_i18n.py -q`
  - 结果：`151 passed`
- 2026-05-05 本轮继续扩展 `15/18/21` 词：
  - `src/krux/pages/__init__.py`：助记词长度选择增加 `15 词`、`18 词`、`21 词`，并保留 `12 词` / `24 词` 原顺序，避免旧流程按钮序列跑偏
  - `src/krux/key.py`：最后一词候选和自动补最后一词支持 14/17/20 个前置词，即可生成 15/18/21 词合法校验码
  - `src/krux/pages/login.py`：拍照、扑克牌、16进制创建按 15/18/21 词分别截取 `20/24/28` 字节熵
  - `src/krux/pages/new_mnemonic/dice_rolls.py`：D6/D20 骰子创建增加 15/18/21 词的最小熵和最少掷骰次数
  - `src/krux/pages/mnemonic_loader.py`：新建手动单词、二维码、CompactSeedQR、SeedQR 导入允许 15/18/21 词
  - `src/krux/pages/mnemonic_editor.py`：助记词编辑页支持 15/18/21 词显示和导航，Amigo 上超过 12 词时用左右两列显示剩余词
  - `src/krux/pages/encryption_ui.py`：加密助记词读取允许 15/18/21 词
  - 新增/扩展测试：`tests/pages/test_login.py::test_new_key_from_hexadecimal_entropy` 覆盖 12/15/18/21/24 词
  - 新增截图：`simulator/sequences/new-mnemonic-hex.txt` 增加 `new-mnemonic-length-options.png`
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/new-mnemonic-hex.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，已人工查看 `new-mnemonic-length-options-300.zh.png` 中显示 `12/24/15/18/21`
  - 定向回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_secondary_mnemonic.py -q`
  - 结果：`58 passed`
  - 合并回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_home.py tests/pages/home_pages/test_mnemonic_backup.py tests/pages/home_pages/test_secondary_mnemonic.py tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py tests/pages/test_self_check.py tests/test_i18n.py -q`
  - 结果：`155 passed`
- 2026-05-05 本轮继续迁移 `开机数字口令锁`：
  - 新增 `src/krux/pages/boot_lock.py`
  - `src/boot.py`：在防篡改检查后、登录菜单前增加 `boot_lock_verification(ctx)`；如果已配置开机口令，必须先解锁才能进入登录菜单
  - `src/krux/pages/settings_page.py`：`设置 -> 安全` 增加 `开机口令锁`，可进入 `功能说明`、`开启开机口令`、`修改开机口令`、`关闭开机口令`
  - `src/krux/pages/__init__.py`：`capture_from_keypad()` 增加 `mask_buffer=True`，数字口令输入时显示 `*`，避免在 3.5 寸屏幕上明文暴露
  - 存储方案：使用 `/flash/boot_lock.json`，保存 `version/iterations/salt/hash`；哈希使用 `PBKDF2-HMAC-SHA256`，盐包含固定上下文、设备 `unique_id()` 和随机盐
  - 安全边界：该功能是本机便捷启动门禁，适合防误触/防普通误用；它不是硬件安全芯片，也不等同树莓派 `BootLockStore` 的 Linux 启动分区加密方案
  - 恢复出厂：`SettingsPage.restore_settings()` 会同时删除 `/flash/boot_lock.json`
  - 新增测试：`tests/pages/test_boot_lock.py`
  - 更新测试：`tests/pages/test_settings_page.py`，恢复出厂断言同步检查删除 boot lock 文件，并将默认中文环境下的设置提示改为翻译断言
  - 新增截图序列：`simulator/sequences/boot-lock-setup.txt`
  - 新增截图序列：`simulator/sequences/boot-lock-unlock.txt`
  - 更新截图脚本：`simulator/generate-device-screenshots.sh` 会创建 `simulator/flash`，先跑开机口令设置和解锁截图，再删除 `simulator/flash/boot_lock.json`，避免影响后续截图序列
  - 更新截图序列：`simulator/sequences/all-settings.txt` 随安全菜单新增 `开机口令锁` 后移返回位置
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/boot-lock-setup.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，已人工查看开启菜单、功能说明、警告、输入新口令、确认口令、保存成功截图
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/boot-lock-unlock.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，已人工查看解锁数字键盘、错误重试、解锁成功、返回中文登录菜单截图
  - 截图序列验证：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python simulator/simulator.py --sequence sequences/all-settings.txt --sd --device maixpy_amigo`
  - 结果：命令成功退出，新增安全菜单项后设置截图序列未跑偏
  - 定向回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_boot_lock.py tests/pages/test_settings_page.py tests/pages/test_login.py -q`
  - 结果：`76 passed`
  - 合并回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_home.py tests/pages/home_pages/test_mnemonic_backup.py tests/pages/home_pages/test_secondary_mnemonic.py tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py tests/pages/test_self_check.py tests/test_i18n.py tests/pages/test_boot_lock.py tests/pages/test_settings_page.py -q`
  - 结果：`178 passed`
  - 当前截图目录检查：`simulator/screenshots/` 中有 `171` 张 `*-300.zh.png`，无 `*smartcard*` 截图
- 2026-05-05 本轮继续按用户要求优化首页和截图路径：
  - `src/krux/pages/home_pages/home.py`：首页改为树莓派式顺序 `扫码签名 / 助记词工具 / 连接钱包 / 固件自检`
  - `连接钱包` 聚合 `Web3 连接钱包`、`导出 BTC xpub/zpub`、`地址 / 扫码验址`、`钱包描述符`
  - `助记词工具` 聚合 `备份 / 核对助记词`、`BIP85 子助记词`、`二次助记词`、`助记词 XOR`、`密码短语`、`自定义`
  - 已同步更新旧首页顺序相关截图序列：`web3*.txt`、`web3-connect-*.txt`、`home-options.txt`、`encrypt-mnemonic.txt`、`self-check-home.txt`、`extended-public-key-*.txt`、`wallet-descriptor-*.txt`、`bip85.txt`、`mnemonic-xor.txt`、`secondary-mnemonic.txt`、`scan-address.txt`、`list-address.txt`、`export-address.txt`、`sign-psbt.txt`、`sign-message*.txt`
  - 已跑通关键模拟器截图序列：`web3.txt`、`home-options.txt`、`self-check-home.txt`、`secondary-mnemonic.txt`、`bip85.txt`、`mnemonic-xor.txt`、`extended-public-key-wpkh.txt`、`web3-connect-okx.txt`、`web3-sign.txt`、`web3-typed-transaction.txt`、`scan-address.txt`、`list-address.txt`、`export-address.txt`、`wallet-descriptor-wpkh.txt`、`wallet-descriptor-wsh.txt`、`sign-psbt.txt`、`sign-message.txt`
  - 已人工查看关键截图：`home-options-300.zh.png`、`mnemonic-tools-menu-300.zh.png`、`web3-connect-center-300.zh.png`、`self-check-home-menu-300.zh.png`、`address-menu-300.zh.png`
  - 完整截图回归：`bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
  - 完整截图结果：命令成功退出，`simulator/screenshots/` 中有 `172` 张 `*-300.zh.png`，无 `*smartcard*` 截图
  - 大回归命令：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_home.py tests/pages/home_pages/test_mnemonic_backup.py tests/pages/home_pages/test_secondary_mnemonic.py tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py tests/pages/test_self_check.py tests/test_i18n.py tests/pages/test_boot_lock.py tests/pages/test_settings_page.py -q`
  - 大回归结果：`178 passed`
- 之前对话里出现过的 `ghp_...` GitHub token 按泄露处理，不要复用，也不要写回文档或代码

## 已知还差

- 除智能卡外，树莓派固件的核心功能路线已经迁移或由 Krux 原生能力覆盖到 Amigo 第一版；下一步不要再重复做智能卡方向，优先做深层页面中文化、3.5 寸触摸屏排版细化和真实固件构建前验证。
- 不要把 Krux 原生的 `Mnemonic XOR`、`Encrypted`、`Stackbit 1248` 直接说成已经等同树莓派的 `二次加密/二次还原/钢板打孔数字`。这些已经新做树莓派兼容第一版，默认参数和自定义参数的钢板恢复都已具备。
- `扑克牌创建`、`16进制创建`、拍照、骰子、手动单词创建已开放 15/18/21 词；但 Tinyseed/Stackbit 这类专用金属格式仍保持 Krux 原生 12/24 词能力，不能说所有专用备份格式都已支持 15/18/21。
- 当前不再做智能卡桥接截图
- 已重跑完整 Amigo 中文截图；后续如果改首页顺序、Web3 文案或扫码节奏，需要重新跑对应模拟器截图
- 硬件差异最大风险：读卡器直连不是简单移植页面。树莓派靠 Linux + PC/SC，Amigo 固件没有这套驱动栈。
- 如果用户继续要求“机器本体直接读卡”，下一位接手者先不要直接写 UI，应先做硬件可行性验证。
- 下一位接手者优先继续做截图人工挑查和深层页面中文排版，然后再进入 Amigo 固件构建。

## 关键文件

- Web3 主逻辑：`src/krux/web3.py`
- Amigo Web3 页面：`src/krux/pages/home_pages/web3_ui.py`
- Amigo 自检页面：`src/krux/pages/self_check.py`
- Amigo 开机口令页：`src/krux/pages/boot_lock.py`
- Amigo 开机入口：`src/boot.py`
- 设置页安全菜单：`src/krux/pages/settings_page.py`
- 登录菜单入口：`src/krux/pages/login.py`
- 已加载助记词后的首页入口：`src/krux/pages/home_pages/home.py`
- 二维码解析与中转分片：`src/krux/qr.py`
- 模拟器脚本：`simulator/generate-device-screenshots.sh`
- 自检测试：`tests/pages/test_self_check.py`
- Web3 序列：
  - `simulator/sequences/web3*.txt`
- 开机口令截图序列：
  - `simulator/sequences/boot-lock-setup.txt`
  - `simulator/sequences/boot-lock-unlock.txt`

## 回归命令

```bash
PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src \
.venv/bin/pytest tests/test_web3.py \
tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py \
tests/pages/test_self_check.py -q
```

```bash
bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN
```

## 2026-05-06 本轮继续项

- 这一轮继续把深层页的 Amigo 中文化收尾到位：
  - `src/krux/pages/settings_page.py`：防篡改码、恢复出厂、SD 卡存储、主题重启、LCD 类型确认等提示都改成 Amigo 更自然的中文；`settings.security` 里也继续保留 `开机口令锁`
  - `src/krux/pages/home_pages/wallet_descriptor.py`：钱包描述符的加载、切换、找零地址警告、策略/网络/脚本类型不匹配提示都改成中文，并把 Amigo 的明文/加密导出菜单做成双行按钮
  - `src/krux/pages/home_pages/sign_message_ui.py`：`Sign?`、原始哈希警告、签名导出菜单、签名结果、公钥展示都改成中文，Amigo 上不再冒英文短词
  - `src/krux/translations/zh.py` 和 `i18n/translations/zh-CN.json`：把 `Changes will last until shutdown.` 的中文润色成 `更改会一直保留到关机。`
  - 定向回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_settings_page.py tests/pages/home_pages/test_wallet_descriptor.py tests/pages/home_pages/test_sign_message_ui.py -q`
  - 结果：`39 passed`
  - 完整 Amigo 截图回归已重新跑通：`bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
  - 这次回归重点覆盖了设置页、钱包描述符、签名页和 Web3/自检/助记词相关中文界面，脚本最终正常退出

- 已继续做深层页面中文润色和 3.5 寸触摸排版：
  - `src/krux/pages/wallet_settings.py`：钱包网络、单签/多签、Miniscript、脚本类型菜单改为可翻译文案；顶部网络名在中文界面显示为 `主网 / 测试网`
  - `src/krux/pages/flash_tools.py`：`TC Flash Hash` 详情页标题改为中文 `闪存校验哈希`
  - `src/krux/pages/file_operations.py`：通用保存页的 `保存到 SD 卡`、`文件名`、`覆盖`、`处理中`、`已保存到 SD 卡`、`未检测到 SD 卡` 改为 Amigo 中文提示
  - `src/krux/pages/home_pages/home.py`：首页二级中心菜单改为 Amigo 双行大触摸按钮，覆盖 `扫码签名`、`连接钱包`、`助记词工具`
  - `src/krux/pages/home_pages/home.py`：PSBT 复核里的继续确认框补成中文，避免 Amigo 在路径不匹配后弹出英文 `Proceed?`
  - `src/krux/pages/wallet_settings.py`：派生路径里“非硬化节点”警告改成中文，避免深层设置页继续露出英文提示
  - `src/krux/pages/mnemonic_loader.py`：助记词导入的摄像头、手动输入、编号输入细分菜单改为双行大按钮
  - `src/krux/pages/home_pages/mnemonic_backup.py`：助记词二维码备份、其他格式、编号显示菜单改为双行大按钮
  - `src/krux/pages/home_pages/bip85.py`：BIP85 Base64 密码导出结果页改为双行大按钮
  - `src/krux/pages/home_pages/wallet_descriptor.py`：钱包描述符导出选项改为双行大按钮
  - `i18n/translations/zh-CN.json`：润色 `钱包描述符`、`仍要继续？`、`从已保存记录加载`、`闪存校验哈希`、`主网 / 测试网`、脚本类型等中文
- 已重新执行翻译生成：
  - `PYTHONPATH=src .venv/bin/python i18n/i18n.py prettify bake validate`
  - 当前结果：所有语言 `validate OK`
- 2026-05-06 继续收尾：
  - `src/krux/pages/home_pages/wallet_descriptor.py`：把钱包描述符的明文/加密入口补成更自然的中文，避免中文界面里继续冒出裸 `Plaintext`
  - `src/krux/pages/qr_view.py`：Amigo 的二维码查看器菜单改成双行中文按钮，并在界面上把 `SeedQR` 默认标题显示成中文
  - `src/krux/pages/print_page.py`：打印助记词标题改成中文输出，十进制 / 十六进制 / 八进制后缀也一起本地化
  - 先继续跑对应测试，再重新生成 Amigo 截图验证大屏效果
- 已执行 Amigo 关键回归：
  - 命令：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py tests/pages/home_pages/test_home.py tests/pages/home_pages/test_mnemonic_backup.py tests/pages/home_pages/test_secondary_mnemonic.py tests/test_web3.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_capture.py tests/pages/test_self_check.py tests/test_i18n.py tests/pages/test_boot_lock.py tests/pages/test_settings_page.py -q`
  - 结果：`178 passed`
- 已重新生成完整 Amigo 中文截图：
  - 命令：`bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
  - 结果：成功生成 `172` 张 `*-300.zh.png`
  - 已确认：`simulator/screenshots/` 没有 `*smartcard*` 截图残留
- 已按用户最新要求构建 Android debug APK：
  - Android 工程：`/home/ak/123/satochip-signer`
  - 构建命令：`JAVA_HOME=/home/ak/.local-jdks/jdk-17 ANDROID_HOME=/home/ak/Android/Sdk ANDROID_SDK_ROOT=/home/ak/Android/Sdk ./gradlew --no-daemon --max-workers=1 -Dorg.gradle.jvmargs='-Xmx1536m -Dfile.encoding=UTF-8' -Dkotlin.daemon.jvmargs='-Xmx768m' :app:assembleDebug`
  - 结果：`BUILD SUCCESSFUL`
  - APK：`/home/ak/123/satochip-signer/dist/satochip-signer-debug.apk`
  - SHA256：`b8dd41dd32d056b37a2ded8dc15ad2d2a8f6994199c1a20aa66cc995866903d7`
  - 说明：这是 Android debug 证书签名 APK；Amigo 固件主线仍不恢复智能卡功能
- Amigo 真机固件包状态：
  - 当前主线不再依赖 Docker 做交付包，默认使用 `firmware/scripts/build-amigo-official-base.sh`
  - 这个脚本走官方 Amigo 的 MaixPy / Kboot 底座，把当前 `src/krux` 和 vendor 依赖冻结进去
  - 正式交付包固定看 `build/amigo-official-base-kboot.kfpkg`，不要再看旧的 `build/amigo-custom-kboot.kfpkg`
- 2026-05-06 继续中文化收尾：
  - `src/krux/pages/mnemonic_loader.py`、`src/krux/pages/home_pages/bip85.py`、`src/krux/pages/home_pages/secondary_mnemonic.py`、`src/krux/pages/home_pages/mnemonic_backup.py`、`src/krux/pages/login.py`、`src/krux/pages/self_check.py` 继续统一 Amigo 深层页面中文文案
  - 重点处理更自然的说法：去掉 `HEX` 等英文碎片，统一 `导入 / 生成 / 位移 / 序号` 的按钮措辞，减少 3.5 寸屏上的生硬长句
  - 这一轮仍然只动 Amigo 固件主线，不恢复智能卡菜单
  - 改完后继续跑对应测试和截图，再决定是否进入下一批页面细化
  - 这次把 `0-2047` 口径继续往下统一到所有 BIP39 编号输入提示，`十进制 / 十六进制 / 八进制` 的中文说明都改成零基准，避免不同页面和不同语言再出现 `1-2048` 的旧说法
  - `src/krux/pages/file_operations.py`、`src/krux/pages/home_pages/home.py`、`src/krux/pages/wallet_settings.py` 又补了一轮通用保存页和深层确认页中文化，后面要继续扫剩余页面是否还有 Amigo 上会露出的英文确认框
  - `tests/pages/test_wallet_settings.py` 的断言已同步为当前更自然的中文派生路径警告文案
  - 最近一次回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_wallet_settings.py tests/pages/home_pages/test_pub_key_view.py tests/pages/home_pages/test_addresses.py tests/pages/test_qr_view.py tests/pages/test_file_operations.py -q`
  - 结果：`50 passed`
  - 这次继续扫剩余页面时又把 `src/krux/pages/print_page.py`、`src/krux/pages/qr_capture.py`、`src/krux/pages/device_tests.py` 的 Amigo 入口做了更直观的中文布局和按钮文案，主要是打印页、扫码页和自检页的加载/模式/结果提示
  - 最近一次回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_print_page.py tests/pages/test_qr_capture.py tests/pages/test_device_tests.py -q`
  - 结果：`46 passed`
  - 最近一次完整截图回归：`bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
  - 结果：命令成功退出，`simulator/screenshots/` 已重新生成本轮 Amigo 中文截图
- 这次完整截图回归里，`print_page.py` 的打印/导出提示、`qr_capture.py` 的加载与模式提示、`device_tests.py` 的自检菜单与结果页都已经跟着新中文布局一起验证过了
- 2026-05-06 本轮继续深层页面中文润色：
  - `src/krux/pages/home_pages/bip85.py` 把 Amigo 的 BIP85 导出页改成更短的中文按钮与中文信息框，`BIP85 密码`、`二维码查看`、`索引`、`长度` 都按 3.5 寸触摸屏重新整理
  - `src/krux/pages/home_pages/mnemonic_backup.py` 把 `其他格式` 里的 `助记词全文`、`钢板打孔`、`钢板 1248`、`点阵备份` 入口重新压缩成更适合大屏点按的中文文案，并把钢板页标题改成更短的 `钢板打孔数字 %d/%d`
  - `src/krux/pages/stack_1248.py`、`src/krux/pages/tiny_seed.py` 继续把专用备份页标题改成 Amigo 中文，避免深层页面还露出 `Stackbit 1248` / `Tinyseed` 这种英文页头
  - `src/krux/pages/mnemonic_loader.py` 的摄像头导入和手动导入菜单也顺手改成中文入口，`点阵备份`、`钢板 1248` 这类选项更像 Amigo 原生菜单
  - `tests/pages/home_pages/test_bip85.py`、`tests/pages/home_pages/test_mnemonic_backup.py` 已同步新的中文标题、信息框和钢板位权断言
  - 最近一次回归：
    - `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/home_pages/test_bip85.py tests/pages/home_pages/test_mnemonic_backup.py -q`
    - `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_login.py -q`
  - 结果：`15 passed`、`53 passed`

## 最新回归

- 2026-05-09 真机刷机记录：
- 官方回退：下载并校验官方 `krux-v26.04.0.zip`，使用 `/tmp/krux-official-v26.04.0/krux-v26.04.0/maixpy_amigo/kboot.kfpkg` 低速 `115200` 刷入 `Sipeed Matrix Amigo` 成功，屏幕重新亮起。
- 触摸排查：Amigo 是触摸屏；Krux v24.03.0 之后要求机身内部触摸 IRQ 小开关拨到上方。用户已打开后盖拨好，触摸问题按硬件开关路线处理。
- 自定义整包：用官方 `v26.04.0` 的 `bootloader_lo.bin`、`bootloader_hi.bin`、`config.bin` 作为壳，把本仓库自定义 `firmware/MaixPy/projects/maixpy_amigo/build/firmware.bin` 打进 `build/amigo-custom-kboot.kfpkg`。
- 自定义整包 SHA256：`d43574ae512309c09f35a1a8b54066b6787fe71495a0f58f00b6bf0366d2c6e2`。
- 自定义刷入：使用 `python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/ttyUSB1 build/amigo-custom-kboot.kfpkg` 成功写入启动器、配置区和 `0x00080000` 应用区，最后显示 `Flashed 904997 B (00080000~0015FFFF)` 并自动重启。
- 结果修正：上述自定义整包刷入后真机黑屏。不要再继续刷这份 `build/amigo-custom-kboot.kfpkg` 作为交付固件。
- 根因判断：本地自定义 `firmware/MaixPy/projects/maixpy_amigo/build/firmware.bin` 只有 `904960` 字节，而官方 `v26.04.0` 的 `maixpy_amigo/firmware.bin` 是 `1746688` 字节；二者不是同一条完整 Amigo 官方构建链路。旧自定义小固件不能当作“官方固件加功能”的交付基线。
- 已恢复：随后重新刷回官方 `/tmp/krux-official-v26.04.0/krux-v26.04.0/maixpy_amigo/kboot.kfpkg`，低速 `115200` 完整写入 `1746725 B (00080000~0022FFFF)` 并自动重启，设备回到官方可亮屏状态。
- 重要教训：不要把 `maixpy.bin` 单独写到 `0x00280000` 当作普通交付刷机。Krux 的 Kboot 配置默认从 `0x00080000` 加载 `firmware.bin`，首刷和正式交付必须刷完整 `kboot.kfpkg`。
- 后续正确路线：以官方 Amigo 完整源码/官方 `v26.04.0` release 为底座，把中文、菜单、Web3、助记词工具等功能合进去，再通过完整 Amigo 构建产出新的 `firmware.bin` 和 `kboot.kfpkg`。没有得到接近官方尺寸并能真机亮屏的完整包前，不要再刷旧的 `904960` 字节产物。
- 2026-05-09 官方底座构建成功：
- 构建命令：`MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh`
- 结果：MaixPy 主固件成功生成，`firmware.bin` 大小 `1876736` 字节，已超过脚本安全阈值 `1200000` 字节，和官方 `1746688` 字节属于同一量级。
- Kboot 修正：`firmware/Kboot/build/BUILD.sh` 增加 `KBOOT_MAKE_JOBS=1` 和 `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`，用于低负载构建并兼容当前仓库 `.venv/bin/cmake 4.3.2`。
- 完整交付包：`build/amigo-official-base-kboot.kfpkg`，大小 `926547` 字节，SHA256 `ecdfec0905a65655faf9c5d8db0bf6abab81b6e7b6a11a888952f923f9298069`。
- 包内检查：`unzip -l build/amigo-official-base-kboot.kfpkg` 显示 `firmware.bin` 为 `1876736` 字节，刷写地址仍是官方 Kboot 的 `524288 / 0x00080000`。
- 固件镜像：`build/amigo-official-base-firmware.bin`，大小 `1876736` 字节，SHA256 `9083c678af2b01ec51ca232d6bf6e919cd5c8c2cfbe14719a1f862a98686c638`。
- 关键回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/test_web3.py tests/pages/home_pages/test_web3_ui.py -q`，结果 `32 passed`。
- 语法检查：`python3 -m py_compile src/krux/web3.py`、`bash -n firmware/scripts/build-amigo-official-base.sh`、`python3 -m py_compile firmware/MaixPy/tools/cmake/project.py` 均通过。
- 2026-05-09 自定义官方底座包真机刷入成功：
- 串口识别：`/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0 -> /dev/ttyUSB0`，`if01-port0 -> /dev/ttyUSB1`。
- 实际刷机命令：`sudo python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/ttyUSB1 build/amigo-official-base-kboot.kfpkg`。
- 权限修正：不用 `sudo` 会出现 `Permission denied: '/dev/ttyUSB1'`，教程已改成 `sudo` 命令，并补充 `dialout` 组说明。
- 刷机结果：Ktool 成功写入 bootloader、配置区和主固件区，主固件显示 `Flashed 1876773 B [29 chunks of 65536B] (00080000~0024FFFF) in 183.019s`，随后显示 `Rebooting...`。
- 2026-05-09 后续黑屏诊断：
- 自定义官方底座包仍会黑屏：`build/amigo-official-base-kboot.kfpkg` SHA256 `35e309d6500fd1cc58bc86d9155ccd0ac4b357a6fbb3a1eab9dfadece85dfd1f`，不要交付。
- 已再次刷回官方救机包：`/tmp/krux-official-v26.04.0/krux-v26.04.0/maixpy_amigo/kboot.kfpkg` SHA256 `2f6afc012978f460b1656a4d8e79271eb65a643551fcbe5f57194a2a76de58f2`，刷写日志显示完整写入并重启。
- 已生成两版最小 LCD/背光诊断包：第一版 `668388d88713c10b216d189854ab0ec625c734014bca51256d93484449670004`，第二版自动轮询 LCD 参数 `54dc7c9366ae2481fb5cc771ec64e02afc10afeeecb7757ecfea519174c5a2bc`；第二版刷入后如果能看到彩色循环页或 `AMIGO DIAG BOOT OK`，说明 MaixPy 和 LCD/背光底层能工作，黑屏更可能集中在 Krux Python 启动层；如果仍黑屏，先立刻刷回官方包救机，再排查本机 MaixPy/K210/LCD 编译环境或硬件连接。
- 当前电脑已重新识别到 Amigo USB 串口，`/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 和 `/dev/ttyUSB1` 均存在。下一步只看用户肉眼屏幕结果。
- 2026-05-10 Sipeed 开发板官方系统恢复：
- 不再把 Krux release 包称为“开发板官方系统”。本轮按 Sipeed 下载站的 MaixPy Amigo 专用固件恢复，下载到 `build/sipeed-official/maixpy_v0.6.3_2_gd8901fd22_amigo_tft_defaults.bin`，大小 `2077376` 字节，SHA256 `e3e15ea8dacff49751405f94215c1252653343f47823fba781990279b6473d56`；同时保留 `amigo_ips_defaults.bin` 作为屏幕类型备用包。
- 已先整片擦除 16MB SPI Flash，再用低速 `115200` 把 `amigo_tft_defaults.bin` 写入 `0x00000000~0x001FFFFF`，写入大小 `2077413 B`，随后自动重启。
- 串口确认已进入真正 Sipeed MaixPy 官方系统，启动横幅为 `MAIXPY`，`board.config["type"]` 为 `amigo_tft`，屏幕参数为 `480x320 / dir=40 / invert=0 / lcd_type=1`。
- 关键硬件差异：Sipeed 官方系统上报按键脚位为 `ENTER=23 / NEXT=20 / BACK=31`，而仓库原 Amigo Krux 配置是 `16 / 20 / 23`。因此按键无效或错位不是用户操作问题，必须按官方脚位修正。
- 已修正 `firmware/MaixPy/projects/maixpy_amigo/builtin_py/board.py` 和 `src/board.py`：`BUTTON_A=23`、`BUTTON_B=20`、`BUTTON_C=31`，SD 卡 `cs=26`，并记录 `variant=amigo_tft`。
- 已废弃的触摸结论：曾尝试给 Amigo 增加 `touch_transform=rotate_cw`，但 2026-05-10 晚间真机反馈触摸仍乱。本结论已撤销，当前代码恢复官方触摸坐标处理；后续不要按这里的历史记录重新加 `rotate_cw`。
- 轻量验证：`python3 -m py_compile src/board.py src/krux/touch.py src/krux/input.py firmware/MaixPy/projects/maixpy_amigo/builtin_py/board.py` 通过；`PYTHONPATH=src .venv/bin/pytest tests/test_touch.py tests/test_input.py -q` 结果 `88 passed`。
- 2026-05-06：重新 bake `zh-CN` 并清理 Amigo 硬编码中文提示中的尾部 `！`，避免 3.5 寸屏出现方块 glyph。
- 2026-05-06：重新运行 `bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`。
- 结果：成功退出，生成 `173` 张 `300.zh.png` 中文截图，空白/黑屏筛查为 `0`。
- 关键截图：`simulator/screenshots/wallet-descriptor-tr-minis-4-300.zh.png` 已显示为 `钱包描述符已加载`，无尾部方块。
- 单测：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/home_pages/test_addresses.py tests/pages/home_pages/test_secondary_mnemonic.py tests/pages/home_pages/test_home.py tests/pages/test_print_page.py -q`
- 结果：`51 passed`
- 2026-05-06：`tests/pages/test_login.py` 的十六进制/八进制 `possible_letters` 用例已改成直接断言 `_load_key_from_keypad` 传入的闭包边界，避免继续硬跑完整 UI 后被自动补全和确认框拖死；当前也已把数字输入相关测试统一到 `0-2047` 口径。
- 2026-05-06：`simulator/sequences/qr-transcript.txt` 已从容易跳进打印分支的 `Datum` 路径改成 Amigo 上更稳的助记词备份二维码路径，`standard / lines / zoomed / regions / grided / qr-viewer` 六张截图已重新验证能正常产出。
- 2026-05-11 真机显示止血：
  - 用户反馈真机上颜色、横线、文字和 UI 全部异常，连助记词英文和横线都显示断续。结论：不能再按“缺中文字库”方向修，先恢复官方 Amigo 显示路径。
  - `src/krux/display.py`：Amigo 启动强制使用官方 release 显示参数 `lcd.init(invert=True, lcd_type=0)`、`lcd.mirror(True)`、`lcd.bgr_to_rgb(True)`，不再读取旧固件可能写入闪存的坏显示设置。
  - `src/krux/pages/__init__.py`：删除自定义 Amigo 卡片式触摸菜单渲染，恢复官方触摸菜单绘制逻辑，避免自定义白底/黑字/卡片边框继续干扰判断。
  - `src/krux/krux_settings.py`：保留 Amigo 默认中文，但显示参数默认值恢复官方口径。
  - `firmware/MaixPy/projects/maixpy_amigo/builtin_py/board.py`：按钮脚位已退回当前仓库官方 Amigo 基线，暂不继续为了坏按键改脚位。
  - 回归测试：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/python -m pytest -q tests/pages/test_self_check.py tests/pages/home_pages/test_web3_ui.py tests/pages/test_qr_view.py`
  - 结果：`31 passed`
  - 低负载编译：`MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell` 成功。
  - 新固件：`build/amigo-official-base-firmware.bin`，大小 `1653696` 字节，SHA256 `24f25f1737553374a88c7db3e7d450582aedfe1017da4b5c0fb872815bd5746d`。
  - 新刷机包：`build/amigo-official-base-official-shell-kboot.kfpkg`，大小 `865532` 字节，SHA256 `3fa43e9ca09b34d8eed62ccaacaf86e9ae9779b41dcf135164e6e4a64315f5e2`。
  - 包检查：`unzip -l build/amigo-official-base-official-shell-kboot.kfpkg` 显示官方壳 5 文件，包内 `firmware.bin` 为 `1653696` 字节。
  - 首次等待固定串口 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 2 分钟，结果 `NO_SIPEED_SERIAL_AFTER_2_MIN`，当时没有刷任何其他端口。
  - 用户重新插线后固定串口出现：`if01-port0 -> /dev/ttyUSB1`。
  - 已刷入：`sudo nice -n 10 python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 build/amigo-official-base-official-shell-kboot.kfpkg`。
  - 刷机结果：主固件写入 `Flashed 1653733 B [26 chunks of 65536B] (00080000~0021FFFF) in 164.726s`，随后 `Rebooting...`。
  - 刷后串口仍存在：`if00 -> /dev/ttyUSB0`，`if01 -> /dev/ttyUSB1`。
  - 下一步只让用户确认一件事：显示是否恢复成官方那样清楚、完整、颜色正常。显示未确认前，不再继续做 UI 美化或功能扩展。
- 2026-05-11 Web3 二维码、Hyperliquid 和 BTC 签名编译前验收：
  - 真机报错 `TypeError("can't convert 'tuple' object to str implicitly")` 的直接风险点已处理：`src/krux/qr.py` 现在把预分页二维码 `list/tuple` 明确标准化为单页字符串/字节流，禁止嵌套 tuple/list 继续传给二维码编码器。
  - 已新增二维码回归：`tests/test_qr.py::test_to_qr_codes_uses_each_pre_split_page` 确认二维码编码器每次只收到单页文本，不会收到整个 `tuple/list`。
  - 已新增 Web3 固定助记词回归：固定助记词 `abandon ... about` 的 EVM 地址必须为 `0x9858EfFD232B4033E47d90003D41EC34EcaEda94`，OKX、Bitget、MetaMask、Rabby、TokenPocket 连接二维码均为可显示字符串页。
  - 已新增 Hyperliquid typed-data 回归：覆盖官方 SDK 形态的 `HyperliquidTransaction:SpotSend` 和 L1 `Agent` typed data；签名后用 secp256k1 从签名恢复地址，必须等于固定助记词地址。
  - Hyperliquid 独立冒烟通过：`SpotSend chain_id=421614 digest=b2866ab10297498ecd1a2f3b05c9792c7d796b9ae30f9537932c692c9fba833f`；`L1 Agent chain_id=1337 digest=5c4c9744212c68e6e2b8a8fccccf13a203b9ecc45ac6664fee435be990ba1e1d`；两者恢复地址均为 `0x9858EfFD232B4033E47d90003D41EC34EcaEda94`。
  - Web3/二维码/UI 定向回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/python -m pytest -q tests/test_qr.py tests/test_web3.py tests/pages/home_pages/test_web3_ui.py`，结果 `46 passed`。
  - BTC PSBT 核心签名回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/python -m pytest -q tests/test_psbt.py -k 'sign_singlesig or sign_multisig or sign_miniscript or sign_tr_miniscript or sign_tr_expanding_multisig or sign_single_1_input_1_output_no_change or sighash'`，结果 `19 passed, 26 deselected`。
  - BTC 首页/扫码签名流程回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/python -m pytest -q tests/pages/home_pages/test_home.py -k 'sign_psbt or sign_wrong_key or sign_review_3_times or sign_zeroes_fingerprint or sign_p2tr_zeroes_fingerprint or sign_high_fee or sign_self or sign_spent_and_self'`，结果 `10 passed, 18 deselected`。
  - BTC 独立冒烟通过：固定助记词签出 P2WPKH PSBT，输出数 `2`，签名后 PSBT `266` 字节，base64 签名结果 `356` 字符，320 宽 PMOFN 二维码可生成。

## 下一步建议

1. 当前优先级：先刷入 2026-05-11 显示止血包，确认 Amigo 显示恢复官方清晰状态。
1. 构建必须低负载：`MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell`。
1. 刷机必须用固定串口：`/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`。
1. 如果显示仍异常，立刻停止改功能，刷回官方 release 包，继续比对 LCD 初始化和 MaixPy 底层。
1. 如果显示恢复正常，再进入 SeedSigner 功能入口完整性检查和截图回归。
1. 让用户先真机确认：屏幕是否进入中文 Krux 首页，触摸菜单是否按点的位置进入，三个实体键是否按当前硬件实际状态工作。
1. 如果触摸仍错位，先检查触摸排线、触摸拨码开关和硬件坐标原始值；不要再直接启用 `touch_transform=rotate_cw`。
1. 如果字体仍缺损，优先排查 LCD 字体渲染或显示参数；当前 Amigo 字库扫描结果是 `missing=0`，不应先盲目继续加字。
1. 重新跑 Amigo 中文截图回归，重点查看开机首页、功能总览、加载钱包、创建钱包、助记词工具、自检、Web3、二维码、地址、设置和加密页面是否还有乱码或难看的折行。
1. 真机确认触摸正常后，再决定是否恢复完整 `kboot.kfpkg` 包；在当前阶段 raw 刷法更接近 Sipeed 开发板官方系统。
1. 继续评估 Tinyseed/Stackbit 等专用金属格式是否要支持 `15/18/21` 词，避免破坏原格式兼容
1. 继续把助记词、BIP85、备份、PSBT 复核页做中文化和 3.5 寸触摸屏排版
1. 每完成一组页面就跑对应测试和截图
1. 不再推进智能卡直连或桥接功能，除非用户重新明确要求
1. 后续如果重新启用 Kboot 包，先用 `unzip -l build/amigo-official-base-kboot.kfpkg` 确认包内 `firmware.bin` 是官方同量级，并先保留 raw 救机路径

## 暂缓和不做

- 不做：直接搬运 PC/SC 智能卡读卡流程
- 不做：外接 ACR39U 读卡器驱动适配
- 不做：Satochip / SeedKeeper 的完整硬件签名链路
- 暂不做：Android 中转 APK 与 Amigo 固件的整套联动协议扩展
- 当前执行项：只维护 Amigo 固件；Android 侧不再作为当前交付主线

原因：

- 用户已明确要求 Amigo 固件不要智能卡相关功能
- Amigo 不是树莓派 Linux 环境，不能直接复用 `pyscard / pcscd / ACR39U`
- 没有确认 USB Host、CCID、T=0/T=1、APDU 层前，不应承诺外接 USB 智能卡读卡器可以工作

## 2026-05-06 继续中文标点收口

- 已把 Amigo 中文界面里容易掉字的全角问号统一换成 ASCII `?`，避免 3.5 寸屏上再出现方块 glyph。
- 重新执行 `i18n/i18n.py bake`，同步更新 `src/krux/translations/zh.py`。
- 重新跑了 `bip85.txt` 和 `wallet-descriptor-wsh.txt` 模拟器序列，确认 `bip85-load-child-300.zh.png` 现在显示 `加载?`。
- 相关回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/home_pages/test_bip85.py tests/pages/home_pages/test_wallet_descriptor.py tests/pages/test_wallet_settings.py tests/test_i18n.py -q`
- 结果：`39 passed`

## 2026-05-06 继续深层中文润色

- 已把 Amigo 的钱包描述符加载提示再缩短一轮，改成两行更紧凑的触摸屏文案，避免 3.5 寸屏上第一屏提示过长。
- 已把 PSBT 里的 `Self-transfer` 中文从 `自转` 润色为 `转回自己`，并把 `Self-transfer or Change` 改为 `转回自己/找零`，让术语更自然也更省空间。
- 已把 `simulator/sequences/tools-descriptor-addresses.txt` 的按键步数修正到真正的 `描述符地址` 入口，现在能稳定抓到 `descriptor-addresses-300.zh.png` 的首次加载提示。
- 后续如果再遇到 PSBT 汇总页或钱包描述符提示页过长，优先继续用短句、换行和 ASCII 标点做收口。

## 下一位 AI 接手步骤

1. 先读本文件，不要从旧聊天里猜状态。
1. 运行 `git status --short`，确认当前工作区改动；不要回滚用户或前序 AI 的已有改动。
1. 继续优先做深层页面中文化和 3.5 寸触摸排版，不要恢复智能卡菜单。
1. 每改一组页面，先跑对应 `simulator/sequences/*.txt`，再人工查看 `simulator/screenshots/*-300.zh.png`。
1. 完成一批后跑 `bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`。
1. 最后跑本文下方回归命令，再进入真实 Amigo 固件构建。

## 验收标准

- `krux` 在 `maixpy_amigo` 配置下能正常启动
- 默认语言为中文，官方首页只增加 `SeedSigner` 一个入口，SeedSigner 页第一层显示树莓派式 `扫码签名 / 助记词工具 / 连接钱包 / 固件自检`
- 首页、Web3、助记词工具、自检、BTC 签名、地址、xpub、钱包描述符路径可从 3.5 寸触摸菜单正常进入
- 可导出 Web3 钱包连接二维码
- 可识别并签名 TP / Web3 请求，能生成结果二维码
- 可继续使用 Krux 原生 BTC PSBT、消息签名、xpub/zpub、地址验证、钱包描述符等功能
- 智能卡相关菜单、测试、截图不再出现
- 相关单元测试通过
- 模拟器截图可复核

## 风险点

- 深层页面仍有部分 Krux 原生英文或直译文案，需要继续润色
- 3.5 寸触摸屏上，长列表页面要避免一屏塞太多按钮导致误触
- typed data 的结构化哈希边界复杂，后续改 Web3 底层时必须补测试
- QR 内容长度会影响扫码和显示，连接钱包和签名结果都要保留截图验证
- Tinyseed/Stackbit 等专用金属格式目前不要直接声称完整支持 15/18/21 词
- Amigo 不是树莓派 Linux 环境，不能直接复用 `pyscard / pcscd / ACR39U` 读卡器驱动

## 2026-05-11 比特币交易签名复测与固件产物

- 用户要求 Hyperliquid 签名测试后，也必须测试比特币交易签名。
- 已低负载复测 BTC PSBT 核心签名：
  `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src nice -n 10 .venv/bin/python -m pytest -q tests/test_psbt.py -k 'sign_singlesig or sign_multisig or sign_miniscript or sign_tr_miniscript or sign_tr_expanding_multisig or sign_single_1_input_1_output_no_change or sighash'`
- 结果：`19 passed, 26 deselected in 3.54s`。
- 已低负载复测 BTC 首页/扫码签名流程：
  `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src nice -n 10 .venv/bin/python -m pytest -q tests/pages/home_pages/test_home.py -k 'sign_psbt or sign_wrong_key or sign_review_3_times or sign_zeroes_fingerprint or sign_p2tr_zeroes_fingerprint or sign_high_fee or sign_self or sign_spent_and_self'`
- 结果：`10 passed, 18 deselected in 4.42s`。
- 已低负载复测完整 PSBT 模块，覆盖不同 PSBT 编码/二维码输入输出和签名向量：
  `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src nice -n 10 .venv/bin/python -m pytest -q tests/test_psbt.py`
- 结果：`45 passed in 5.22s`。
- 当前固件已编译完成：
  `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell`
- 当前 raw 固件：`build/amigo-official-base-firmware.bin`
- raw 固件大小：`1653184 bytes`
- raw 固件 SHA256：`a2685875bf75e5cd6c3cb35e28bc34c18bad5c66681afcc9693a9f6a14ee7646`
- 当前 Kboot 刷机包：`build/amigo-official-base-official-shell-kboot.kfpkg`
- Kboot 包大小：`865497 bytes`
- Kboot 包 SHA256：`34107b12094056d12e597ce98ffabd6689ad4ac947188a0183a66efe0b65554d`
- Kboot 包内容已检查，包含 `flash-list.json`、`bootloader_lo.bin`、`bootloader_hi.bin`、`config.bin`、`firmware.bin`，其中包内 `firmware.bin` 为 `1653184 bytes`。
- 结论：当前比特币 PSBT/交易签名回归通过；Hyperliquid 回归在上一轮已通过；当前固件产物可进入真机刷入前的最后确认。

## 2026-05-11 真机刷入记录

- 时间：`2026-05-11 16:55:07 +0800`
- 用户已把 Amigo 插入电脑，电脑识别到两个串口：
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0`
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`
- 本次按固定串口刷入：
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`
- 本次刷入文件：
  `build/amigo-official-base-official-shell-kboot.kfpkg`
- 刷入命令：
  `printf '518998\n' | sudo -S nice -n 10 python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 build/amigo-official-base-official-shell-kboot.kfpkg`
- ktool 检测到 K210 ROM ISP，Flash ID：`0xEF6018`，容量：`16 MB`。
- 已写入 `bootloader_lo.bin`、`bootloader_hi.bin`、`config.bin`、`firmware.bin`。
- 主固件写入结果：`Flashed 1653221 B [26 chunks of 65536B] (00080000~0021FFFF) in 164.778s`。
- 工具最终返回：`Rebooting...`，进程退出码 `0`。
- 结论：电脑端刷机成功。下一步由用户看真机屏幕确认：是否进入中文首页、显示是否清晰、触摸是否准确、SeedSigner 入口和 Web3/BTC 签名流程是否能进入。

## 2026-05-11 Web3 真机 tuple 报错修复

- 用户真机截图显示：`TypeError("can't convert 'tuple' object to str implicitly",)`。
- 根因判断：桌面 Python 支持 `str.startswith(("a", "b"))` / `str.endswith(("a", "b"))`，但 MaixPy/MicroPython 不支持 tuple 作为前缀/后缀参数，会在真机直接报 `tuple` 转字符串错误。
- 已修复文件：`src/krux/web3.py`。
- 已新增 MicroPython 兼容 helper：`_starts_with_any()`、`_ends_with_any()`。
- 已把 Web3 内所有 `.startswith((...))` / `.endswith((...))` 改为 helper 调用。
- 已新增测试：`tests/test_web3.py::test_web3_avoids_tuple_prefix_suffix_calls_for_micropython`，防止以后再次引入这类电脑能跑、真机会炸的写法。
- 已执行全源码检查：
  `rg -n "\\.endswith\\(\\(|\\.startswith\\(\\(" src/krux vendor/urtypes/src vendor/foundation-ur-py/src`
- 结果：无命中。
- 已执行 Web3/二维码/UI 回归：
  `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src nice -n 10 .venv/bin/python -m pytest -q tests/test_web3.py tests/test_qr.py tests/pages/home_pages/test_web3_ui.py`
- 结果：`47 passed in 2.14s`。
- 已执行 BTC 回归：
  `PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src nice -n 10 .venv/bin/python -m pytest -q tests/test_psbt.py tests/pages/home_pages/test_home.py -k 'sign_singlesig or sign_multisig or sign_miniscript or sign_tr_miniscript or sign_tr_expanding_multisig or sign_single_1_input_1_output_no_change or sighash or sign_psbt or sign_wrong_key or sign_review_3_times or sign_zeroes_fingerprint or sign_p2tr_zeroes_fingerprint or sign_high_fee or sign_self or sign_spent_and_self'`
- 结果：`29 passed, 44 deselected in 6.27s`。
- 已低负载重新编译：
  `MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh --official-shell`
- 编译结果：成功。
- 新 raw 固件：`build/amigo-official-base-firmware.bin`
- 新 raw 固件大小：`1653696 bytes`
- 新 raw 固件 SHA256：`2ffae585e9730c240a25f96c925f115e95d7c963705321b145e79fe969c88794`
- 新 Kboot 包：`build/amigo-official-base-official-shell-kboot.kfpkg`
- 新 Kboot 包 SHA256：`fc0c27e1b59421d4045dac127f86554b3b68b16e4c0f0e6e497e27bb262b693a`
- 包内 `firmware.bin` 大小：`1653696 bytes`。
- 固件内容检查：`strings build/amigo-official-base-firmware.bin | rg -n "_starts_with_any|_ends_with_any|QR page must be text or bytes|crypto-multi-accounts"` 有命中，说明新修复已进入固件。
- 当前刷机状态：电脑暂未检测到 Sipeed 串口，`/dev/serial/by-id` 和 `/dev/ttyUSB*` 不存在，`lsusb` 也未看到 Sipeed USB 串口设备；已轮询 60 秒仍未出现。
- 下一步：用户需要重新插入 Amigo USB，使电脑出现 `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0` 后，再刷入新 Kboot 包。

## 2026-05-11 Web3 tuple 修复包真机刷入记录

- 时间：`2026-05-11 17:38:26 +0800`
- 用户重新插入 Amigo 后，电脑识别到：
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0 -> ../../ttyUSB0`
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 -> ../../ttyUSB1`
- 本次刷入文件：`build/amigo-official-base-official-shell-kboot.kfpkg`
- 本次刷入包 SHA256：`fc0c27e1b59421d4045dac127f86554b3b68b16e4c0f0e6e497e27bb262b693a`
- 刷入串口：`/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`
- 刷入命令：
  `printf '518998\n' | sudo -S nice -n 10 python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 build/amigo-official-base-official-shell-kboot.kfpkg`
- ktool 检测到 K210 ROM ISP，Flash ID：`0xEF6018`，容量：`16 MB`。
- 已写入 `bootloader_lo.bin`、`bootloader_hi.bin`、`config.bin`、`firmware.bin`。
- 主固件写入结果：`Flashed 1653733 B [26 chunks of 65536B] (00080000~0021FFFF) in 164.865s`。
- 工具最终返回：`Rebooting...`，进程退出码 `0`。
- 结论：Web3 tuple 修复包已成功刷入真机。下一步请真机测试 `SeedSigner -> 连接钱包`，确认不再出现 `can't convert 'tuple' object to str implicitly`。

## 2026-05-12 Amigo 救砖 / BOOT0 定位记录

- 当前优先级：先救活开发板并刷回官方 Sipeed/官方 Krux 可启动状态，确认屏幕、触摸、三个顶部按键/触摸关机路径正常后，再刷自定义固件。
- 用户实拍确认：`PWRON` 开机键和 `RESET/RST` 复位键已经物理损坏；顶部 `KEY1/KEY2/KEY3` 中间确认键曾可用，两侧键可能受损或接触异常。
- 电脑仍能识别 USB 双串口：`0403:6010 FT2232C/D/H Dual UART/FIFO IC`，典型路径为：
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0`
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0`
- 多次刷机失败均停在 `Greeting fail, check serial port (SLIP receive timeout (wait frame start))`，说明电脑看到了 USB-UART，但 K210 没有进入 ROM ISP 下载模式；这些失败没有成功擦写 Flash。
- 官方原理图确认：外部坏掉的 `PWRON` 是 `S5`，`RST` 是 `S1`，普通按键 `KEY1/KEY2/KEY3` 是 `S3/S4/S6`；`BOOT0` 不在外部按钮上，而是在 `P20` 预留 2x4 焊盘。
- `P20` 官方引脚映射：左列自上到下 `U1TX / BOOT0 / Function4 / GND`，右列自上到下 `+3V3 / KEY1 / KEY2 / U1RX`。救砖只允许短接 `BOOT0` 到 `GND`，严禁短接 `+3V3` 到 `GND`。
- 已保存官方/照片辅助图：
  `/home/ak/123/krux/build/button-diagrams/amigo-p20-boot0-gnd-annotated.png`
  `/home/ak/123/krux/build/button-diagrams/amigo-user-photo-front-reference-annotated.png`
  `/home/ak/123/krux/build/button-diagrams/amigo-buttons-all-annotated.png`
  `/home/ak/123/krux/build/button-diagrams/amigo-reset-power-annotated.png`
- 用户 2026-05-12 13:22 上传了背面照片。背面左下 USB-C 附近可见一组 2x4 金色焊盘，形态上疑似 P20 或相关预留口，但当前照片看不清丝印，不能直接确认哪两个孔是 `BOOT0/GND`。
- 下一步必须让用户对准背面左下 USB-C 旁边那组 2x4 焊盘拍清晰近照，要求能看清焊盘旁边白色丝印；确认 `P20/BOOT0/GND` 后，才可指导用户短接 `BOOT0` 到 `GND` 并插底部 USB-C 进入下载模式。
- 一旦用户确认已短接 `BOOT0-GND` 并重新插入底部 USB-C，先刷官方 Sipeed 工厂固件：
  `build/sipeed-official/maixpy_v0.6.3_2_gd8901fd22_amigo_tft_defaults.bin`
  SHA256：`e3e15ea8dacff49751405f94215c1252653343f47823fba781990279b6473d56`
- 推荐低负载刷回官方命令：
  `printf '518998\n' | sudo -S -p '' timeout 12m nice -n 19 python3 firmware/Kboot/build/ktool.py -B kd233 -b 115200 -p /dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 build/sipeed-official/maixpy_v0.6.3_2_gd8901fd22_amigo_tft_defaults.bin`
- 如果确认短接后 `kd233 + if01` 仍失败，再依次尝试 `goE + if01`、`kd233 + if00`、`goE + if00`。不要在未进入 ROM ISP 的情况下反复刷自定义固件。

### 看不到 P20 丝印时的安全定位办法

- 用户反馈背面肉眼看不到字。不要要求用户凭丝印硬找，也不要让用户盲短接任意 2x4 焊盘。
- 安全办法优先级：
  1. 使用万用表蜂鸣/通断档，先找 `GND`：一支表笔接 USB-C 金属外壳，另一支表笔逐个碰疑似 2x4 焊盘，蜂鸣/接近 0 欧姆的是地。
  2. 按官方 P20 映射，`GND` 与 `BOOT0` 在同一列，分别是左列第 4 个和左列第 2 个；但实物照片可能旋转/翻面，必须以找到的 GND 和焊盘排布方向共同判断。
  3. 不用万用表时，至少要求用户拍疑似 2x4 焊盘的超近清晰照片，并标出 USB-C 方向；仍不能确认时，宁可暂停，不要短接。
- 再次提醒：严禁碰到 `+3V3`。如果短到 `+3V3-GND`，可能导致电脑 USB 保护、开发板掉电或硬件损坏。

### 2026-05-12 P20 正反面方向修正

- 用户提示：P20/BOOT0/GND 相关丝印可能在正面，背面看不到字。
- 重要修正：如果从背面看焊盘，左右方向会相对正面镜像；不能把官方原理图/正面丝印的左右列直接套到背面照片上。
- 下一步优先让用户翻回正面，寻找与背面左下 USB-C 附近 2x4 焊盘贯通的对应位置，拍清楚正面丝印；如果正面能看到 `BOOT0/GND/P20`，按正面丝印操作。
- 如果只能从背面短接，必须先通过万用表确认 GND，再结合正面/背面镜像关系确定 BOOT0。没有万用表且没有清晰丝印时，禁止继续短接。

### 2026-05-12 用户正面找到 P21/P23

- 用户反馈：正面已经找到 `P21`、`P23`，因此 `P20` 很可能也在正面丝印侧。
- 后续操作只允许找 `P20`，不要短接 `P21/P23`。官方原理图里救砖需要 `P20` 的 `BOOT0` 与 `GND`，`P21/P23` 不是本次下载模式入口。
- 让用户在正面继续找 `P20` 或 `BOOT0/GND` 字样，找到后拍近照确认；确认前不要短接。
- 如果用户能明确看到 `P20`、`BOOT0`、`GND`，操作为：断电状态下用镊子短接 `BOOT0-GND`，保持短接并插底部 USB-C 数据口，上电 1-2 秒后可松开，然后电脑端尝试刷官方固件。

### 2026-05-12 用户找到 TX/BO 缩写

- 用户反馈正面可能没有完整丝印，但找到了 `TX` 和 `BO` 字样。
- 判断：`TX` 大概率对应官方 P20 的 `U1TX`，`BO` 大概率对应 `BOOT0`。
- 关键提醒：救砖短接点是 `BO/BOOT0` 到 `GND`，绝对不是 `TX` 到 `BO`。
- 如果用户能明确看到 `BO` 焊盘，可以用 `BO` 连接任意可靠 `GND`，例如同一组 P20 的 `G/GND` 焊盘，或 USB-C 金属外壳地；操作时必须避免碰到 `+3V3`、`TX`、`RX` 等相邻点。
- 后续用户短接 `BO-GND` 并插底部 USB-C 后，先检测串口和 ROM ISP，再刷官方 Sipeed 工厂固件。

### 2026-05-12 GND 查找说明

- 用户询问 `GND` 在哪里。
- 如果 P20 周围看不到完整 `GND`，可以使用 USB-C 金属外壳作为可靠地线参考；大部分开发板 USB 外壳与 GND 相连。
- 更安全确认方式：万用表蜂鸣档，一端接 USB-C 金属壳，另一端接疑似 `G/GND` 焊盘，蜂鸣即为地。
- 实际进入下载模式时，可以短接 `BO/BOOT0` 到 USB-C 金属外壳地，但操作难度较高，必须避免碰到相邻焊盘和 3V3。

### 2026-05-12 13:57 BO-GND 短接后刷机尝试

- 用户表示已经短接/插上。
- 电脑检测到 Sipeed 双串口：
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0 -> ../../ttyUSB0`
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 -> ../../ttyUSB1`
- USB ID：`0403:6010 Future Technology Devices International, Ltd FT2232C/D/H Dual UART/FIFO IC`。
- 低负载、短超时尝试以下组合，均未进入 K210 ROM ISP，均停在 `Greeting fail, check serial port (SLIP receive timeout (wait frame start))`：
  - `kd233 + if01 + 115200`
  - `goE + if01 + 115200`
  - `kd233 + if00 + 115200`
  - `goE + if00 + 115200`
- 结论：刷机工具尚未与 K210 ROM 建立握手，没有写入/擦除 Flash。当前问题仍是硬件未进入下载模式，重点检查：
  1. `BO/BOOT0` 是否找对；
  2. `GND` 是否可靠接地；
  3. 是否在完全断电状态下先短接 `BO-GND`，再插底部 USB-C；
  4. 是否因为 PWRON/RESET 损坏导致上电状态异常，必要时尝试拔电池、断 USB 等待 10 秒、保持短接后再插。

### 2026-05-12 14:01 第二次 BO-GND 短接后尝试

- 用户再次表示已插上。
- 初始检测时串口尚未出现，轮询约 20 秒后出现：
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0 -> ../../ttyUSB0`
  `/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if01-port0 -> ../../ttyUSB1`
- 立即尝试：
  - `kd233 + if01 + 115200`：`Greeting fail`
  - `goE + if01 + 115200`：`Greeting fail`
  - `kd233 + if00 + 115200`：`Greeting fail`
- 再试 `goE + if00` 时串口已经消失，系统里 `/dev/serial/by-id` 与 `lsusb 0403` 均未再出现。
- 结论：仍未进入 K210 ROM ISP，且 USB 连接/短接可能不稳定。下一步不要继续盲试刷机，优先让用户拍 `TX/BO` 附近正面近照，或使用万用表确认 `BO` 与 `GND`；如果能焊一根临时线从 `BO` 到 GND 会比手持镊子可靠。

### 2026-05-12 关于用另一个 USB 口当地线

- 用户询问是否可以短接另外一个 USB 口。
- 说明：如果只是用另一个 USB-C 口的金属外壳作为 `GND`，通常可以，因为 USB 外壳/地线在板上一般共地。
- 禁止：不要碰 USB-C 口里面的小触点，不要把 `BO/BOOT0` 接到 USB 的 `VBUS/5V` 或任何内部针脚。
- 建议：短接 `BO/BOOT0` 到 USB-C 金属外壳即可；插电脑刷机仍优先使用能枚举出 Sipeed 双串口的底部/数据 USB-C 口。

### 2026-05-12 14:09 第三次 BO-GND 尝试

- 用户再次插入后，电脑稳定检测到双串口和 `0403:6010 FT2232C/D/H Dual UART/FIFO IC`。
- 尝试官方 Sipeed 工厂固件刷回，组合如下，全部失败在 ROM ISP 握手阶段：
  - `kd233 + if01 + 115200`：`Greeting fail`
  - `goE + if01 + 115200`：`Greeting fail`
  - `kd233 + if00 + 115200`：`Greeting fail`
  - `goE + if00 + 115200`：`Greeting fail`
- 仍未出现 Flash ID，未发生擦写。
- 结论更新：USB-UART 与电脑连接没问题；目前唯一有效推进点是确认真正 `BOOT0` 焊盘位置，或用万用表/临时焊线确保 `BOOT0` 上电瞬间被拉到 `GND`。

### 2026-05-12 是否存在非短接救砖办法

- 用户询问：除了短接是否还有其他办法。
- 技术结论：K210 ROM ISP 下载模式本质要求 `BOOT0` 在上电/复位瞬间被拉到 `GND`。因此所有救砖办法都绕不开 `BOOT0` 低电平，只是实现方式不同。
- 可选办法：
  1. 手持镊子短接 `BOOT0-GND` 后插 USB，最简单但最不稳定。
  2. 临时焊一根细线从 `BOOT0` 到 `GND`，刷完再拆，成功率更高。
  3. 焊一个小开关/飞线按钮，等同于自制 BOOT 键。
  4. 修复/更换坏掉的 `RESET/PWRON`，再配合 `BOOT0-GND` 进入下载模式。
  5. 如果原系统还能启动并提供应用层升级/bootloader 升级入口，可从软件升级；但当前 ktool 无法握手且板子启动异常，暂不可依赖。
  6. 使用 JTAG/SPI Flash 外部编程器直接写 Flash，理论可行但难度高、风险高，不建议普通操作。
- 当前建议：不要继续盲试软件刷机；优先确认 `BOOT0` 焊盘，最好用万用表或临时焊线稳定拉低。

### 2026-05-12 14:16 第四次尝试

- 用户要求再次尝试。
- 电脑检测到双串口稳定存在：`if00 -> ttyUSB0`，`if01 -> ttyUSB1`，USB ID 仍为 `0403:6010`。
- 官方 Sipeed 工厂固件刷回尝试四组组合全部失败在 ROM ISP 握手阶段：
  - `kd233 + if01`
  - `goE + if01`
  - `kd233 + if00`
  - `goE + if00`
- 全部输出 `Greeting fail, check serial port (SLIP receive timeout (wait frame start))`。
- 未出现 Flash ID，未擦写。
- 明确结论：刷机软件、固件文件、串口组合基本排除；下一步必须硬件层面稳定拉低 BOOT0。建议用户拍 `TX/BO` 近照或临时焊线。

### 2026-05-12 14:20-14:23 双 USB 口尝试

- 用户表示两个 USB 口都插电脑。
- 初始仍只检测到一个 Sipeed 双串口设备，这是正常现象：`0403:6010 FT2232C/D/H Dual UART/FIFO IC`，`if00/if01`。
- 准备刷官方固件时串口路径突然消失：`could not open port ... No such file or directory`。
- 随后轮询 20 秒未再检测到 Sipeed 串口。
- 结论：两个口同时插电脑没有帮助，反而可能导致供电/枚举不稳定。后续建议只插能枚举双串口的底部数据口；另一个 USB 口最多只用其金属外壳作为 GND 参考，不要同时作为数据/供电连接参与刷机。

### 2026-05-12 14:24 再次尝试

- 用户再次要求尝试。
- 双串口恢复：`if00 -> ttyUSB0`，`if01 -> ttyUSB1`，USB ID `0403:6010`。
- 官方 Sipeed 工厂固件刷回四组组合全部失败：`Greeting fail, check serial port (SLIP receive timeout (wait frame start))`。
- 未出现 Flash ID，未擦写。
- 结论不变：必须确认/稳定拉低 `BOOT0`，软件端无法绕过。

### 2026-05-12 14:58 再次尝试

- 用户再次要求尝试。
- 检查无残留 `ktool.py/kflash` 刷机进程。
- 电脑仍能识别 Sipeed 双串口：`if00 -> ttyUSB0`，`if01 -> ttyUSB1`，USB ID `0403:6010`。
- 官方 Sipeed 工厂固件刷回四组组合全部失败：
  - `goE + if01`
  - `kd233 + if01`
  - `goE + if00`
  - `kd233 + if00`
- 全部停在 `Greeting fail, check serial port (SLIP receive timeout (wait frame start))`。
- 未出现 Flash ID，未擦写。结论不变：软件端可达 USB-UART，但 K210 未进入 ROM ISP，必须硬件确认/稳定拉低 `BOOT0` 到 `GND`。

## 2026-05-12 当前暂停与 GitHub 备份状态

- 用户决定先暂停救砖，当前损坏 Amigo 暂时按坏板/练手板处理，后续购买新机器后继续。
- 当前坏板结论：USB-UART 仍可被电脑识别，但 K210 一直无法进入 ROM ISP；所有失败都停在 `Greeting fail`，没有出现 Flash ID，没有擦写。
- 新机器建议流程：
  1. 新板到手先不要拆后盖。
  2. 先刷官方 Krux 或官方 Sipeed 固件，确认屏幕、触摸、按键和 USB 连接正常。
  3. 再刷当前自定义 Amigo 固件。
  4. 真机测试 SeedSigner 入口、Web3 连接/签名、BTC PSBT、助记词工具、手动派生地址、触摸关机。
- 主仓库内已新增子模块补丁备份目录：`docs/maintenance/submodule-patches/`。
- 子模块补丁作用：保存 `firmware/Kboot` 与 `firmware/MaixPy` 的本地构建/字体/低负载修补，避免以后重新克隆主仓库时丢失。
- 接手者应先读：
  - `docs/amigo-tp-web3-port-plan.zh-CN.md`
  - `docs/maintenance/submodule-patches/README.zh-CN.md`
  - `docs/getting-started/installing/amigo-flash-path.zh-CN.md`
