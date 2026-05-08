# Amigo 固定快照极速版

如果你只想快速从 GitHub 重新编译这次已经验证过的 Amigo 版本，直接照下面做。

## 1. 拉代码

```bash
git clone --recurse-submodules -b amigo-snapshot https://github.com/akg5188/krux
cd krux
```

## 2. 确认版本

```bash
git rev-parse HEAD
git -C firmware/MaixPy rev-parse HEAD
git submodule status --recursive
```

应当分别对应：

- 父仓库：`8f22a11f07c8333d663fa1887d83f968e785e300`
- 子模块：`a90beb74ae1037782e4a10bd33dc2f79f7bf0e88`

不要执行 `git submodule update --remote`。

## 3. 编译

完整交付：

```bash
nice -n 10 ./krux build maixpy_amigo
```

只重建底层镜像：

```bash
nice -n 10 make -C firmware/MaixPy/projects/maixpy_amigo/build -j1
```

## 4. 结果

你应该能看到：

- `build/firmware.bin`
- `build/kboot.kfpkg`

底层镜像路径里还会有：

- `firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin`
- `firmware/MaixPy/projects/maixpy_amigo/build/maixpy.elf`

本次验证过的 `maixpy.bin` SHA256：

```text
04a59041f4d20dd9a6ac79d82807325c1d5db38d8ef1e787af820555722ead4b
```

## 5. 刷机

完整固件：

- [Amigo 源码编译并烧录](from-source.zh-CN.md)

只刷 `maixpy.bin`：

- [Amigo 直接烧录 `maixpy.bin`](from-maixpy-bin.zh-CN.md)
