from . import create_ctx


def test_self_check_menu_items(mocker, amigo):
    from krux.pages.self_check import SelfCheck

    ctx = create_ctx(mocker, None)
    page = SelfCheck(ctx)
    labels = [name for name, _ in page.menu.menu]

    assert labels[:4] == [
        "状态总览\n版本 / 屏幕 / 功能",
        "SD 卡检查\n检测存储卡",
        "测试套件\n逐项检查设备",
        "触摸测试\n检查大屏触摸",
    ]


def test_self_check_status_overview(mocker, amigo):
    from krux.input import BUTTON_ENTER
    from krux.pages.self_check import SelfCheck

    ctx = create_ctx(mocker, [BUTTON_ENTER])
    page = SelfCheck(ctx)

    page.status_overview()

    rendered = ctx.display.draw_centered_text.call_args.args[0]
    assert "固件自检" in rendered
    assert "Sipeed Matrix Amigo" in rendered
    assert "链上:已启用" in rendered
    assert "签名:本机助记词" in rendered


def test_login_menu_includes_self_check(mocker, amigo):
    from krux.pages.login import Login

    ctx = create_ctx(mocker, None)
    page = Login(ctx)
    labels = [name for name, _ in page.menu.menu]

    assert "固件自检\n设备 / 触摸 / SD 卡" in labels
    assert labels[labels.index("工具") + 1] == "固件自检\n设备 / 触摸 / SD 卡"
