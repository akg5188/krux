# Amigo 固件从源码编译并烧录

这份教程只针对 `Sipeed Matrix Amigo`。目标是把你自己修改后的 Krux 固件编译出来，然后刷进开发板。

这不是原版 Krux 的通用构建说明，而是基于上游 `selfcustody/krux` 的 Amigo 下游改造版教程。
如果你要看原版项目的通用构建和发布信息，请回到上游仓库。

如果你只是想先把机器刷起来，建议先看[官方预编译包烧录教程](from-pre-built-release.zh-CN.md)。
如果你已经改过代码，或者想自己编译，就继续看这篇。
如果你在看这篇时遇到智能卡、USB 口、打印机或者固件大小问题，先看[Amigo 常见问题](../../faq.zh-CN.md)。
如果你还不确定该点哪一页，先看[Amigo 刷机路径图](amigo-flash-path.zh-CN.md)。
如果你想重现这次已经验证过的 GitHub 快照，并尽量保证编译结果和现在一致，先看[Amigo 固定快照重编译教程](from-github-snapshot.zh-CN.md)。

## 0. 先看懂仓库

这份固件不是只有一个 Git 仓库。

- `krux` 是主仓库，放界面、菜单、助记词、Web3、测试和文档
- `firmware/MaixPy` 是 `krux` 的子模块，放 Amigo 的底层板级支持、MicroPython 端口、屏幕和触摸相关代码

如果你以后只改中文、菜单、功能和测试，一般只动 `krux`。
如果你以后改到硬件底层、驱动或者板级适配，才进入 `firmware/MaixPy`。

如果你改了 `firmware/MaixPy`，顺序要记住：

1. 先在 `firmware/MaixPy` 里提交并推送
2. 再回到父仓库更新 submodule 指针
3. 最后再推 `krux`

更详细的说明请先看[仓库结构与接手说明](repo-structure.zh-CN.md)。
如果你是来复现这次已经固定好的 Amigo 版本，请优先看[固定快照重编译教程](from-github-snapshot.zh-CN.md)。

## 准备工作

- 一台能运行 `git`、`python3`、`make`、`cmake` 的电脑
- Kendryte K210 工具链，本机默认路径是 `/home/ak/123/toolchains/kendryte-toolchain/bin`
- 一条支持数据传输的 USB-C 线
- Amigo 本体
- Krux 仓库源码

如果你有 Docker，也可以继续用官方 `./krux build maixpy_amigo` 路线。
这台电脑当前更推荐用本页下面的“官方基线本地构建”，因为它低负载、可检查、不会一上来吃满电脑。

## 1. 获取源码

如果你还没有克隆仓库：

```bash
git clone --recurse-submodules https://github.com/akg5188/krux
cd krux
```

如果你已经有仓库，只想更新到最新代码：

```bash
git pull origin main
git submodule update --init --recursive
```

## 2. 编译 Amigo 固件

### 推荐方式：官方基线本地构建

这条命令做的是“官方 Amigo 固件底座 + 当前 Krux 功能代码”：

- 保留 Amigo 官方板级 `board.py`
- 同步当前 `src/krux` 主程序
- 同步 `embit`、`ur`、`urtypes` 依赖
- 把 `src/boot.py` 作为固件启动入口 `_boot.py`
- 排除桌面测试专用的 `src/board.py`、`ujson.py`、`urandom.py`、`ucryptolib.py`
- 用 `MAIXPY_MAKE_JOBS=1` 和 `KBOOT_MAKE_JOBS=1` 低负载编译，避免把电脑拖死

在仓库根目录运行：

```bash
MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 \
nice -n 10 firmware/scripts/build-amigo-official-base.sh
```

编译完成后，正式交付文件在：

- `build/amigo-official-base-firmware.bin`
- `build/amigo-official-base-kboot.kfpkg`
- `build/amigo-official-base-firmware.bin.sha256.txt`
- `build/amigo-official-base-kboot.kfpkg.sha256.txt`

普通刷机和交付优先刷：

```text
build/amigo-official-base-kboot.kfpkg
```

### Docker 方式

在仓库根目录运行：

```bash
./krux build maixpy_amigo
```

Docker 编译完成后，`build/` 目录里应该能看到这两个文件：

- `firmware.bin`
- `kboot.kfpkg`

如果你在本机没有 Docker，就不要硬装一大堆东西把电脑拖死，优先用上面的本地构建脚本。

## 2.1 先检查产物，不合格不要刷

先看整包里有没有完整的 `firmware.bin`：

```bash
unzip -l build/amigo-official-base-kboot.kfpkg
```

官方 `v26.04.0` 的 Amigo `firmware.bin` 是 `1746688` 字节。我们自定义版本因为加了中文和功能，大小可以不同，但必须是同一量级。

如果看到下面这些情况，不要刷：

- 只有几十 KB
- 只有几百 KB
- 大约 `904960` 字节的旧失败产物
- 只有 `maixpy.bin`，没有 `kboot.kfpkg`

旧的 `build/amigo-custom-kboot.kfpkg` 已经真机验证黑屏，不再作为交付固件。

如果你已经在 `firmware/MaixPy/projects/maixpy_amigo/build/` 里看到了 `maixpy.bin` 和 `maixpy.elf`，那说明你看到的是更底层的应用构建产物。普通交付还是必须优先刷完整 `kboot.kfpkg`；如果你只想直接更新 `maixpy.bin`，可以看[Amigo 直接烧录 `maixpy.bin`](from-maixpy-bin.zh-CN.md)，但普通用户不要走那条路线。

## 3. 连接 Amigo

1. 用 USB-C 线连接 `Amigo` **底部** 的 USB-C 口。
2. 不要优先用左侧那个口。
3. 如果电脑识别出两个串口，这是正常现象。烧录时如果自动识别失败，通常换另一个串口就能解决。

## 4. 烧录固件

### 方式 A：直接用项目脚本

这是最省事的方式，推荐先试这个：

```bash
./krux flash maixpy_amigo
```

这个命令会自动调用 Ktool，并尝试自动找到 Amigo 的串口。

### 方式 B：手动调用 Ktool

如果你已经有 release 包里自带的 `ktool-linux`、`ktool-mac` 或 `ktool-win.exe`，又或者你想在离线环境里手动刷写，就可以手动指定串口。
如果自动识别失败，或者 Ktool 选错了端口，也可以用这一种方式。

#### Linux

先看串口列表：

```bash
ls /dev/ttyUSB*
```

再刷写：

```bash
sudo python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/ttyUSB1 build/amigo-official-base-kboot.kfpkg
```

这台 Amigo 真机已经验证 `115200` 最稳。高速刷写如果不稳定，优先降回 `115200`。

如果不用 `sudo` 时看到 `Permission denied: '/dev/ttyUSB1'`，说明当前用户没有串口权限。临时刷机直接用上面的 `sudo` 命令；长期使用可以把当前用户加入 `dialout` 组后重新登录。

#### macOS

先去掉 Ktool 的隔离属性：

```bash
xattr -d com.apple.quarantine ktool-mac
```

再查看串口：

```bash
ls /dev/cu.usb*
```

再刷写：

```bash
./ktool-mac -B goE -b 115200 build/amigo-official-base-kboot.kfpkg -p /dev/cu.usbserial-10
```

#### Windows

先在 **设备管理器 -> 端口 (COM 和 LPT)** 里看串口号，然后刷写：

```pwsh
.\ktool-win.exe -B goE -b 115200 build\amigo-official-base-kboot.kfpkg -p COM6
```

## 5. 如果你刷的是官方 release

如果你下载的是官方预编译压缩包，路径里的 `build/kboot.kfpkg` 换成 release 包内对应的文件即可：

```bash
maixpy_amigo/kboot.kfpkg
```

Linux 示例：

```bash
./ktool-linux -B goE -b 115200 maixpy_amigo/kboot.kfpkg
```

## 6. 烧录后检查

- 烧录完成后，先拔掉 USB 再重新插一次
- 重新开机后，应该能看到 Krux 启动画面
- Amigo 默认会进入中文界面

如果屏幕亮了，但触摸方向不对，或者颜色显示不正常，可以去看故障排查里的 `Maix Amigo LCD Settings` 部分。

## 常见问题

### 电脑找不到设备

- 换一条支持数据传输的 USB-C 线
- 确认你插的是 Amigo 底部 USB-C 口
- 先把板子断电，再重新上电
- Linux 下可以看：

```bash
ls /dev/ttyUSB*
```

- macOS 下可以看：

```bash
ls /dev/cu.usb*
```

- Windows 下去设备管理器里确认串口是否出现

### 烧录中途失败

- 拔掉 USB 线，等几秒再重新插回去
- 换另一个串口试试
- 如果自动识别失败，就手动加 `-p`
- 如果提示 `Permission denied`，Linux 下先用 `sudo` 重新执行刷机命令

### Ktool 无法运行

- Linux / macOS 下先给文件执行权限：

```bash
chmod +x ./ktool-linux
chmod +x ./ktool-mac
```

- macOS 如果被系统拦住了，执行：

```bash
xattr -d com.apple.quarantine ktool-mac
```

### 烧录后黑屏或卡在 Logo

- 先确认刷进去的是 `maixpy_amigo` 对应的完整 `kboot.kfpkg`，不是别的设备包
- 不要继续重复刷 `build/amigo-custom-kboot.kfpkg`
- 不要继续重复刷已经记录为黑屏的 `build/amigo-official-base-kboot.kfpkg`
- 先刷回官方包确认机器能亮屏

本机已经验证过的官方恢复命令：

```bash
python3 firmware/Kboot/build/ktool.py -B goE -b 115200 -p /dev/ttyUSB1 \
/tmp/krux-official-v26.04.0/krux-v26.04.0/maixpy_amigo/kboot.kfpkg
```

官方包能亮屏后，再回到本页重新构建官方基线自定义包。

如果要判断黑屏是在底层 LCD/背光，还是 Krux Python 启动层，可以先构建最小诊断包：

```bash
MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 \
firmware/scripts/build-amigo-official-base.sh --diag-boot --official-shell
```

诊断包路径是：

```text
build/amigo-diag-official-shell-kboot.kfpkg
```

这个包复用官方 Amigo `kboot.kfpkg` 里的 bootloader 和配置区，只替换本机编译出的最小诊断 `firmware.bin`，可以少一个变量。

刷入诊断包后，如果屏幕显示 `AMIGO DIAG BOOT OK`，说明 MaixPy 和 LCD/背光底层能工作，下一步排查 Krux 启动脚本。如果诊断包仍黑屏，先立刻刷回官方包救机，再排查本机 MaixPy/K210/LCD 构建环境或硬件连接。

如果完整 Krux 包刷入后是白屏，先不要重复乱刷。当前真机曾定位到一种白屏原因：MaixPy 不支持 CPython 的 `str.translate()`，导致 `_boot.py` 画启动图时崩溃。修复点在 `src/krux/display.py` 的 `_safe_text()`；修复后重新构建 `build/amigo-official-base-official-shell-kboot.kfpkg`，串口应能看到进入 `[KRUX BOOT] login page run start`。

完整 Krux 包推荐使用官方壳构建：

```bash
MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1 nice -n 10 \
firmware/scripts/build-amigo-official-base.sh --official-shell
```

当前真机验证过的刷机包路径是：

```text
build/amigo-official-base-official-shell-kboot.kfpkg
```

如果要避免手动输错端口，可以用安全脚本。它只认 Sipeed 的固定 `by-id` 串口，找不到就退出，不会自动改刷其他设备：

```bash
AMIGO_WAIT_SECONDS=300 firmware/scripts/flash-amigo-diag.sh
```

如果还是不行，再去看 `troubleshooting.en.md` 里的 Amigo 相关排查说明。
