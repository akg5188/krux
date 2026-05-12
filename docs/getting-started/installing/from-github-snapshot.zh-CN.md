# Amigo 固定快照重编译教程

这页是给以后维护、换电脑、换 AI 时用的。目标不是“随便编出一个能用的固件”，而是从 GitHub 重新拉回这次已经验证过的 Amigo 快照，并尽量得到同一条构建基线。

如果你只是想先刷机，不需要自己编译，先看[Amigo 预编译包烧录](from-pre-built-release.zh-CN.md)。
如果你只想直刷底层 `maixpy.bin`，看[Amigo 直接烧录 `maixpy.bin`](from-maixpy-bin.zh-CN.md)。

## 这次固定了什么

| 项目 | 固定值 |
| --- | --- |
| 父仓库 | `https://github.com/akg5188/krux` |
| 父仓库分支 | `amigo-snapshot` |
| 父仓库提交 | `8f22a11f07c8333d663fa1887d83f968e785e300` |
| 子模块 | `https://github.com/akg5188/MaixPy` |
| 子模块分支 | `main` |
| 子模块提交 | `a90beb74ae1037782e4a10bd33dc2f79f7bf0e88` |

这两个点要一起固定。只改父仓库、不固定子模块，或者只拉 `main` 不看 `amigo-snapshot`，都不算同一版。

## 1. 拉回这条快照

第一次克隆：

```bash
git clone --recurse-submodules -b amigo-snapshot https://github.com/akg5188/krux
cd krux
```

如果你已经有仓库，只是想切回这条固定快照：

```bash
git fetch origin
git checkout amigo-snapshot
git submodule update --init --recursive
```

## 2. 先确认版本没有漂

先看父仓库：

```bash
git rev-parse HEAD
```

应该是：

```text
8f22a11f07c8333d663fa1887d83f968e785e300
```

再看 `MaixPy`：

```bash
git -C firmware/MaixPy rev-parse HEAD
git submodule status --recursive
```

应该看到 `a90beb74ae1037782e4a10bd33dc2f79f7bf0e88 firmware/MaixPy`。

不要运行：

```bash
git submodule update --remote
```

那会把子模块浮动到最新提交，结果就不再是这次快照。

## 3. 重新编译

2026-05-09 修正：这条线现在默认走“官方 Amigo 固件底座 + 当前 Krux 功能代码”的完整整包构建，不再使用旧的几百 KB 半成品。

推荐命令：

```bash
MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 \
nice -n 10 firmware/scripts/build-amigo-official-base.sh
```

输出文件：

- `build/amigo-official-base-firmware.bin`
- `build/amigo-official-base-kboot.kfpkg`
- `build/amigo-official-base-firmware.bin.sha256.txt`
- `build/amigo-official-base-kboot.kfpkg.sha256.txt`

如果你有 Docker，也可以用父仓库脚本：

```bash
nice -n 10 ./krux build maixpy_amigo
```

不要再把下面这种命令当成正式交付构建：

```bash
nice -n 10 make -C firmware/MaixPy/projects/maixpy_amigo/build -j1
```

它只能重建已有底层 build 目录，不能保证当前 `src/` 和 vendor 依赖已经完整冻结进固件。

### 这几个坑要避开

- 不要刷 `build/amigo-custom-kboot.kfpkg`，它已经真机验证黑屏
- 不要把几十 KB 或几百 KB 的文件当成完整 Amigo 固件
- 不要只看 `maixpy.bin` 就交付
- 不要把 `src/board.py` 这个桌面测试 fallback 冻结进真机固件
- 不要把 `ujson.py`、`urandom.py`、`ucryptolib.py` 这些桌面测试兼容层冻结进真机固件

### 你应该看到什么

官方 `v26.04.0` 的 Amigo `firmware.bin` 是 `1746688` 字节。自定义版本大小可以不同，但必须是同一量级。

先检查：

```bash
unzip -l build/amigo-official-base-kboot.kfpkg
```

如果 `firmware.bin` 明显太小，说明 Krux 主程序没有完整冻结进去，不要刷。

旧失败产物的 SHA256 是：

```text
04a59041f4d20dd9a6ac79d82807325c1d5db38d8ef1e787af820555722ead4b
```

这是旧 `904960` 字节 `firmware.bin` 的哈希，只作为排错反例，不再作为可交付基线。

## 4. 烧录

如果你要把完整固件刷进 Amigo，继续看：

- [Amigo 源码编译并烧录](from-source.zh-CN.md)

如果你只想单独刷 `maixpy.bin`，继续看：

- [Amigo 直接烧录 `maixpy.bin`](from-maixpy-bin.zh-CN.md)

## 5. 低负载建议

为了避免把电脑资源吃满，建议：

- 先用 `nice -n 10`
- 构建时不要开太大的并发
- 如果只是确认代码没问题，优先只重建一次，不要反复同时开多个构建

## 6. 交接检查清单

以后换电脑、换 AI，或者隔很久再接手时，先检查这四样：

- 父仓库是不是 `amigo-snapshot`
- `firmware/MaixPy` 是不是 `a90beb...`
- `git submodule status --recursive` 有没有漂移
- 产物是不是还在同一条路径下生成

如果这四项都对，通常就是同一条可复现基线。
