# Krux 仓库结构与接手说明

这页是给以后自己、或者其他 AI 接手用的。

你现在看到的不是两个重复项目，而是一个上游项目、一份下游备份仓库和一个子模块：

- `selfcustody/krux` 是上游 Krux，负责通用功能和原始文档。
- `krux`（`https://github.com/akg5188/krux`）是当前这份下游备份仓库，保留上游结构并叠加 Amigo 改造。
- `firmware/MaixPy` 是 `krux` 的子模块，放 Amigo 这类硬件的底层板级支持、MicroPython 端口、屏幕、触摸和启动相关代码。

换句话说：

- 改用户能直接看到的功能，通常改 `krux`
- 改硬件底层、驱动、板级适配，才进入 `firmware/MaixPy`

## 这三个地址

- 上游项目：`https://github.com/selfcustody/krux`
- 当前仓库：`https://github.com/akg5188/krux`
- 子模块：`https://github.com/akg5188/MaixPy`

## 先记住怎么拉代码

如果你是第一次拿这份仓库，或者换了电脑，直接这样拉：

```bash
git clone --recurse-submodules https://github.com/akg5188/krux
cd krux
git submodule update --init --recursive
```

如果仓库已经在本地，只是想更新：

```bash
git pull origin main
git submodule update --init --recursive
```

## 以后改代码的顺序

1. 先确认你要改的是上层功能还是底层硬件
2. 大多数情况下只改 `krux`
3. 如果确实改了 `firmware/MaixPy`，先在 `MaixPy` 里提交并推送
4. 回到父仓库，把 `firmware/MaixPy` 的 submodule 指针更新到新提交
5. 再提交并推送 `krux`

如果你不是要改代码，而是要复现这次已经验证过的 Amigo 固件，请先看[Amigo 固定快照重编译教程](from-github-snapshot.zh-CN.md)。

## 交接时最容易踩的坑

- 不要把 `sd/` 提交进去，它只是本机模拟器数据
- 不要把 `projects/maixpy_amigo/.config.mk` 之类本机生成文件当正式代码
- 如果 `git status` 里只有 `firmware/MaixPy` 显示变化，先确认是 submodule 指针变化，不要误以为整个底层仓库都变了
- 如果以后接手时脑子里只有一句话，那就记住：`krux` 管功能，`MaixPy` 管底层

## 推荐阅读顺序

如果你是后来接手的人，建议按这个顺序看：

1. [README 的中文快速开始](../../../README.md)
2. [本页：仓库结构与接手说明](repo-structure.zh-CN.md)
3. [Amigo 迁移计划 / 接手记录](../../amigo-tp-web3-port-plan.zh-CN.md)
4. [Amigo 固定快照重编译教程](from-github-snapshot.zh-CN.md)
5. [Amigo 固件从源码编译并烧录](from-source.zh-CN.md)
