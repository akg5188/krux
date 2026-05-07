# Amigo 直接烧录 `maixpy.bin`

这页给已经在 `firmware/MaixPy/projects/maixpy_amigo/build/` 里拿到 `maixpy.bin` 的维护者看。

`maixpy.bin` 是 Amigo 上更底层的应用镜像，适合已经有可用启动器、只想更新应用层的时候使用。
如果你的板子还是空的，或者你想一次性刷完整交付包，请先看[Amigo 预编译包烧录](from-pre-built-release.zh-CN.md)或[Amigo 源码编译并烧录](from-source.zh-CN.md)。

## 这和整包刷机有什么区别

- `./krux build maixpy_amigo` 的普通交付产物是 `build/firmware.bin` 和 `build/kboot.kfpkg`
- `firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin` 是更底层的应用镜像
- `maixpy.bin` 体积小是正常的，因为它不包含完整刷机包里的启动器和打包文件

## 直接烧录

`maixpy.bin` 对应的闪存地址是 `0x00280000`，也就是十进制 `2621440`。

### Linux

```bash
./ktool-linux -B goE -b 1500000 -a 2621440 -t firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin
```

如果自动识别串口失败，再手动加 `-p`，例如：

```bash
./ktool-linux -B goE -b 1500000 -a 2621440 -t firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin -p /dev/ttyUSB1
```

### macOS

```bash
./ktool-mac -B goE -b 1500000 -a 2621440 -t firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin
```

如果自动识别串口失败，再手动加 `-p`，例如：

```bash
./ktool-mac -B goE -b 1500000 -a 2621440 -t firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin -p /dev/cu.usbserial-10
```

### Windows

先在 **设备管理器 -> 端口 (COM 和 LPT)** 里找串口号。

```pwsh
.\ktool-win.exe -B goE -b 1500000 -a 2621440 -t firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin
```

如果自动识别失败，再手动加 `-p`，例如：

```pwsh
.\ktool-win.exe -B goE -b 1500000 -a 2621440 -t firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin -p COM6
```

## 什么时候不要直接刷这个文件

- 你要给普通用户交付整包
- 你的板子还没有可用的启动器
- 你想确认 release 包可以直接安装

这种情况下，请改用 `kboot.kfpkg` 或 `./krux flash maixpy_amigo`。

## 刷完以后

- 断电后重新上电更稳妥
- 看到 Amigo 中文首页，说明基本成功
- 如果没有正常启动，优先回到[源码编译并烧录](from-source.zh-CN.md)或[预编译包烧录](from-pre-built-release.zh-CN.md)重新检查
