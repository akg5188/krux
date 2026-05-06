import pytest

from .. import create_ctx
from ...test_web3 import build_tpr1_pages, build_tp_raw_request, make_wallet


def test_home_menu_includes_web3_entry(mocker, amigo):
    from krux.pages.home_pages.home import Home

    ctx = create_ctx(mocker, None)
    home = Home(ctx)
    labels = [name for name, _ in home.menu.menu]

    assert labels[:4] == [
        "扫码签名\n比特币 / 链上 / 消息",
        "助记词工具\n备份 / BIP85 / 钢板",
        "连接钱包\n公钥 / 地址 / 描述符",
        "固件自检\n设备 / 触摸 / SD 卡",
    ]


def test_web3_submenu_items(mocker, amigo):
    from krux.pages.home_pages.web3_ui import Web3

    ctx = create_ctx(mocker, None)
    page = Web3(ctx)
    menu_mock = mocker.patch("krux.pages.home_pages.web3_ui.Menu")
    menu_mock.return_value.run_loop.return_value = None

    page.web3()

    assert menu_mock.call_count == 1
    menu_items = menu_mock.call_args.args[1]
    assert [item[0] for item in menu_items] == [
        "连接钱包\nOKX / Bitget / MetaMask",
        "扫码签名\n消息 / 交易 / TP 中转",
    ]
    assert [item[1].__name__ for item in menu_items] == [
        "connect_wallet",
        "scan_and_sign",
    ]


def test_web3_connect_wallet_flow(mocker, amigo):
    from krux.pages.home_pages.web3_ui import Web3

    ctx = create_ctx(mocker, None)
    page = Web3(ctx)
    menu_mock = mocker.patch("krux.pages.home_pages.web3_ui.Menu")
    menu_mock.return_value.run_loop.return_value = None

    page.connect_wallet()

    assert menu_mock.call_count == 1
    menu_items = menu_mock.call_args.args[1]
    assert [item[0] for item in menu_items] == [
        "OKX 钱包",
        "Bitget 钱包",
        "MetaMask",
        "Rabby",
        "TokenPocket",
    ]


@pytest.mark.parametrize(
    "wallet_profile, expected_prefix, expected_title, min_pages",
    [
        ("okx", "UR:CRYPTO-MULTI-ACCOUNTS/", "OKX 钱包", 2),
        ("bitget", "UR:CRYPTO-MULTI-ACCOUNTS/", "Bitget 钱包", 1),
        ("metamask", "UR:CRYPTO-HDKEY/", "MetaMask", 1),
    ],
)
def test_web3_connect_wallet_profile_flow(
    mocker, amigo, wallet_profile, expected_prefix, expected_title, min_pages
):
    from krux.input import BUTTON_ENTER
    from krux.pages.home_pages.web3_ui import Web3
    from krux.qr import FORMAT_NONE

    wallet = make_wallet()
    ctx = create_ctx(mocker, [BUTTON_ENTER], wallet=wallet)
    page = Web3(ctx)
    display_mock = mocker.patch.object(page, "display_qr_codes")

    page._connect_wallet_profile(wallet_profile)

    display_mock.assert_called_once()
    qr_pages, qr_format, title = display_mock.call_args.args
    assert isinstance(qr_pages, list)
    assert len(qr_pages) >= min_pages
    assert qr_pages[0].startswith(expected_prefix)
    assert qr_format == FORMAT_NONE
    assert title == expected_title
    assert ctx.input.wait_for_button.call_count == 1


def test_web3_scan_and_sign_flow(mocker, amigo):
    from krux.input import BUTTON_ENTER
    from krux.pages.home_pages.web3_ui import Web3
    from krux.pages.qr_capture import QRCodeCapture
    from krux.qr import FORMAT_NONE, FORMAT_TP
    from krux.web3 import derive_web3_account

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    raw_request = build_tp_raw_request(
        "personalSign",
        {
            "address": expected_address,
            "message": "hello web3",
            "dappName": "Krux",
            "source": "krux",
        },
    )

    ctx = create_ctx(mocker, [BUTTON_ENTER], wallet=wallet)
    page = Web3(ctx)
    display_mock = mocker.patch.object(page, "display_qr_codes")
    mocker.patch.object(QRCodeCapture, "qr_capture_loop", return_value=(raw_request, FORMAT_TP))

    page.scan_and_sign()

    display_mock.assert_called_once()
    response_pages, qr_format, title = display_mock.call_args.args
    assert response_pages[0].startswith("tp:personalSignSignature-")
    assert qr_format == FORMAT_NONE
    assert title == "消息签名结果"
    assert ctx.input.wait_for_button.call_count == 1


def test_web3_scan_and_sign_relay_flow(mocker, amigo):
    from krux.input import BUTTON_ENTER
    from krux.pages.home_pages.web3_ui import Web3
    from krux.pages.qr_capture import QRCodeCapture
    from krux.qr import FORMAT_NONE, FORMAT_RELAY
    from krux.web3 import derive_web3_account

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    raw_request = build_tp_raw_request(
        "personalSign",
        {
            "address": expected_address,
            "message": "relay hello",
            "dappName": "Krux",
            "source": "krux",
        },
        request_id="relay-ui",
    )

    ctx = create_ctx(mocker, [BUTTON_ENTER], wallet=wallet)
    page = Web3(ctx)
    display_mock = mocker.patch.object(page, "display_qr_codes")
    relay_payload = build_tpr1_pages(raw_request, chunk_chars=500)[0]
    mocker.patch.object(
        QRCodeCapture,
        "qr_capture_loop",
        return_value=(relay_payload, FORMAT_RELAY),
    )

    page.scan_and_sign()

    display_mock.assert_called_once()
    response_pages, qr_format, title = display_mock.call_args.args
    assert response_pages[0].startswith("tp:personalSignSignature-")
    assert qr_format == FORMAT_NONE
    assert title == "消息签名结果"
    assert ctx.input.wait_for_button.call_count == 1


@pytest.mark.parametrize(
    "tx_data, expected_title",
    [
        (
            {
                "to": "0x1111111111111111111111111111111111111111",
                "value": "0",
                "data": "0x",
                "gasLimit": "21000",
                "nonce": "0",
                "gasPrice": "1",
                "type": 0,
            },
            "交易签名结果",
        ),
        (
            {
                "to": "0x1111111111111111111111111111111111111111",
                "value": "0",
                "data": "0x",
                "gasLimit": "21000",
                "nonce": "1",
                "maxFeePerGas": "1000000000",
                "maxPriorityFeePerGas": "100000000",
                "accessList": [],
                "type": 2,
            },
            "结构化交易签名结果",
        ),
    ],
)
def test_web3_scan_and_sign_transaction_flow(mocker, amigo, tx_data, expected_title):
    from krux.input import BUTTON_ENTER
    from krux.pages.home_pages.web3_ui import Web3
    from krux.pages.qr_capture import QRCodeCapture
    from krux.qr import FORMAT_NONE, FORMAT_TP
    from krux.web3 import derive_web3_account

    wallet = make_wallet()
    expected_address = derive_web3_account(wallet.key).address
    raw_request = build_tp_raw_request(
        "signTransaction",
        {
            "id": "req-tx-ui",
            "address": expected_address,
            "txData": tx_data,
            "dappName": "Krux",
            "source": "krux",
        },
        request_id="req-tx-ui",
    )

    ctx = create_ctx(mocker, [BUTTON_ENTER], wallet=wallet)
    page = Web3(ctx)
    display_mock = mocker.patch.object(page, "display_qr_codes")
    mocker.patch.object(QRCodeCapture, "qr_capture_loop", return_value=(raw_request, FORMAT_TP))

    page.scan_and_sign()

    display_mock.assert_called_once()
    response_pages, qr_format, title = display_mock.call_args.args
    assert response_pages[0].startswith("tp:signTransactionSignature-")
    assert qr_format == FORMAT_NONE
    assert title == expected_title
    assert ctx.input.wait_for_button.call_count == 1
