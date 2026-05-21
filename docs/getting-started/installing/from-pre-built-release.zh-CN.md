# Amigo 固件从官方预编译包烧录

这份教程适合第一次使用 Krux 的人。你不需要自己编译代码，只要下载已经打好的固件包，然后刷进 `Sipeed Matrix Amigo` 就行。

这里说的“官方预编译包”，指的是上游 `selfcustody/krux` 的正式发行版，不是这份下游备份仓库自己重新打包的文件。

如果你想自己改代码、自己编译，请看另一页：[Amigo 固件从源码编译并烧录](from-source.zh-CN.md)。
如果你以后要接手维护，先看[Krux 仓库结构与接手说明](repo-structure.zh-CN.md)。
如果你卡在智能卡、USB 口、打印机或者固件大小这些问题上，先看[Amigo 常见问题](../../faq.zh-CN.md)。

## 1. 下载固件包

打开上游 Krux 的发布页，下载最新的官方 release 压缩包：

<https://github.com/selfcustody/krux/releases>

下载后先解压，进入解压出来的文件夹。

## 2. 先确认文件没坏

推荐先检查下载的文件是否完整。

### 自动检查

如果你解压后的目录里有 `krux` 脚本，可以用它检查 SHA256 和签名：

```bash
./krux sha256 {{latest_krux}}.zip
./krux verify {{latest_krux}}.zip selfcustody.pem
```

### 手动检查

如果你更习惯手动检查，也可以这样做：

```bash
sha256sum {{latest_krux}}.zip.sha256.txt -c
openssl sha256 <{{latest_krux}}.zip -binary | openssl pkeyutl -verify -pubin -inkey selfcustody.pem -sigfile {{latest_krux}}.zip.sig
```

如果你在 macOS 上执行 `sha256sum`，可能需要先安装：

```bash
brew install coreutils
```

## 3. 连接 Amigo

1. 用 USB-C 线连接 `Amigo` **底部** 的 USB-C 口。
2. 不要优先用左侧那个口。
3. 如果电脑识别出两个串口，这是正常现象，后面如果自动刷写失败，可以手动指定端口。

## 4. 烧录

### Linux

```bash
./ktool-linux -B goE -b 1500000 maixpy_amigo/kboot.kfpkg
```

如果自动找错串口，就手动指定：

```bash
./ktool-linux -B goE -b 1500000 maixpy_amigo/kboot.kfpkg -p /dev/ttyUSB1
```

### macOS

先取消 Ktool 的隔离属性：

```bash
xattr -d com.apple.quarantine ktool-mac
```

然后刷写：

```bash
./ktool-mac -B goE -b 1500000 maixpy_amigo/kboot.kfpkg
```

如果自动选错端口，就手动指定：

```bash
./ktool-mac -B goE -b 1500000 maixpy_amigo/kboot.kfpkg -p /dev/cu.usbserial-10
```

### Windows

先打开 **设备管理器 -> 端口 (COM 和 LPT)**，找到对应的串口号。

然后刷写：

```pwsh
.\ktool-win.exe -B goE -b 1500000 maixpy_amigo\kboot.kfpkg
```

如果自动识别失败，就手动指定：

```pwsh
.\ktool-win.exe -B goE -b 1500000 maixpy_amigo\kboot.kfpkg -p COM6
```

## 5. 刷完以后看什么

- 重新插拔一次 USB 更稳妥
- 开机后应该看到 Krux 的启动画面
- Amigo 默认会进入中文界面

如果你看到黑屏、卡 Logo，先确认你刷的是 `maixpy_amigo/kboot.kfpkg`，不是别的设备包。

## 6. 常见问题

### 找不到设备

- 确认插的是 Amigo 底部 USB-C 口
- 换一条支持数据传输的 USB-C 线
- 先断电，再重新上电
- Linux 下可以看 `ls /dev/ttyUSB*`
- macOS 下可以看 `ls /dev/cu.usb*`
- Windows 下看设备管理器里的串口

### 烧录中途失败

- 拔掉 USB 线，等几秒再插回去
- 换另一个串口试试
- 还不行就手动加 `-p`

### 电脑拦住 Ktool

- Linux / macOS 下先给文件执行权限

```bash
chmod +x ./ktool-linux
chmod +x ./ktool-mac
```

- macOS 如果提示未验证，先执行

```bash
xattr -d com.apple.quarantine ktool-mac
```

如果这些还不行，再看仓库里的 [故障排查](../../troubleshooting.en.md)。
