# Amigo 固定快照卡片版

如果你已经把仓库拉下来了，只想确认是不是这次同一版，先跑这 3 条：

```bash
git rev-parse HEAD
git -C firmware/MaixPy rev-parse HEAD
git submodule status --recursive
```

核对值：

- 父仓库：`8f22a11f07c8333d663fa1887d83f968e785e300`
- 子模块：`a90beb74ae1037782e4a10bd33dc2f79f7bf0e88`
- `maixpy.bin` SHA256：`04a59041f4d20dd9a6ac79d82807325c1d5db38d8ef1e787af820555722ead4b`

如果你还没拉仓库，或者要重新编译，再跑这 3 条：

```bash
git clone --recurse-submodules -b amigo-snapshot https://github.com/akg5188/krux
cd krux
nice -n 10 ./krux build maixpy_amigo
```

不要执行：

```bash
git submodule update --remote
```

刷机继续看：

- [Amigo 源码编译并烧录](from-source.zh-CN.md)
- [Amigo 直接烧录 `maixpy.bin`](from-maixpy-bin.zh-CN.md)
