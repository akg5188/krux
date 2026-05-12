# The MIT License (MIT)

# Copyright (c) 2021-2024 Krux contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# pylint: disable=C0103

import sys
import time
import gc
import os

MIN_SPLASH_WAIT_TIME = 1000
_LAST_BOOT_STAGE = "starting"
power_manager = None


def _error_text(error):
    try:
        return "%s: %s" % (error.__class__.__name__, error)
    except Exception:
        return "unknown error"


def boot_status(text):
    """Tracks boot progress without touching the LCD during early startup."""
    global _LAST_BOOT_STAGE
    _LAST_BOOT_STAGE = text


def init_power_manager():
    """Import power management after LCD init so early boot failures stay visible."""
    global power_manager
    from krux.power import power_manager as imported_power_manager

    power_manager = imported_power_manager
    return power_manager


def boot_failed(error):
    """Keep a visible error on screen instead of getting stuck on the logo."""
    try:
        sys.print_exception(error)
    except Exception:
        pass
    try:
        from krux.display import display

        display.clear()
        display.draw_centered_text(
            "启动失败\n%s\n\n%s" % (_LAST_BOOT_STAGE, _error_text(error)[:80])
        )
    except Exception:
        pass
    while True:
        time.sleep(1)


def draw_splash():
    """Display splash while loading modules"""
    from krux.display import display, SPLASH

    display.initialize_lcd()
    display.clear()
    display.draw_centered_text(SPLASH)


def check_for_updates():
    """Checks SD card, if a valid firmware is found asks if user wants to update the device"""

    # Check if the SD card is inserted and contains a firmware before loading the firmware module
    try:
        os.stat("/sd/firmware.bin")
    except OSError:
        return

    from krux import firmware

    if firmware.upgrade():
        power_manager.shutdown()

    # Unimport firware
    sys.modules.pop("krux.firmware")
    del sys.modules["krux"].firmware
    del firmware


def tc_code_verification(ctx_pin):
    """Loads and run the Pin Verification page"""
    from krux.krux_settings import Settings, TC_CODE_PATH

    # Checks if there is a pin set
    try:
        if not (os.stat(TC_CODE_PATH)[0] & 0x4000) == 0:
            raise OSError
    except OSError:
        print("No pin set")
        return True

    ctx_pin.tc_code_enabled = True

    if not Settings().security.boot_flash_hash:
        return True

    from krux.pages.tc_code_verification import TCCodeVerification

    pin_verification_page = TCCodeVerification(ctx_pin)
    pin_hash = pin_verification_page.capture(return_hash=True)
    if not pin_hash:
        return False

    from krux.pages.flash_tools import FlashHash

    flash_hash = FlashHash(ctx_pin, pin_hash)
    flash_hash.generate()

    # Unimport FlashHash the free memory
    sys.modules.pop("krux.pages.flash_tools")
    del sys.modules["krux"].pages.flash_tools
    del FlashHash

    # Unimport TCCodeVerification the free memory
    sys.modules.pop("krux.pages.tc_code_verification")
    del sys.modules["krux"].pages.tc_code_verification
    del TCCodeVerification
    return True


def login(ctx_login):
    """Loads and run the Login page"""
    from krux.pages.login import Login

    start_from = None
    while True:
        login_page = Login(ctx_login)
        if not login_page.run(start_from):
            # Exited for shutdown
            break

        if ctx_login.wallet is not None:
            # Exited for Home menu
            break

        # Exited for change in Settings
        start_from = Login.SETTINGS_MENU_INDEX

    # Unimport Login the free memory
    sys.modules.pop("krux.pages.login")
    del sys.modules["krux"].pages.login
    del Login


def prepare_login_display(ctx_display):
    """Clear the display once before drawing the main menu."""
    try:
        ctx_display.display.clear()
    except Exception as error:
        sys.print_exception(error)


def boot_lock_verification(ctx_lock):
    """Loads and runs the Amigo boot lock page when configured."""
    from krux.pages.boot_lock import BootLockPage

    unlocked = BootLockPage(ctx_lock).unlock_at_boot()

    # Unimport BootLockPage to free memory
    sys.modules.pop("krux.pages.boot_lock")
    del sys.modules["krux"].pages.boot_lock
    del BootLockPage
    return unlocked


def home(ctx_home):
    """Loads and run the Login page"""
    from krux.pages.home_pages.home import Home

    if ctx_home.is_logged_in():
        while True:
            if not Home(ctx_home).run():
                break


try:
    preimport_ticks = time.ticks_ms()
    draw_splash()
    boot_status("初始化电源")
    init_power_manager()
    boot_status("检查SD卡")
    check_for_updates()
    gc.collect()

    boot_status("加载系统")
    from krux.context import ctx
    from krux.auto_shutdown import auto_shutdown

    ctx.power_manager = power_manager
    auto_shutdown.add_ctx(ctx)


    # If importing happened too fast, sleep the difference so the logo
    # will be shown
    postimport_ticks = time.ticks_ms()
    if preimport_ticks + MIN_SPLASH_WAIT_TIME > postimport_ticks:
        time.sleep_ms(preimport_ticks + MIN_SPLASH_WAIT_TIME - postimport_ticks)

    boot_status("校验安全设置")
    if not tc_code_verification(ctx):
        power_manager.shutdown()
    boot_status("检查开机口令")
    if not boot_lock_verification(ctx):
        power_manager.shutdown()
    boot_status("进入主菜单")
    prepare_login_display(ctx)
    login(ctx)
    gc.collect()
    home(ctx)

    ctx.clear()
    power_manager.shutdown()
except Exception as error:
    boot_failed(error)
