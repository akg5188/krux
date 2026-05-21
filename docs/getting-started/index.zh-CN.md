---
hide:
  - navigation
  - toc
---

# Krux 中文新手入口

这不是上游原版 Krux 的通用入口，而是基于 `selfcustody/krux` 的 Amigo 下游快照入口。

如果你拿到的是 `Sipeed Matrix Amigo`，这里可以直接当总目录用；如果你要看原版 Krux 的通用文档，请回到上游仓库。

## 先按这个顺序看

1. [仓库结构与接手说明](installing/repo-structure.zh-CN.md)
2. [Amigo 预编译包烧录](installing/from-pre-built-release.zh-CN.md)
3. [Amigo 刷机路径图](installing/amigo-flash-path.zh-CN.md)
4. [Amigo 源码编译并烧录](installing/from-source.zh-CN.md)
5. [Amigo 固定快照重编译教程](installing/from-github-snapshot.zh-CN.md)
6. [Amigo 固定快照卡片版](installing/from-github-snapshot-quick.zh-CN.md)
7. [Amigo 直接烧录 maixpy.bin](installing/from-maixpy-bin.zh-CN.md)
8. [Amigo 商用交付说明](../amigo-commercial-release.zh-CN.md)
9. [Amigo 常见问题](../faq.zh-CN.md)
10. [Amigo TP / Web3 迁移计划与接手记录](../amigo-tp-web3-port-plan.zh-CN.md)

## Amigo 上先看什么

- 首页是中文双行大按钮
- 登录页先看 `加载助记词`、`新助记词`、`设置`、`工具`、`固件自检`
- 加载助记词后的首页按 `扫码签名 / 助记词工具 / 连接钱包 / 固件自检` 分组
- 智能卡相关功能已经不再是 Amigo 主线内容

## 登录页和首页怎么用

- `加载助记词`：导入或者打开已有钱包
- `新助记词`：创建新的助记词钱包
- `设置`：改语言、显示、打印机、主题、开机口令锁等
- `工具`：看自检、二维码、SD 卡、文件和其它辅助功能
- `固件自检`：检查设备、触摸、SD 卡和版本信息
- 首页的 `扫码签名`、`助记词工具`、`连接钱包`、`固件自检` 是当前最常用的四个大入口
- 如果你想先判断这套固件能不能直接交付给用户，先看商用交付说明
- 如果你还不确定该点哪一页，先看第 3 条
- 如果你想复现这次已经验证过的 GitHub 快照，先看第 5 条
- 如果你只想照着最短步骤快速重编译，先看第 6 条
- 如果你在看助记词编号、钢板打孔数字或 TinySeed，记住统一口径都是 `0-2047`，位权从左到右是 `1 / 2 / 4 / ... / 1024`，扫描还原也跟手动输入用同一套映射
- 如果你已经在看 `maixpy.bin` 或只想维护底层镜像，先看第 7 条
- 如果你卡在连接、打印、智能卡、USB 口或者固件大小这些问题上，先看第 9 条

## 小白最短路径

1. 先看预编译包教程，如果你只是想尽快刷机
2. 如果你要改中文、改 UI、改功能，再看源码编译教程
3. 改完以后先跑模拟器，再看截图目录确认界面
4. 如果你只想知道“现在做到哪一步了”，直接看迁移计划

## 截图和验证

- 本地会用 `bash simulator/generate-device-screenshots.sh maixpy_amigo zh-CN` 重新生成中文截图
- 生成结果保存在 `simulator/screenshots/`
- 迁移计划文档里记录了当前关键功能、测试结果和截图进度

## 推荐继续看

- [Amigo 中文预编译包烧录](installing/from-pre-built-release.zh-CN.md)
- [Amigo 刷机路径图](installing/amigo-flash-path.zh-CN.md)
- [Amigo 中文源码编译](installing/from-source.zh-CN.md)
- [Amigo 固定快照重编译](installing/from-github-snapshot.zh-CN.md)
- [Amigo 固定快照卡片版](installing/from-github-snapshot-quick.zh-CN.md)
- [Amigo 中文接手说明](installing/repo-structure.zh-CN.md)
- [Amigo 商用交付说明](../amigo-commercial-release.zh-CN.md)
- [Amigo 常见问题](../faq.zh-CN.md)
- [Amigo 迁移计划 / 接手记录](../amigo-tp-web3-port-plan.zh-CN.md)
