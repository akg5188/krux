#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEVICE="maixpy_amigo"
MAIXPY_DIR="$REPO_ROOT/firmware/MaixPy"
PROJECT_DIR="$MAIXPY_DIR/projects/$DEVICE"
BUILTIN_DIR="$PROJECT_DIR/builtin_py"
KBOOT_BUILD_DIR="$REPO_ROOT/firmware/Kboot/build"
ROOT_BUILD_DIR="$REPO_ROOT/build"
OFFICIAL_KBOOT="${AMIGO_OFFICIAL_KBOOT:-}"
DEFAULT_OFFICIAL_KBOOT="/tmp/krux-official-v26.04.0/krux-v26.04.0/maixpy_amigo/kboot.kfpkg"

TOOLCHAIN_PATH="${TOOLCHAIN_PATH:-}"
if [ -z "$TOOLCHAIN_PATH" ]; then
    if [ -d "/home/ak/123/toolchains/kendryte-toolchain/bin" ]; then
        TOOLCHAIN_PATH="/home/ak/123/toolchains/kendryte-toolchain/bin"
    else
        TOOLCHAIN_PATH="/opt/kendryte-toolchain/bin"
    fi
fi

MAIXPY_MAKE_JOBS="${MAIXPY_MAKE_JOBS:-1}"
KBOOT_MAKE_JOBS="${KBOOT_MAKE_JOBS:-1}"
MIN_FIRMWARE_SIZE="${AMIGO_MIN_FIRMWARE_SIZE:-1200000}"
OUTPUT_PREFIX="amigo-official-base"
DIAG_BOOT=0
SKIP_BUILD=0
SKIP_KBOOT=0
USE_OFFICIAL_SHELL=0

usage() {
    cat <<'EOF'
Usage: firmware/scripts/build-amigo-official-base.sh [options]

Build Krux for Sipeed Matrix Amigo using the official MaixPy/Kboot pipeline.

Options:
  --diag-boot     Build a minimal LCD/backlight diagnostic package.
  --prepare-only   Only sync Krux and vendor Python files into builtin_py.
  --skip-kboot     Build firmware.bin but do not create kboot.kfpkg.
  --official-shell Package with bootloader/config copied from official Amigo kboot.
  -h, --help       Show this help.

Environment:
  TOOLCHAIN_PATH            Kendryte toolchain bin directory.
  MAIXPY_MAKE_JOBS          MaixPy make jobs, default 1.
  KBOOT_MAKE_JOBS           Kboot make jobs, default 1.
  AMIGO_MIN_FIRMWARE_SIZE   Minimum firmware.bin size, default 1200000.
  AMIGO_OFFICIAL_KBOOT      Official Amigo kboot.kfpkg used by --official-shell.
                            If unset, the script tries /tmp, then build/ caches.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --diag-boot)
            DIAG_BOOT=1
            OUTPUT_PREFIX="amigo-diag"
            MIN_FIRMWARE_SIZE="${AMIGO_MIN_FIRMWARE_SIZE:-500000}"
            ;;
        --prepare-only)
            SKIP_BUILD=1
            ;;
        --skip-kboot)
            SKIP_KBOOT=1
            ;;
        --official-shell)
            USE_OFFICIAL_SHELL=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

require_file() {
    if [ ! -e "$1" ]; then
        echo "Missing required path: $1" >&2
        exit 1
    fi
}

resolve_official_kboot() {
    if [ -n "$OFFICIAL_KBOOT" ]; then
        require_file "$OFFICIAL_KBOOT"
        return
    fi

    for candidate in \
        "$DEFAULT_OFFICIAL_KBOOT" \
        "$ROOT_BUILD_DIR/amigo-official-shell-template.kfpkg" \
        "$ROOT_BUILD_DIR/amigo-official-base-official-shell-kboot.kfpkg" \
        "$ROOT_BUILD_DIR/amigo-diag-official-shell-kboot.kfpkg"
    do
        if [ -e "$candidate" ]; then
            OFFICIAL_KBOOT="$candidate"
            echo "==> Using official shell source: $OFFICIAL_KBOOT"
            return
        fi
    done

    echo "Missing official Amigo kboot shell." >&2
    echo "Set AMIGO_OFFICIAL_KBOOT=/path/to/maixpy_amigo/kboot.kfpkg" >&2
    echo "or restore one of the build/ official-shell cache files." >&2
    exit 1
}

copy_dir() {
    local src="$1"
    local dst="$2"
    require_file "$src"
    rm -rf "$dst"
    cp -R "$src" "$dst"
}

remove_pycache() {
    find "$1" -type d -name "__pycache__" -prune -exec rm -rf {} +
    find "$1" -type f -name "*.pyc" -delete
}

remove_mpy() {
    find "$1" -type f -name "*.mpy" -delete
}

find_cmake() {
    if command -v cmake >/dev/null 2>&1; then
        return
    fi
    if [ -x "$REPO_ROOT/.venv/bin/cmake" ]; then
        export PATH="$REPO_ROOT/.venv/bin:$PATH"
        return
    fi
    echo "cmake not found. Install cmake or keep repo .venv available." >&2
    exit 1
}

prepare_builtin_py() {
    echo "==> Preparing official-base builtin_py for $DEVICE"
    require_file "$BUILTIN_DIR/board.py"
    require_file "$BUILTIN_DIR/fpioa_manager.py"
    require_file "$BUILTIN_DIR/pmu.py"

    find "$BUILTIN_DIR" -mindepth 1 -maxdepth 1 \
        ! -name "board.py" \
        ! -name "fpioa_manager.py" \
        ! -name "pmu.py" \
        -exec rm -rf {} +
    remove_pycache "$BUILTIN_DIR"

    if [ "$DIAG_BOOT" -eq 1 ]; then
        echo "==> Installing minimal Amigo diagnostic _boot.py"
        cp "$REPO_ROOT/firmware/scripts/amigo-diag-boot.py" "$BUILTIN_DIR/_boot.py"
        remove_pycache "$BUILTIN_DIR"
        remove_mpy "$BUILTIN_DIR"
        echo "==> builtin_py file count: $(find "$BUILTIN_DIR" -type f -name '*.py' | wc -l)"
        echo "==> builtin_py mpy residue: $(find "$BUILTIN_DIR" -type f -name '*.mpy' | wc -l)"
        return
    fi

    copy_dir "$REPO_ROOT/vendor/urtypes/src/urtypes" "$BUILTIN_DIR/urtypes"
    copy_dir "$REPO_ROOT/vendor/foundation-ur-py/src/ur" "$BUILTIN_DIR/ur"
    copy_dir "$REPO_ROOT/vendor/embit/src/embit" "$BUILTIN_DIR/embit"

    rm -rf "$BUILTIN_DIR/embit/util/prebuilt"
    rm -rf "$BUILTIN_DIR/embit/liquid"
    rm -f "$BUILTIN_DIR/embit/psbtview.py"
    rm -f "$BUILTIN_DIR/embit/slip39.py"
    rm -f "$BUILTIN_DIR/embit/wordlists/slip39.py"
    rm -f "$BUILTIN_DIR/embit/util/ctypes_secp256k1.py"
    rm -f "$BUILTIN_DIR/embit/util/py_secp256k1.py"
    rm -f "$BUILTIN_DIR/embit/util/py_ripemd160.py"
    remove_mpy "$BUILTIN_DIR/embit"
    remove_mpy "$BUILTIN_DIR/ur"
    remove_mpy "$BUILTIN_DIR/urtypes"

    copy_dir "$REPO_ROOT/src/krux" "$BUILTIN_DIR/krux"
    cp "$REPO_ROOT/src/boot.py" "$BUILTIN_DIR/_boot.py"

    # Do not freeze desktop pytest compatibility shims or stale local .mpy
    # artifacts into MaixPy firmware. Stale .mpy files can override freshly
    # compiled modules and are risky across MicroPython builds.
    rm -f "$BUILTIN_DIR/board.py.tmp"
    rm -f "$BUILTIN_DIR/ucryptolib.py" "$BUILTIN_DIR/ujson.py" "$BUILTIN_DIR/urandom.py"
    remove_pycache "$BUILTIN_DIR"
    remove_mpy "$BUILTIN_DIR"

    # Amigo is a Chinese-first build. Keeping only zh-CN cuts frozen module
    # size and reduces boot memory pressure on K210.
    find "$BUILTIN_DIR/krux/translations" -maxdepth 1 -type f -name "*.py" \
        ! -name "__init__.py" \
        ! -name "zh.py" \
        -delete

    if [ -d "$PROJECT_DIR/compile/overrides" ]; then
        cp -rf "$PROJECT_DIR/compile/overrides/." "$MAIXPY_DIR/"
    fi

    echo "==> builtin_py file count: $(find "$BUILTIN_DIR" -type f -name '*.py' | wc -l)"
    echo "==> builtin_py mpy residue: $(find "$BUILTIN_DIR" -type f -name '*.mpy' | wc -l)"
}

build_firmware() {
    echo "==> Building MaixPy firmware with MAIXPY_MAKE_JOBS=$MAIXPY_MAKE_JOBS"
    find_cmake
    export PATH="$TOOLCHAIN_PATH:$PATH"
    export MAIXPY_MAKE_JOBS
    (
        cd "$PROJECT_DIR"
        python3 project.py --toolchain "$TOOLCHAIN_PATH" --toolchain-prefix "riscv64-unknown-elf-" clean
        python3 project.py --toolchain "$TOOLCHAIN_PATH" --toolchain-prefix "riscv64-unknown-elf-" distclean
        python3 project.py --toolchain "$TOOLCHAIN_PATH" --toolchain-prefix "riscv64-unknown-elf-" build
        cp build/maixpy.bin build/firmware.bin
    )

    local firmware="$PROJECT_DIR/build/firmware.bin"
    local firmware_size
    firmware_size="$(stat -c %s "$firmware")"
    echo "==> firmware.bin size: $firmware_size bytes"
    if [ "$firmware_size" -lt "$MIN_FIRMWARE_SIZE" ]; then
        echo "Refusing to continue: firmware.bin is smaller than $MIN_FIRMWARE_SIZE bytes." >&2
        echo "This usually means Krux was not frozen into the official Amigo firmware." >&2
        exit 1
    fi
}

build_kboot_package() {
    echo "==> Building full Kboot package with KBOOT_MAKE_JOBS=$KBOOT_MAKE_JOBS"
    find_cmake
    export PATH="$TOOLCHAIN_PATH:$PATH"
    export TOOLCHAIN_PATH
    export KBOOT_MAKE_JOBS

    cp "$PROJECT_DIR/build/firmware.bin" "$KBOOT_BUILD_DIR/firmware.bin"
    (
        cd "$KBOOT_BUILD_DIR"
        ./CLEAN.sh
        ./BUILD.sh
    )

    mkdir -p "$ROOT_BUILD_DIR"
    cp "$PROJECT_DIR/build/firmware.bin" "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-firmware.bin"
    cp "$KBOOT_BUILD_DIR/kboot.kfpkg" "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-kboot.kfpkg"
    sha256sum "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-firmware.bin" \
        > "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-firmware.bin.sha256.txt"
    sha256sum "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-kboot.kfpkg" \
        > "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-kboot.kfpkg.sha256.txt"

    echo "==> Output:"
    ls -lh "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-firmware.bin" \
        "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-kboot.kfpkg"
}

build_official_shell_package() {
    echo "==> Packaging with official Amigo Kboot shell"
    resolve_official_kboot

    mkdir -p "$ROOT_BUILD_DIR"
    cp "$PROJECT_DIR/build/firmware.bin" "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-firmware.bin"

    local output_kfpkg="$ROOT_BUILD_DIR/$OUTPUT_PREFIX-official-shell-kboot.kfpkg"
    local shell_kboot="$OFFICIAL_KBOOT"
    local shell_tmp=""
    if [ -e "$output_kfpkg" ] && [ "$(realpath "$shell_kboot")" = "$(realpath "$output_kfpkg")" ]; then
        shell_tmp="$output_kfpkg.shell"
        cp "$shell_kboot" "$shell_tmp"
        shell_kboot="$shell_tmp"
    fi

    OFFICIAL_KBOOT="$shell_kboot" \
    FIRMWARE_BIN="$PROJECT_DIR/build/firmware.bin" \
    OUTPUT_KFPKG="$output_kfpkg" \
    python3 - <<'PY'
import os
import zipfile

official_kboot = os.environ["OFFICIAL_KBOOT"]
firmware_bin = os.environ["FIRMWARE_BIN"]
output_kfpkg = os.environ["OUTPUT_KFPKG"]
names = (
    "flash-list.json",
    "bootloader_lo.bin",
    "bootloader_hi.bin",
    "config.bin",
    "firmware.bin",
)
fixed_dt = (2009, 1, 3, 18, 15, 0)

with zipfile.ZipFile(official_kboot, "r") as src:
    with zipfile.ZipFile(
        output_kfpkg, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as dst:
        for name in names:
            data = open(firmware_bin, "rb").read() if name == "firmware.bin" else src.read(name)
            info = zipfile.ZipInfo(name, fixed_dt)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            dst.writestr(info, data)
PY
    if [ -n "$shell_tmp" ]; then
        rm -f "$shell_tmp"
    fi

    sha256sum "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-firmware.bin" \
        > "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-firmware.bin.sha256.txt"
    sha256sum "$output_kfpkg" \
        > "$output_kfpkg.sha256.txt"

    echo "==> Output:"
    ls -lh "$ROOT_BUILD_DIR/$OUTPUT_PREFIX-firmware.bin" "$output_kfpkg"
}

prepare_builtin_py
if [ "$SKIP_BUILD" -eq 1 ]; then
    echo "==> Prepare-only mode complete."
    exit 0
fi

build_firmware
if [ "$SKIP_KBOOT" -eq 1 ]; then
    echo "==> Skipped Kboot package."
    exit 0
fi

if [ "$USE_OFFICIAL_SHELL" -eq 1 ]; then
    build_official_shell_package
else
    build_kboot_package
fi
