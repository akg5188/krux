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

这版固件的主构建入口还是父仓库脚本：

```bash
nice -n 10 ./krux build maixpy_amigo
```

如果你只想单独重建底层 `maixpy.bin`，或者电脑资源很紧张，也可以直接在 `MaixPy` 里低负载编译：

```bash
nice -n 10 make -C firmware/MaixPy/projects/maixpy_amigo/build -j1
```

这两个命令的侧重点不同：

- `./krux build maixpy_amigo` 适合完整交付
- `make -C ...` 适合只重建底层镜像，或者做快速验证

### 你应该看到什么

完整构建结束后，常见产物是：

- `build/firmware.bin`
- `build/kboot.kfpkg`

如果你走的是底层镜像路径，还会看到：

- `firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin`
- `firmware/MaixPy/projects/maixpy_amigo/build/maixpy.elf`

这次我们验证过的 `maixpy.bin` SHA256 是：

```text
04a59041f4d20dd9a6ac79d82807325c1d5db38d8ef1e787af820555722ead4b
```

如果你用同样的仓库快照、同样的 `MaixPy` 提交和同样的编译环境，应该能得到一致结果。

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
