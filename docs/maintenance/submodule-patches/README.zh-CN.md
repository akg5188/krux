# Amigo 子模块本地补丁说明

本目录用于保存 `firmware/Kboot` 和 `firmware/MaixPy` 子模块里的本地改动，避免以后重新克隆主仓库时丢失构建修补。

## 补丁文件

- `firmware-Kboot-amigo-local.patch`：Kboot 低负载构建、CMake 兼容参数和 Amigo bootloader 链接地址修补。
- `firmware-MaixPy-amigo-local.patch`：MaixPy Amigo 中文字体、亮度控制、低负载构建和官方底座固件构建相关修补。

## 恢复方式

从主仓库根目录执行：

```bash
git -C firmware/Kboot apply ../../docs/maintenance/submodule-patches/firmware-Kboot-amigo-local.patch
git -C firmware/MaixPy apply ../../docs/maintenance/submodule-patches/firmware-MaixPy-amigo-local.patch
```

如果子模块已经有本地改动，先人工检查 `git -C firmware/Kboot status --short` 和 `git -C firmware/MaixPy status --short`，不要直接覆盖。

## 注意

- `firmware/MaixPy/projects/maixpy_amigo/.config.mk` 是本机生成文件，里面包含本机工具链路径，不提交到主仓库。
- 构建时优先使用低负载参数，避免把电脑卡死：`MAIXPY_MAKE_JOBS=1 KBOOT_MAKE_JOBS=1`。
- 新机器到手后，先刷官方 Krux 或官方 Sipeed 固件确认屏幕、触摸和按键，再刷自定义固件。
