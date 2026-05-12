# Amigo 直接烧录 `maixpy.bin`

这页给已经在 `firmware/MaixPy/projects/maixpy_amigo/build/` 里拿到 `maixpy.bin` 的维护者看。

如果这台电脑没有单独下载的 `ktool-linux`，也可以直接用仓库自带的 `python3 firmware/Kboot/build/ktool.py`。

`maixpy.bin` 是 Amigo 上更底层的应用镜像，适合已经有可用启动器、只想更新应用层的时候使用。
如果你的板子还是空的，或者你想一次性刷完整交付包，请先看[Amigo 预编译包烧录](from-pre-built-release.zh-CN.md)或[Amigo 源码编译并烧录](from-source.zh-CN.md)。

普通刷机、第一次刷机、给用户交付、或者刚从官方固件切到自定义固件时，不要走本页。请刷完整 `kboot.kfpkg`，它会同时写入启动器、配置区和固件应用区。

2026-05-09 真机验证后再强调一次：旧的 `904960` 字节自定义 `firmware.bin` 和 `build/amigo-custom-kboot.kfpkg` 会黑屏，不要再刷。

## 这和整包刷机有什么区别

- `./krux build maixpy_amigo` 的普通交付产物是 `build/firmware.bin` 和 `build/kboot.kfpkg`
- `firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin` 是更底层的应用镜像
- `maixpy.bin` 不等于正式交付整包，它不包含完整刷机包里的启动器和配置区
- 如果你要判断正式交付是否完整，要看 `kboot.kfpkg` 里的 `firmware.bin`，不要只看 `maixpy.bin`

## 直接烧录

`maixpy.bin` 对应的旧示例闪存地址是 `0x00280000`，也就是十进制 `2621440`。

注意：Krux 的完整 `kboot.kfpkg` 默认让启动器从 `0x00080000` 加载 `firmware.bin`。如果你只是把 `maixpy.bin` 写到 `0x00280000`，设备可能写入成功但启动器不会加载它。

### Linux

先确认串口权限。如果你想长期修好权限：

```bash
sudo usermod -aG dialout $USER
```

执行后需要重新登录或重启才会生效。如果只是这次马上刷机，可以临时放开串口：

```bash
sudo chmod a+rw /dev/ttyUSB0 /dev/ttyUSB1
```

如果仓库里有 `firmware/Kboot/build/ktool.py`，优先用这一条：

```bash
python3 firmware/Kboot/build/ktool.py -B goE -b 1500000 -a 2621440 -p /dev/ttyUSB1 firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin
```

如果 `/dev/ttyUSB1` 没响应，再换 `/dev/ttyUSB0`：

```bash
python3 firmware/Kboot/build/ktool.py -B goE -b 1500000 -a 2621440 -p /dev/ttyUSB0 firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin
```

如果你用的是 release 包里的 `ktool-linux`：

```bash
./ktool-linux -B goE -b 1500000 -a 2621440 -p /dev/ttyUSB1 firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin
```

### macOS

```bash
./ktool-mac -B goE -b 1500000 -a 2621440 firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin
```

如果自动识别串口失败，再手动加 `-p`，例如：

```bash
./ktool-mac -B goE -b 1500000 -a 2621440 -p /dev/cu.usbserial-10 firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin
```

### Windows

先在 **设备管理器 -> 端口 (COM 和 LPT)** 里找串口号。

```pwsh
.\ktool-win.exe -B goE -b 1500000 -a 2621440 firmware/MaixPy/projects/maixpy_amigo/build/maixpy.bin
```

如果自动识别失败，再手动加 `-p`，例如：

```pwsh
.\ktool-win.exe -B goE -b 1500000 -a 2621440 -p COM6 firmware\MaixPy\projects\maixpy_amigo\build\maixpy.bin
```

## 什么时候不要直接刷这个文件

- 你要给普通用户交付整包
- 你的板子还没有可用的启动器
- 你想确认 release 包可以直接安装
- 你刚从官方固件切到自定义固件
- 你不确定启动器配置区是否正确

这种情况下，请改用 `kboot.kfpkg` 或 `./krux flash maixpy_amigo`。

## 刷完以后

- 断电后重新上电更稳妥
- 看到 Amigo 中文首页，说明基本成功
- 如果没有正常启动，优先回到[源码编译并烧录](from-source.zh-CN.md)或[预编译包烧录](from-pre-built-release.zh-CN.md)重新检查
