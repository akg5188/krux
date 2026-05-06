# Sipeed Matrix Amigo 的 TP / Web3 迁移计划

这份文档记录把 `satochip-signer` 里的 TP / Web3 / 连接钱包 / 签名请求能力，迁移到 `krux` 的 Amigo 目标上的执行计划。

如果你是以后接手的人，建议先按这个顺序看：

1. [Krux 仓库结构与接手说明](getting-started/installing/repo-structure.zh-CN.md)
2. [Amigo 中文新手入口](getting-started/index.zh-CN.md)
3. 本页
4. [Amigo 固件从源码编译并烧录](getting-started/installing/from-source.zh-CN.md)

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

- 2026-05-06 更新：新增 `Amigo 商用交付说明` 中文页，把支持范围、禁用范围、验证记录和接手顺序集中到一页，方便以后发货、售后和交接。
- 2026-05-06 更新：新增 `Amigo 常见问题` 中文页，并把它挂到 README、中文新手入口和安装教程里，补齐商业化交付最常被问到的支持入口。
- 2026-05-06 更新：继续做 Amigo 深层页面中文润色和 3.5 寸触摸排版细化，统一修正了 `添加或修改钱包密码短语？`、`继续？`、`派生 BIP85 熵？`、`完成？` 等半角标点；`BIP85` 相关文案统一为 `BIP85 子助记词` 和 `BIP85 密码`，登录菜单里的 `固件自检` 入口也保持为双行大按钮。最新针对性回归 `101 passed`。
- 总结论：**除智能卡外，树莓派固件里的核心功能路线已经迁移或由 Krux 原生能力覆盖到 Amigo 第一版**。Web3/TP/EVM、固件自检、首页大屏触摸排版、BTC/PSBT/xpub、助记词创建/导入/备份、`扑克牌创建`、`16进制创建`、`查看原始熵`、`钢板打孔数字`、`二次助记词`、`钢板二次还原`、`15/18/21词创建/导入` 和 `开机数字口令锁` 已完成；后续剩余工作主要是深层页面继续中文化、3.5 寸触摸屏排版细化、Tinyseed/Stackbit 等专用金属格式对 15/18/21 词的兼容性评估。
- 继续确认：TinySeed 已经统一到 `0-2047 / 11 位` 编号体系，显示、手动输入、打印和扫描还原都要跟着同一套编号走，不能再沿用旧的 `1-2048 / 12 位` 假设。
- 已完成：已加载助记词后的 Amigo 首页按树莓派首页逻辑重排为 `扫码签名 / 助记词工具 / 连接钱包 / 固件自检`；因为智能卡方向已取消，`连接钱包` 占用原树莓派 `智能卡工具` 的分类位置。
- 已完成：Web3 入口、连接钱包、消息签名、结构化数据签名、交易签名、结构化交易签名
- 已完成：`OKX / Bitget / MetaMask / Rabby / TokenPocket` 连接二维码
- 已完成：`tpr1:` / `w3r1:` 安卓低密度中转请求解析
- 已完成：Amigo 桌面模拟器中文截图验证
- 已完成：Web3 顶层菜单改成 3.5 寸触摸屏大按钮，两项入口分别带用途说明
- 已完成：继续收尾 Amigo 深层中文页面的标点统一，消息签名、钱包描述符、自检、设备测试、Web3 预览和开机口令相关页面改成更紧凑的 ASCII 冒号，减少 3.5 寸屏上的折行和视觉噪音
- 已完成：新增中文 `固件自检` 入口，登录前和加载助记词后的首页都能进入
- 已完成：Amigo 默认语言改为 `zh-CN`，首次启动和模拟器无设置时默认中文
- 已完成：加载助记词后的 Amigo 首页改为中文双行大按钮，按树莓派首页逻辑整理为 `扫码签名`、`助记词工具`、`连接钱包`、`固件自检`
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
| 开机口令锁 | 已迁移第一版 | 已按 Amigo 原生固件重做：`设置 -> 安全 -> 开机口令锁` 可开启/修改/关闭；开机进入登录菜单前先显示大触摸数字键盘；支持 4-12 位数字；错误 5 次后返回失败并关机。注意：这是本机 Flash 中的便捷启动门禁，不是硬件安全芯片，也不等同树莓派 Linux 启动分区加密方案 |
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
| 中文大屏首页 | 已迁移 | Amigo 默认 `zh-CN`，首页按触摸屏双行大按钮重新排版；首页顺序按树莓派首页重排为 `扫码签名 / 助记词工具 / 连接钱包 / 固件自检`，其中 `连接钱包` 替代已取消的智能卡工具位置 |
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
  - README 中的构建入口是 `./krux build maixpy_amigo`
  - 当前机器未检测到可用 `docker` 命令，因此本轮没有生成 `build/firmware.bin` / `build/kboot.kfpkg`
  - 后续如果要真机刷 Amigo，需要先装好 Docker/让当前用户可运行 Docker，再执行 `./krux build maixpy_amigo`
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

- 2026-05-06：重新 bake `zh-CN` 并清理 Amigo 硬编码中文提示中的尾部 `！`，避免 3.5 寸屏出现方块 glyph。
- 2026-05-06：重新运行 `bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN`。
- 结果：成功退出，生成 `173` 张 `300.zh.png` 中文截图，空白/黑屏筛查为 `0`。
- 关键截图：`simulator/screenshots/wallet-descriptor-tr-minis-4-300.zh.png` 已显示为 `钱包描述符已加载`，无尾部方块。
- 单测：`PYTHONPATH=src:vendor/embit/src:vendor/foundation-ur-py/src:vendor/urtypes/src .venv/bin/pytest tests/pages/home_pages/test_addresses.py tests/pages/home_pages/test_secondary_mnemonic.py tests/pages/home_pages/test_home.py tests/pages/test_print_page.py -q`
- 结果：`51 passed`
- 2026-05-06：`tests/pages/test_login.py` 的十六进制/八进制 `possible_letters` 用例已改成直接断言 `_load_key_from_keypad` 传入的闭包边界，避免继续硬跑完整 UI 后被自动补全和确认框拖死；当前也已把数字输入相关测试统一到 `0-2047` 口径。
- 2026-05-06：`simulator/sequences/qr-transcript.txt` 已从容易跳进打印分支的 `Datum` 路径改成 Amigo 上更稳的助记词备份二维码路径，`standard / lines / zoomed / regions / grided / qr-viewer` 六张截图已重新验证能正常产出。

## 下一步建议

1. 继续评估 Tinyseed/Stackbit 等专用金属格式是否要支持 `15/18/21` 词，避免破坏原格式兼容
1. 继续把助记词、BIP85、备份、PSBT 复核页做中文化和 3.5 寸触摸屏排版
1. 每完成一组页面就跑对应测试和截图
1. 不再推进智能卡直连或桥接功能，除非用户重新明确要求
1. 待上述非智能卡功能完成后再开始真实 `Amigo` 固件构建

## 暂缓和不做

- 不做：直接搬运 PC/SC 智能卡读卡流程
- 不做：外接 ACR39U 读卡器驱动适配
- 不做：Satochip / SeedKeeper 的完整硬件签名链路
- 暂不做：Android 中转 APK 与 Amigo 固件的整套联动协议扩展
- 最新执行项：用户 2026-05-06 要求 Amigo 侧完成后构建现有 Android debug APK；只做低并发 APK 构建，不重新设计 Android 功能

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
- 默认语言为中文，首页为 `扫码签名 / 助记词工具 / 连接钱包 / 固件自检`
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
