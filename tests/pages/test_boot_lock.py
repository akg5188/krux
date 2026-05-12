from . import create_ctx


def test_boot_lock_store_set_verify_and_clear(amigo, tmp_path):
    from krux.pages.boot_lock import BootLockStore

    path = str(tmp_path / "boot_lock.json")
    store = BootLockStore(path)

    ok, message = store.set_pin("1234")

    assert ok
    assert message == "开机口令已保存"
    assert store.is_configured()
    assert store.verify_pin("1234")
    assert not store.verify_pin("0000")

    store.clear()
    assert not store.is_configured()


def test_boot_lock_store_rejects_invalid_pin(amigo, tmp_path):
    from krux.pages.boot_lock import BootLockStore

    store = BootLockStore(str(tmp_path / "boot_lock.json"))

    ok, message = store.set_pin("123")

    assert not ok
    assert message == "口令必须是 4 到 12 位数字"
    assert not store.is_configured()


def test_boot_lock_unlock_retries_then_accepts(amigo, mocker, tmp_path):
    from krux.pages.boot_lock import BootLockPage, BootLockStore

    store = BootLockStore(str(tmp_path / "boot_lock.json"))
    store.set_pin("1234")
    ctx = create_ctx(mocker, [])
    page = BootLockPage(ctx, store)
    page.capture_from_keypad = mocker.MagicMock(side_effect=["0000", "1234"])
    page.flash_text = mocker.MagicMock()
    page.flash_error = mocker.MagicMock()

    assert page.unlock_at_boot()
    page.flash_error.assert_called_once_with("开机口令错误\n还可重试 4 次")


def test_boot_lock_ignores_invalid_pin_lengths(amigo, mocker, tmp_path):
    from krux.pages.boot_lock import BootLockPage, BootLockStore

    store = BootLockStore(str(tmp_path / "boot_lock.json"))
    store.set_pin("1234")
    ctx = create_ctx(mocker, [])
    page = BootLockPage(ctx, store)
    page.capture_from_keypad = mocker.MagicMock(side_effect=["", "1", "1234"])
    page.flash_text = mocker.MagicMock()
    page.flash_error = mocker.MagicMock()

    assert page.unlock_at_boot()
    assert page.flash_error.call_args_list == [
        mocker.call("口令必须是 4 到 12 位数字"),
        mocker.call("口令必须是 4 到 12 位数字"),
    ]


def test_boot_lock_unlock_fails_after_max_attempts(amigo, mocker, tmp_path):
    from krux.pages.boot_lock import (
        BOOT_LOCK_MAX_ATTEMPTS,
        BootLockPage,
        BootLockStore,
    )

    store = BootLockStore(str(tmp_path / "boot_lock.json"))
    store.set_pin("1234")
    ctx = create_ctx(mocker, [])
    page = BootLockPage(ctx, store)
    page.capture_from_keypad = mocker.MagicMock(
        side_effect=["0000"] * BOOT_LOCK_MAX_ATTEMPTS
    )
    page.flash_text = mocker.MagicMock()
    page.flash_error = mocker.MagicMock()

    assert not page.unlock_at_boot()
    page.flash_error.assert_any_call("开机口令错误次数过多\n设备即将关机")


def test_sign_pin_not_required_when_unconfigured(amigo, mocker, tmp_path):
    from krux.pages.boot_lock import BootLockPage, BootLockStore

    store = BootLockStore(str(tmp_path / "boot_lock.json"))
    ctx = create_ctx(mocker, [])
    page = BootLockPage(ctx, store)
    page.capture_from_keypad = mocker.MagicMock()

    assert page.verify_before_signing() is True
    page.capture_from_keypad.assert_not_called()


def test_secret_pin_requires_configured_pin(amigo, mocker, tmp_path):
    from krux.pages.boot_lock import BootLockPage, BootLockStore

    store = BootLockStore(str(tmp_path / "boot_lock.json"))
    ctx = create_ctx(mocker, [])
    page = BootLockPage(ctx, store)
    page.flash_error = mocker.MagicMock()
    page.capture_from_keypad = mocker.MagicMock()

    assert page.verify_before_secret_access() is False
    page.flash_error.assert_called_once_with("请先设置开机口令\n才能显示助记词")
    page.capture_from_keypad.assert_not_called()


def test_sign_pin_fails_after_three_attempts(amigo, mocker, tmp_path):
    from krux.pages.boot_lock import MENU_SHUTDOWN, BootLockPage, BootLockStore

    store = BootLockStore(str(tmp_path / "boot_lock.json"))
    store.set_pin("1234")
    ctx = create_ctx(mocker, [])
    page = BootLockPage(ctx, store)
    page.capture_from_keypad = mocker.MagicMock(side_effect=["0000", "1111", "2222"])
    page.flash_text = mocker.MagicMock()
    page.flash_error = mocker.MagicMock()

    assert page.verify_before_signing() == MENU_SHUTDOWN
    page.flash_error.assert_any_call("口令错误 3 次\n设备即将关机")


def test_secret_pin_fails_after_three_attempts(amigo, mocker, tmp_path):
    from krux.pages.boot_lock import MENU_SHUTDOWN, BootLockPage, BootLockStore

    store = BootLockStore(str(tmp_path / "boot_lock.json"))
    store.set_pin("1234")
    ctx = create_ctx(mocker, [])
    page = BootLockPage(ctx, store)
    page.capture_from_keypad = mocker.MagicMock(side_effect=["0000", "1111", "2222"])
    page.flash_text = mocker.MagicMock()
    page.flash_error = mocker.MagicMock()

    assert page.verify_before_secret_access() == MENU_SHUTDOWN
    page.flash_error.assert_any_call("口令错误 3 次\n设备即将关机")


def test_sign_pin_accepts_correct_pin(amigo, mocker, tmp_path):
    from krux.pages.boot_lock import BootLockPage, BootLockStore

    store = BootLockStore(str(tmp_path / "boot_lock.json"))
    store.set_pin("1234")
    ctx = create_ctx(mocker, [])
    page = BootLockPage(ctx, store)
    page.capture_from_keypad = mocker.MagicMock(side_effect=["0000", "1234"])
    page.flash_text = mocker.MagicMock()
    page.flash_error = mocker.MagicMock()

    assert page.verify_before_signing() is True
    page.flash_text.assert_any_call("签名前验证通过", mocker.ANY)


def test_secret_pin_accepts_correct_pin(amigo, mocker, tmp_path):
    from krux.pages.boot_lock import BootLockPage, BootLockStore

    store = BootLockStore(str(tmp_path / "boot_lock.json"))
    store.set_pin("1234")
    ctx = create_ctx(mocker, [])
    page = BootLockPage(ctx, store)
    page.capture_from_keypad = mocker.MagicMock(side_effect=["1234"])
    page.flash_text = mocker.MagicMock()
    page.flash_error = mocker.MagicMock()

    assert page.verify_before_secret_access() is True
    page.flash_text.assert_any_call("验证通过", mocker.ANY)


def test_boot_lock_enable_change_and_disable(amigo, mocker, tmp_path):
    from krux.pages.boot_lock import BootLockPage, BootLockStore, MENU_CONTINUE

    store = BootLockStore(str(tmp_path / "boot_lock.json"))
    ctx = create_ctx(mocker, [])
    page = BootLockPage(ctx, store)
    page.prompt = mocker.MagicMock(return_value=True)
    page.capture_from_keypad = mocker.MagicMock(side_effect=["1234", "1234"])
    page.flash_text = mocker.MagicMock()

    assert page.enable() == MENU_CONTINUE
    assert store.verify_pin("1234")

    page.capture_from_keypad = mocker.MagicMock(
        side_effect=["1234", "5678", "5678"]
    )
    assert page.change_pin() == MENU_CONTINUE
    assert store.verify_pin("5678")

    page.capture_from_keypad = mocker.MagicMock(side_effect=["5678"])
    assert page.disable() == MENU_CONTINUE
    assert not store.is_configured()
