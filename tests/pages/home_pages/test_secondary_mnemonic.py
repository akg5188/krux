from .test_home import tdata
from .. import create_ctx


def test_default_secondary_encrypt_and_restore(mocker, amigo):
    from embit.networks import NETWORKS
    from krux.input import BUTTON_ENTER
    from krux.key import Key, TYPE_SINGLESIG
    from krux.pages.home_pages.secondary_mnemonic import SecondaryMnemonic
    from krux.wallet import Wallet

    mnemonic = (
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon "
        "abandon abandon about"
    )
    encrypted_words = SecondaryMnemonic.shift_words(
        mnemonic.split(" "),
        SecondaryMnemonic._default_entries(False),
    )
    encrypted_mnemonic = " ".join(encrypted_words)

    ctx = create_ctx(
        mocker,
        [
            BUTTON_ENTER,  # Leave result page
        ],
        Wallet(Key(mnemonic, TYPE_SINGLESIG, NETWORKS["main"])),
    )
    secondary = SecondaryMnemonic(ctx)
    mocker.spy(secondary, "display_mnemonic")

    secondary.default_encrypt()

    secondary.display_mnemonic.assert_called_once_with(
        encrypted_mnemonic,
        title="二次加密结果",
    )
    assert ctx.wallet.key.mnemonic == mnemonic

    assert (
        " ".join(
            SecondaryMnemonic.shift_words(
                encrypted_words,
                SecondaryMnemonic._default_entries(True),
            )
        )
        == mnemonic
    )

    ctx = create_ctx(
        mocker,
        [
            BUTTON_ENTER,  # Leave result page
            BUTTON_ENTER,  # Load restored mnemonic
        ],
        Wallet(Key(mnemonic, TYPE_SINGLESIG, NETWORKS["main"])),
    )
    ctx.wallet.key.mnemonic = encrypted_mnemonic
    secondary = SecondaryMnemonic(ctx)

    secondary.default_restore()

    assert ctx.wallet.key.mnemonic == mnemonic


def test_secondary_parse_custom_entries(mocker, amigo):
    from krux.pages.home_pages.secondary_mnemonic import SecondaryMnemonic

    entries = SecondaryMnemonic.parse_shift_entries(
        "+1 -2 *3 /4 +5 -6 +7 -8 +9 -10 +11 -12"
    )

    assert entries[0] == ("+", 1)
    assert entries[1] == ("-", 2)
    assert entries[2] == ("*", 3)
    assert entries[3] == ("/", 4)
    assert SecondaryMnemonic.format_shift_entries(entries).startswith(
        "+1 -2 *3 /4"
    )


def test_secondary_rejects_24_words(mocker, amigo, tdata):
    from krux.input import BUTTON_ENTER
    from krux.pages.home_pages.secondary_mnemonic import SecondaryMnemonic
    from krux.wallet import Wallet

    ctx = create_ctx(
        mocker,
        [BUTTON_ENTER],
        Wallet(tdata.SINGLESIG_24_WORD_KEY),
    )
    secondary = SecondaryMnemonic(ctx)
    mocker.spy(secondary, "flash_error")

    secondary.default_encrypt()

    secondary.flash_error.assert_called_once_with("二次助记词第一版只支持 12 词")


def test_restore_secondary_from_steel_plate_numbers(mocker, amigo):
    from embit.networks import NETWORKS
    from embit.wordlists.bip39 import WORDLIST
    from krux.input import BUTTON_ENTER
    from krux.key import Key, TYPE_SINGLESIG
    from krux.pages import MENU_EXIT
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.pages.home_pages.secondary_mnemonic import SecondaryMnemonic
    from krux.pages.login import Login
    from krux.wallet import Wallet

    mnemonic = (
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon "
        "abandon abandon about"
    )
    fake_words = SecondaryMnemonic.shift_words(
        mnemonic.split(" "),
        SecondaryMnemonic._default_entries(False),
    )
    fake_indices = [WORDLIST.index(word) for word in fake_words]
    plate_groups = []
    for index in fake_indices:
        weights = MnemonicsView._steel_punch_weights(index)
        plate_groups.append(" ".join(str(weight) for weight in weights) or "0")
    raw_plate_numbers = ",".join(plate_groups)

    assert SecondaryMnemonic.words_from_indices(
        SecondaryMnemonic.parse_steel_plate_indices(raw_plate_numbers)
    ) == fake_words

    ctx = create_ctx(
        mocker,
        [BUTTON_ENTER],
        Wallet(Key(mnemonic, TYPE_SINGLESIG, NETWORKS["main"])),
    )
    login = Login(ctx)
    mocker.patch.object(login, "capture_from_keypad", return_value=raw_plate_numbers)
    load_spy = mocker.patch.object(
        login,
        "_load_key_from_words",
        return_value=MENU_EXIT,
    )

    assert login._load_key_from_secondary_steel() == MENU_EXIT
    load_spy.assert_called_once_with(mnemonic.split(" "))


def test_restore_secondary_from_steel_plate_numbers_custom(mocker, amigo):
    from embit.networks import NETWORKS
    from embit.wordlists.bip39 import WORDLIST
    from krux.input import BUTTON_ENTER
    from krux.key import Key, TYPE_SINGLESIG
    from krux.pages import MENU_EXIT
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.pages.home_pages.secondary_mnemonic import SecondaryMnemonic
    from krux.pages.login import Login
    from krux.wallet import Wallet

    mnemonic = (
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon "
        "abandon abandon about"
    )
    encrypt_entries = SecondaryMnemonic.parse_shift_entries(
        "+1 +2 +3 +4 +5 +6 +7 +8 +9 +10 +11 +12"
    )
    restore_entries = SecondaryMnemonic.parse_shift_entries(
        "-1 -2 -3 -4 -5 -6 -7 -8 -9 -10 -11 -12",
        default_operator="-",
    )
    fake_words = SecondaryMnemonic.shift_words(mnemonic.split(" "), encrypt_entries)
    fake_indices = [WORDLIST.index(word) for word in fake_words]
    plate_groups = []
    for index in fake_indices:
        weights = MnemonicsView._steel_punch_weights(index)
        plate_groups.append(" ".join(str(weight) for weight in weights) or "0")
    raw_plate_numbers = ",".join(plate_groups)

    ctx = create_ctx(
        mocker,
        [BUTTON_ENTER],
        Wallet(Key(mnemonic, TYPE_SINGLESIG, NETWORKS["main"])),
    )
    login = Login(ctx)
    mocker.patch.object(
        login,
        "capture_from_keypad",
        side_effect=[
            raw_plate_numbers,
            SecondaryMnemonic.format_shift_entries(restore_entries),
        ],
    )
    load_spy = mocker.patch.object(
        login,
        "_load_key_from_words",
        return_value=MENU_EXIT,
    )

    assert login._load_key_from_secondary_steel(custom=True) == MENU_EXIT
    load_spy.assert_called_once_with(mnemonic.split(" "))
