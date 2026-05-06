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
