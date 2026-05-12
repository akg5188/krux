"""Minimal Amigo boot diagnostic.

This frozen _boot.py intentionally avoids importing Krux. It only initializes
the Amigo LCD/backlight path and draws short ASCII text, so a black screen here
points to the MaixPy/K210/LCD build layer rather than Krux page code.
"""

import time


BLACK = 0x0000
BLUE = 0x001F
GREEN = 0x07E0
RED = 0xF800
WHITE = 0xFFFF
YELLOW = 0xFFE0


def log(text):
    print("[AMIGO DIAG] " + text)


def set_pmu_backlight(level=15):
    try:
        from pmu import PMUController

        pmu = PMUController()
        # AXP173 LDO2/3 backlight range used by Krux is 7..15.
        if level < 7:
            level = 7
        if level > 15:
            level = 15
        pmu.set_screen_brightness(level)
        log("pmu backlight set")
    except Exception as error:
        log("pmu backlight failed: %s" % error)


def draw_diag_screen(lcd_type, invert, bgr, rotation, color, label):
    import lcd

    log(
        "lcd init start type=%s invert=%s bgr=%s rotation=%s"
        % (lcd_type, invert, bgr, rotation)
    )
    lcd.init(invert=invert, lcd_type=lcd_type)
    lcd.mirror(True)
    lcd.bgr_to_rgb(bgr)
    lcd.rotation(rotation)
    log("lcd init done width=%s height=%s" % (lcd.width(), lcd.height()))

    lcd.clear(color)
    lcd.fill_rectangle(20, 20, 440, 280, BLACK)
    lcd.draw_outline(20, 20, 440, 280, WHITE)
    lcd.draw_string(54, 58, "AMIGO DIAG BOOT OK", GREEN, BLACK)
    lcd.draw_string(54, 100, label, WHITE, BLACK)
    lcd.draw_string(54, 142, "If you see any page,", YELLOW, BLACK)
    lcd.draw_string(54, 176, "MaixPy display works.", YELLOW, BLACK)
    lcd.draw_string(54, 232, "Auto cycling LCD modes", WHITE, BLACK)


try:
    log("boot start")
    set_pmu_backlight(15)
except Exception as error:
    log("failed: %s" % error)
    try:
        import lcd

        lcd.init(invert=True, lcd_type=1)
        lcd.clear(RED)
        lcd.draw_string(20, 40, "AMIGO DIAG FAILED", WHITE, RED)
        lcd.draw_string(20, 82, str(error)[:32], WHITE, RED)
    except Exception:
        pass

LCD_TESTS = (
    (0, True, True, 2, BLUE, "lcd_type=0 invert=1 bgr=1"),
    (1, True, True, 2, GREEN, "lcd_type=1 invert=1 bgr=1"),
    (0, False, True, 2, YELLOW, "lcd_type=0 invert=0 bgr=1"),
    (1, False, True, 2, RED, "lcd_type=1 invert=0 bgr=1"),
    (0, True, False, 2, WHITE, "lcd_type=0 invert=1 bgr=0"),
    (1, True, False, 2, BLUE, "lcd_type=1 invert=1 bgr=0"),
    (0, True, True, 0, GREEN, "rotation=0 type=0"),
    (0, True, True, 1, YELLOW, "rotation=1 type=0"),
    (0, True, True, 3, RED, "rotation=3 type=0"),
)

while True:
    for test in LCD_TESTS:
        try:
            draw_diag_screen(*test)
            log("screen drawn " + test[5])
        except Exception as error:
            log("draw failed %s: %s" % (test[5], error))
        time.sleep(4)
