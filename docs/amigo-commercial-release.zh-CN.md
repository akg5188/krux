# Amigo 商用交付说明

这页是给以后接手、打包、发货和售后的人看的。目标不是“把功能都堆上去”，而是把 `Sipeed Matrix Amigo` 上的 Krux 固件做成一份可交付、可验证、可维护的产品版本。

## 这份版本包含什么

- 中文界面和中文新手入口
- Amigo 3.5 寸触摸屏适配后的大按钮首页
- 自定义文本二维码和二维码导出
- 助记词创建、导入、备份、恢复
- 助记词编号、钢板打孔数字和 TinySeed 都统一按 `0-2047` 口径处理，位权从左到右显示 `1 / 2 / 4 / ... / 1024`，手动输入、打印和扫描还原都走同一套映射
- BTC / PSBT / xpub / wallet descriptor 相关功能
- Web3 / TP / EVM 连接钱包与签名
- 固件自检、触摸测试、SD 卡检查、设备测试
- TTL 串口热敏打印相关能力
- 15 / 18 / 21 / 24 词相关流程
- BIP85、钢板打孔数字、二次助记词、原始熵查看等工具

## 这份版本不包含什么

- 智能卡主线功能
- ACR39U / PC/SC / pyscard / pcscd 直连读卡器方案
- Android 固件交付
- 直接驱动 USB 办公打印机

## 商用交付标准

一份能交付的版本，至少要满足这几件事：

1. 用户能从中文首页和中文新手入口直接找到刷机、编译、FAQ 和接手说明
2. 所有高频页面在 Amigo 3.5 寸屏上能正常显示，不依赖小屏按键布局
3. 中文文案没有明显的半角/全角混乱，也没有容易误导的翻译
4. 关键功能回归测试通过
5. 截图回归能稳定生成，便于人工复核
6. 支持边界写清楚，不把不支持的东西包装成支持

## 2026-05-06 验证记录

- 截图回归：`bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
- 截图产物：`173` 张中文截图
- 关键回归：`209 passed`
- 代码检查：`git diff --check` 通过
- 快照分支：`backup/amigo-snapshot`

## 2026-05-07 验证记录

- 继续做 Amigo 深层页面中文润色和 3.5 寸触摸排版细化，重点收口 `KEF`、密码短语和消息签名的高频提示，把 `使用默认加密模式`、`更新标签`、`密码短语含非 ASCII 字符`、`消息 / 地址 / 签名 / 公钥` 等页面再压短一轮
- 定向回归：`PYTHONPATH=src .venv/bin/pytest -q tests/pages/test_encryption_ui.py tests/pages/home_pages/test_sign_message_ui.py tests/pages/test_wallet_settings.py tests/pages/home_pages/test_home.py tests/pages/home_pages/test_mnemonic_backup.py`
- 定向回归结果：`111 passed`
- 新增 `工具 -> 创建二维码` 中文入口，模拟器序列 `simulator/sequences/tools-create-QR.txt` 可完整走通
- 继续收口 `MnemonicLoader` / `Mnemonic XOR` / `BIP85` / `助记词备份` / `消息签名` 的中文确认词、错误提示和基础加载标题
- 截图回归：`bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
- 截图产物：`176` 张中文截图
- 继续收口 `钱包描述符` / `地址列表` / `二维码查看器` 的 Amigo 中文菜单和触摸排版，并新增 `Amigo 直接烧录 maixpy.bin` 维护者教程，方便以后只更新底层镜像的人直接接手
- 顶部状态栏的 testnet 指示在 Amigo 上改成中文 `测试网`，对应单测 `PYTHONPATH=src .venv/bin/pytest tests/pages/test_page.py -q` 结果 `37 passed`
- Web3 顶层菜单和连接钱包 / 签名流程继续复核，`tests/pages/home_pages/test_web3_ui.py -q` 结果 `10 passed`
- 钱包描述符 / 文件操作回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/home_pages/test_wallet_descriptor.py tests/pages/test_file_operations.py -q`，结果 `22 passed`
- 定向回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_qr_view.py tests/pages/home_pages/test_addresses.py tests/pages/home_pages/test_wallet_descriptor.py tests/pages/home_pages/test_mnemonic_backup.py -q`
- 定向回归结果：`58 passed`
- 最新组合回归：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest -q tests/pages/test_encryption_ui.py tests/pages/test_wallet_settings.py tests/pages/home_pages/test_bip85.py tests/pages/home_pages/test_wallet_descriptor.py tests/pages/test_file_operations.py`
- 最新组合回归结果：`83 passed`
- 工具页单测：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/test_tools.py -q`
- 工具页单测结果：`7 passed`
- 代码检查：`git diff --check` 通过
- Amigo 固件编译：`make -C firmware/MaixPy/projects/maixpy_amigo/build -j2`
- 编译结果：`maixpy.bin`、`firmware.bin`、`maixpy.elf` 已生成
- 编译校验：`maixpy.bin` SHA256 `04a59041f4d20dd9a6ac79d82807325c1d5db38d8ef1e787af820555722ead4b`

## 2026-05-08 验证记录

- 继续收尾 Amigo 深层页面中文润色和 3.5 寸触摸排版细化，修正 `secondary_mnemonic.py` 的语法问题，并把 `地址` / `助记词 XOR` / `加密` / `钱包设置` 等残留页再核对一轮
- 定向回归：`PYTHONPATH=src .venv/bin/python -m pytest -q tests/pages/home_pages/test_addresses.py`
- 定向回归结果：`15 passed`
- 定向回归：`PYTHONPATH=src .venv/bin/python -m pytest -q tests/pages/test_encryption_ui.py tests/pages/test_wallet_settings.py tests/pages/home_pages/test_mnemonic_xor.py`
- 定向回归结果：`74 passed`
- 继续跑完整 Amigo 中文截图回归：`bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
- 截图产物：`176` 张中文截图
- 代码检查：`python3 -m py_compile` 通过，`src/krux/pages/home_pages/secondary_mnemonic.py`、`src/krux/pages/home_pages/addresses.py` 等关键页面可正常编译
- `simulator/screenshots/` 已确认包含最新的 `print-qr-prompt-300.zh.png`、`print-qr-printing-300.zh.png`、`web3-typed-transaction-preview-300.zh.png`、`tools-create-QR-view-300.zh.png` 等中文截图

## 2026-05-09 验证记录

- 构建路线已经收敛为“官方 Amigo 固件底座 + 当前 Krux 功能代码”，不再使用旧的几百 KB 失败包
- 低负载构建命令：`MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh`
- 完整交付包：`build/amigo-official-base-kboot.kfpkg`
- 包内 `firmware.bin` 大小：`1876736` 字节
- 完整交付包 SHA256：`ecdfec0905a65655faf9c5d8db0bf6abab81b6e7b6a11a888952f923f9298069`
- 独立固件镜像 SHA256：`9083c678af2b01ec51ca232d6bf6e919cd5c8c2cfbe14719a1f862a98686c638`
- 包内容检查：`unzip -l build/amigo-official-base-kboot.kfpkg` 显示官方 Kboot 结构和 `0x00080000` 固件区不变
- 关键回归：`tests/test_web3.py` 和 `tests/pages/home_pages/test_web3_ui.py` 结果 `32 passed`
- 语法检查：`src/krux/web3.py`、`firmware/scripts/build-amigo-official-base.sh`、`firmware/MaixPy/tools/cmake/project.py` 均通过
- 禁止交付：`build/amigo-custom-kboot.kfpkg`，SHA256 `d43574ae512309c09f35a1a8b54066b6787fe71495a0f58f00b6bf0366d2c6e2`，该包已真机验证黑屏
- 真机刷入命令：`sudo python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/ttyUSB1 build/amigo-official-base-kboot.kfpkg`
- 真机刷入结果：主固件区成功写入 `1876773 B (00080000~0024FFFF)`，Ktool 最后显示 `Rebooting...`
- 教程修正：Linux 下如果直接刷机提示 `Permission denied`，使用 `sudo` 或把用户加入 `dialout` 组

## 2026-05-09 真机反馈修复记录

- 用户反馈真机存在“很多乱码”和“功能不完整”的观感问题，本轮不能继续按“已商业交付完成”处理
- 已修复底层字体缺字风险：`font.c` 查不到字形时不再绘制未初始化缓存，避免缺字变成随机花字
- 已增加 Amigo 显示层安全文本替换：省略号、细空格和全角标点在绘制前转成更稳的 ASCII 字符
- 已重排开机首页：新增 `功能总览`，把加载钱包、创建钱包、助记词工具、离线工具、自检、设置等入口前置
- 已继续清理高频页面中文文案和 3.5 寸触摸屏按钮文案
- 轻量验证：关键 Python 文件 `py_compile` 通过，`git diff --check` 通过
- 定向回归一：`tests/test_display.py tests/pages/test_login.py tests/pages/home_pages/test_home.py tests/pages/test_self_check.py tests/pages/home_pages/test_web3_ui.py`，结果 `162 passed`
- 定向回归二：`tests/pages/test_print_page.py tests/pages/test_device_tests.py tests/pages/test_qr_view.py tests/pages/test_qr_capture.py tests/pages/test_encryption_ui.py tests/pages/test_wallet_settings.py tests/pages/home_pages/test_addresses.py tests/pages/home_pages/test_wallet_descriptor.py tests/pages/home_pages/test_sign_message_ui.py tests/pages/home_pages/test_secondary_mnemonic.py tests/pages/test_tiny_seed.py`，结果 `184 passed`
- 尚未完成：本轮修复后还没重新生成完整截图、还没重新低负载编译、还没重新刷真机验证，因此不能标记为最终商用交付版

## 2026-05-10 官方底座收敛记录

- 新策略：官方 Amigo 顶层菜单尽量保持不变，只新增一个 `树莓派功能` 入口。
- 登录页顶层：`加载助记词 / 新助记词 / 设置 / 工具 / 树莓派功能 / 关于`。
- 加载钱包后首页顶层：`备份助记词 / 扩展公钥 / 钱包 / 地址 / 签名 / 树莓派功能 / 重启或关机`。
- `树莓派功能` 子菜单承载：`扫码签名 / 助记词工具 / 连接钱包 / 固件自检`。
- 已清理临时诊断串口打印，避免启动和菜单运行时持续刷日志。
- 已同步截图脚本导航，关键序列现在都会先进入 `树莓派功能`，避免 Web3、扫码签名、自检截图误拍官方首页。
- 本轮低负载验证：关键 Python 文件语法检查通过，`git diff --check` 通过，Amigo 中文字库检查 `missing=0`，定向回归 `94 passed`，关键截图序列单独跑通。
- 已重新低负载编译官方壳包：`build/amigo-official-base-official-shell-kboot.kfpkg`，大小 `865812` 字节，SHA256 `206d78fae4c2ff9621f123c6d8cf24683ae4c072da5910294824a2f464a184b8`；包内 `firmware.bin` 大小 `1653184` 字节，SHA256 `88b627994832c50b9fe2fda0f9841128b88f08bef77b742bece766196e1e6af0`。
- 仍不恢复：智能卡、ACR39U、PC/SC、pyscard、pcscd、Brother USB 办公打印机直连。

## 2026-05-09 晚间收口记录

- 已重新跑完整 Amigo 中文截图回归：`nice -n 10 bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`
- 截图产物：`176` 张 `simulator/screenshots/*-300.zh.png`
- 已修复 Amigo 截图触摸序列：模拟器 `touch` 坐标统一转成整数，并把触摸点写入 `irq_point`，以后 Amigo 专用序列能稳定点中大按钮
- 已新增 Amigo 专用 `print-qr.txt` 序列，`print-qr-prompt-300.zh.png` 不再显示红色 `加载失败`，`print-qr-printing-300.zh.png` 显示 `正在打印... 1 / 1`
- 打印确认页不再暴露底层驱动名 `thermal/adafruit`，Amigo 上显示为 `TTL 串口热敏打印机`
- Web3 长交易签名前预览已压缩到确认按钮上方，底部显示 `内容已省略`，不会再压住 `否 / 是` 按钮
- QR 显示页和扫码页提示已按触摸屏改写为 `点按退出 / 按键调亮度`、`按侧键切换模式\n点屏或返回键退出`
- 已清掉菜单循环里的高频调试输出，避免真机菜单刷新和按键时持续刷串口日志
- 本轮完整截图回归中曾出现一次 `Exception in thread Thread-1 (run_krux):`，脚本最终退出 `0`，截图数量完整；随后单独复跑 `wallet-descriptor-wsh.txt`、`extended-public-key-wpkh.txt`、`extended-public-key-wsh.txt` 未复现，后续如再出现需抓完整 traceback
- 本轮轻量验证：`python3 -m py_compile` 通过，`git diff --check` 通过，`tests/pages/home_pages/test_web3_ui.py tests/pages/test_print_page.py tests/pages/home_pages/test_mnemonic_backup.py tests/test_display.py` 结果 `93 passed`
- 已完成低负载编译：`MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 firmware/scripts/build-amigo-official-base.sh`
- 新交付包：`build/amigo-official-base-kboot.kfpkg`，大小 `930231` 字节，SHA256 `3624fe149006f46be4d9da511239c70d728fb02790bdc9b1edd74bb078f8a048`
- 新固件镜像：`build/amigo-official-base-firmware.bin`，大小 `1885440` 字节，SHA256 `b19ac93a23de5fc82040dd263e2f5e693b881165f5fb455bd381e49dcc81d38e`
- 包内检查：`unzip -l build/amigo-official-base-kboot.kfpkg` 显示 `firmware.bin` 为 `1885440` 字节，仍是官方 Kboot 结构和 `0x00080000` 主固件区，不是旧的几百 KB 黑屏包
- 真机刷入前检查：`lsusb` 当前只能看到鼠标、SD 读卡器、蓝牙音箱和硬盘盒；`/dev/serial/by-id`、`/dev/ttyUSB*`、`/dev/ttyACM*` 都没有出现 Sipeed/Amigo 串口，所以本轮不能盲刷
- 如果继续刷机，先让电脑识别到 Amigo 串口，再执行 `sudo python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/ttyUSB1 build/amigo-official-base-kboot.kfpkg`
- 未识别串口时优先检查：数据线是否支持数据、是否插到 Amigo 可刷机 USB 口、是否按住 BOOT/IO0 再点 RESET 或重新插电、USB 转接头是否只供电不传数据
- 用户重新插 USB 后设备被识别为 `Sipeed USB to Dual Uart`，`/dev/serial/by-id/usb-xel@sipeed_Sipeed_USB_to_Dual_Uart-if00-port0 -> /dev/ttyUSB0`，`if01-port0 -> /dev/ttyUSB1`
- 真机刷入成功：`sudo python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/ttyUSB1 build/amigo-official-base-kboot.kfpkg`
- 刷机结果：Ktool 成功进入 ROM ISP，写入 bootloader、配置区和 `0x00080000` 主固件区，主固件显示 `Flashed 1885477 B [29 chunks of 65536B] (00080000~0024FFFF) in 183.144s`，最后显示 `Rebooting...`
- 刷后复查：`/dev/ttyUSB0`、`/dev/ttyUSB1` 仍存在，`sha256sum` 与文档中的新交付包哈希一致；下一步需要人工看真机屏幕是否进入中文 Krux 首页、触摸是否可用
- 当前仍不支持：智能卡、ACR39U、PC/SC、pyscard、pcscd、Brother USB 办公打印机直连

## 接手顺序

如果你以后要继续这条线，建议按这个顺序看：

1. [Krux 仓库结构与接手说明](getting-started/installing/repo-structure.zh-CN.md)
2. [Amigo 中文新手入口](getting-started/index.zh-CN.md)
3. [Amigo 常见问题](faq.zh-CN.md)
4. [Amigo 迁移计划 / 接手记录](amigo-tp-web3-port-plan.zh-CN.md)

## 维护原则

- 只要是 Amigo 主线，默认以触摸屏体验优先
- 只要是支持边界，默认写清楚，不留想象空间
- 只要是会反复被问的问题，默认放到 FAQ 和新手入口里
- 只要是交付证据，默认保留测试和截图路径
