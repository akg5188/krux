# Amigo 商用交付说明

这页是给以后接手、打包、发货和售后的人看的。目标不是“把功能都堆上去”，而是把 `Sipeed Matrix Amigo` 上的 Krux 固件做成一份可交付、可验证、可维护的产品版本。

## 这份版本包含什么

- 中文界面和中文新手入口
- Amigo 3.5 寸触摸屏适配后的大按钮首页
- 助记词创建、导入、备份、恢复
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

