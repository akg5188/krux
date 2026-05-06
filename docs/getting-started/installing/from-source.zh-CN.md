# Amigo 固件从源码编译并烧录

这份教程只针对 `Sipeed Matrix Amigo`。目标是把你自己修改后的 Krux 固件编译出来，然后刷进开发板。

如果你只是想先把机器刷起来，建议先看[官方预编译包烧录教程](from-pre-built-release.zh-CN.md)。
如果你已经改过代码，或者想自己编译，就继续看这篇。

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

## 准备工作

- 一台能运行 `git` 和 `docker` 的电脑
- 一条支持数据传输的 USB-C 线
- Amigo 本体
- Krux 仓库源码

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

在仓库根目录运行：

```bash
./krux build maixpy_amigo
```

编译完成后，`build/` 目录里应该能看到这两个文件：

- `firmware.bin`
- `kboot.kfpkg`

`firmware.bin` 本身只有几百 KB，这是正常的。你截图里看到的“100 多 MB”通常是电脑上的安装器包，或者是把多个设备的文件、`ktool` 工具一起打进去的 release 总包，不是 Amigo 单机固件本体。

如果你只看到了 `firmware.bin`，先不要烧录，说明打包步骤没有完整跑通。请重新执行上面的构建命令，确认 `kboot.kfpkg` 也生成了。

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
./ktool-linux -B goE -b 1500000 build/kboot.kfpkg -p /dev/ttyUSB1
```

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
./ktool-mac -B goE -b 1500000 build/kboot.kfpkg -p /dev/cu.usbserial-10
```

#### Windows

先在 **设备管理器 -> 端口 (COM 和 LPT)** 里看串口号，然后刷写：

```pwsh
.\ktool-win.exe -B goE -b 1500000 build\kboot.kfpkg -p COM6
```

## 5. 如果你刷的是官方 release

如果你下载的是官方预编译压缩包，路径里的 `build/kboot.kfpkg` 换成 release 包内对应的文件即可：

```bash
maixpy_amigo/kboot.kfpkg
```

Linux 示例：

```bash
./ktool-linux -B goE -b 1500000 maixpy_amigo/kboot.kfpkg
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

- 先确认刷进去的是 `maixpy_amigo` 对应的包，不是别的设备包
- 再重新执行一次 `./krux build maixpy_amigo`
- 然后重新烧录

如果还是不行，再去看 `troubleshooting.en.md` 里的 Amigo 相关排查说明。
