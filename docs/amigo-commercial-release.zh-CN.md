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
