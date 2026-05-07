from .test_home import tdata
from ...shared_mocks import MockPrinter
from .. import create_ctx


def test_load_mnemonic_encryption(mocker, amigo):
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.input import BUTTON_ENTER, BUTTON_PAGE_PREV

    BTN_SEQUENCE = [
        BUTTON_PAGE_PREV,  # Go to Back
        BUTTON_ENTER,  # Exit
    ]

    ctx = create_ctx(mocker, BTN_SEQUENCE)
    m_view = MnemonicsView(ctx)
    m_view.encrypt_mnemonic_menu()

    assert ctx.input.wait_for_button.call_count == len(BTN_SEQUENCE)


def test_mnemonic_words(mocker, m5stickv, tdata):
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.wallet import Wallet
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV
    from krux.qr import FORMAT_NONE

    cases = [
        # See 12 Words
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            None,
            [
                BUTTON_PAGE,
                BUTTON_PAGE,
                BUTTON_ENTER,  # Other
                BUTTON_ENTER,  # Words
                BUTTON_ENTER,  # Leave Page 1
                BUTTON_PAGE_PREV,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        # See 24 Words
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            None,
            [
                BUTTON_PAGE,
                BUTTON_PAGE,
                BUTTON_ENTER,  # Other
                BUTTON_ENTER,  # Words
                BUTTON_ENTER,  # Leave Page 1
                BUTTON_ENTER,  # Leave Page 2
                BUTTON_PAGE_PREV,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        # See and print 24 Words
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_PAGE,
                BUTTON_PAGE,
                BUTTON_ENTER,  # Other
                BUTTON_ENTER,  # Words
                BUTTON_ENTER,  # Leave Page 1
                BUTTON_ENTER,  # Leave Page 2
                BUTTON_ENTER,  # Print
                BUTTON_PAGE_PREV,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
    ]
    num = 0
    for case in cases:
        print(num)
        num = num + 1
        ctx = create_ctx(mocker, case[2], case[0], case[1])
        mnemonics = MnemonicsView(ctx)

        mocker.spy(mnemonics, "display_mnemonic")
        mnemonics.mnemonic()

        mnemonics.display_mnemonic.assert_called_with(
            ctx.wallet.key.mnemonic, suffix="Mnemonic", display_mnemonic=None
        )
        assert ctx.input.wait_for_button.call_count == len(case[2])


def test_mnemonic_standard_qr(mocker, m5stickv, tdata):
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.wallet import Wallet
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV
    from krux.qr import FORMAT_NONE
    from krux.krux_settings import t

    cases = [
        # No print prompt
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            None,  # printer
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_ENTER,  # Plaintext QR
                BUTTON_ENTER,  # Leave QR Viewer
                BUTTON_PAGE_PREV,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            None,  # printer
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_ENTER,  # Plaintext QR
                BUTTON_ENTER,  # Leave QR Viewer
                BUTTON_PAGE_PREV,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        # Print
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_ENTER,  # Plaintext QR
                BUTTON_ENTER,  # Leave QR Viewer
                BUTTON_ENTER,  # Print
                BUTTON_PAGE_PREV,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_ENTER,  # Plaintext QR
                BUTTON_ENTER,  # Leave QR Viewer
                BUTTON_ENTER,  # Print
                BUTTON_PAGE_PREV,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        # Decline to print
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_ENTER,  # Plaintext QR
                BUTTON_ENTER,  # Leave QR Viewer
                BUTTON_PAGE,  # Decline to print
                BUTTON_PAGE_PREV,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_ENTER,  # Plaintext QR
                BUTTON_ENTER,  # Leave QR Viewer
                BUTTON_PAGE,  # Decline to print
                BUTTON_PAGE_PREV,  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
    ]
    num = 0
    for case in cases:
        print(num)
        num = num + 1
        ctx = create_ctx(mocker, case[2], case[0], case[1])
        mnemonics = MnemonicsView(ctx)

        mocker.spy(mnemonics, "display_qr_codes")
        mnemonics.mnemonic()

        title = t("Plaintext QR")
        mnemonics.display_qr_codes.assert_called_with(
            ctx.wallet.key.mnemonic, title=title
        )
        assert ctx.input.wait_for_button.call_count == len(case[2])


def test_mnemonic_compact_qr(mocker, m5stickv, tdata):
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.wallet import Wallet
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV
    from krux.qr import FORMAT_NONE

    cases = [
        # 0 - 12W
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            None,
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_PAGE,  # Move to Compact SeedQR
                BUTTON_ENTER,  # Compact SeedQR
                BUTTON_ENTER,  # Enter QR Menu
                BUTTON_PAGE_PREV,  # change to btn Back to Menu on QR Menu
                BUTTON_ENTER,  # click on back to return to QR codes Backup Menu
                *([BUTTON_PAGE_PREV] * 2),  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        # 1 - 24W
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            None,
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_PAGE,  # Move to Compact SeedQR
                BUTTON_ENTER,  # Compact SeedQR
                BUTTON_ENTER,  # Enter QR Menu
                BUTTON_PAGE_PREV,  # change to btn Back to Menu on QR Menu
                BUTTON_ENTER,  # click on back to return to QR codes Backup Menu
                *([BUTTON_PAGE_PREV] * 2),  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        # 2 - 12W Print
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_PAGE,  # Move to Compact SeedQR
                BUTTON_ENTER,  # Compact SeedQR
                BUTTON_ENTER,  # Enter QR Menu
                *([BUTTON_PAGE] * 3),  # Move to Print
                BUTTON_ENTER,  # Print
                BUTTON_ENTER,  # Confirm Print
                BUTTON_ENTER,  # Enter QR Menu again
                BUTTON_PAGE_PREV,  # move to btn Back to Menu on QR Menu
                BUTTON_ENTER,  # click on back to return to QR codes Backup Menu
                *([BUTTON_PAGE_PREV] * 2),  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        # 3 - 24W Print
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_PAGE,  # Move to Compact SeedQR
                BUTTON_ENTER,  # Compact SeedQR
                BUTTON_ENTER,  # Enter QR Menu
                *([BUTTON_PAGE] * 3),  # Move to Print
                BUTTON_ENTER,  # Print
                BUTTON_ENTER,  # Confirm Print
                BUTTON_ENTER,  # Enter QR Menu again
                BUTTON_PAGE_PREV,  # move to btn Back to Menu on QR Menu
                BUTTON_ENTER,  # click on back to return to QR codes Backup Menu
                *([BUTTON_PAGE_PREV] * 2),  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        # 4 - 12W Print, Decline to print
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_PAGE,  # Move to Compact SeedQR
                BUTTON_ENTER,  # Compact SeedQR
                BUTTON_ENTER,  # Enter QR Menu
                *([BUTTON_PAGE] * 3),  # Move to Print
                BUTTON_ENTER,  # Print
                BUTTON_PAGE,  # Decline Print
                BUTTON_ENTER,  # Enter QR Menu again
                BUTTON_PAGE_PREV,  # move to btn Back to Menu on QR Menu
                BUTTON_ENTER,  # click on back to return to QR codes Backup Menu
                *([BUTTON_PAGE_PREV] * 2),  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
        # 5 - 24W Print, Decline to print
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                BUTTON_PAGE,  # Move to Compact SeedQR
                BUTTON_ENTER,  # Compact SeedQR
                BUTTON_ENTER,  # Enter QR Menu
                *([BUTTON_PAGE] * 3),  # Move to Print
                BUTTON_ENTER,  # Print
                BUTTON_PAGE,  # Decline Print
                BUTTON_ENTER,  # Enter QR Menu again
                BUTTON_PAGE_PREV,  # move to btn Back to Menu on QR Menu
                BUTTON_ENTER,  # click on back to return to QR codes Backup Menu
                *([BUTTON_PAGE_PREV] * 2),  # change to btn Back
                BUTTON_ENTER,  # click on back to return to Mnemonic Backup
                BUTTON_PAGE_PREV,
                BUTTON_ENTER,  # click on back to return to home init screen
            ],
        ),
    ]
    num = 0
    for case in cases:
        print(num)
        num = num + 1
        ctx = create_ctx(mocker, case[2], case[0], case[1])
        mnemonics = MnemonicsView(ctx)

        mocker.spy(mnemonics, "display_seed_qr")
        mnemonics.mnemonic()

        mnemonics.display_seed_qr.assert_called_once()

        assert ctx.input.wait_for_button.call_count == len(case[2])


def test_mnemonic_standard_qr_touch(mocker, amigo, tdata):
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.wallet import Wallet
    from krux.input import BUTTON_TOUCH
    from krux.qr import FORMAT_NONE
    from krux.krux_settings import t

    touch_index = [0, 0]  # Enter QR Code, Enter Plaintext QR

    cases = [
        # No print prompt
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            None,
            [
                *([BUTTON_TOUCH] * 5),
            ],
            touch_index
            + [
                # 0,  # QR code leave press won't read index
                4,  # Back to Mnemonic Backup
                3,  # Back to home init screen
            ],
        ),
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            None,
            [
                *([BUTTON_TOUCH] * 5),
            ],
            touch_index
            + [
                # 0,  # QR code leave press won't read index
                4,  # Back to Mnemonic Backup
                3,  # Back to home init screen
            ],
        ),
        # Print
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            MockPrinter(),
            [
                *([BUTTON_TOUCH] * 6),
            ],
            touch_index
            + [
                # 0,  # QR code leave press won't read index
                0,  # Print
                4,  # Back to Mnemonic Backup
                3,  # Back to home init screen
            ],
        ),
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            MockPrinter(),
            [
                *([BUTTON_TOUCH] * 6),
            ],
            touch_index
            + [
                # 0,  # QR code leave press won't read index
                0,  # Print
                4,  # Back to Mnemonic Backup
                3,  # Back to home init screen
            ],
        ),
        # Decline to print
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            MockPrinter(),
            [
                *([BUTTON_TOUCH] * 6),
            ],
            touch_index
            + [
                # 0,  # QR code leave press won't read index
                1,  # Decline to print
                4,  # Back to Mnemonic Backup
                3,  # Back to home init screen
            ],
        ),
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            MockPrinter(),
            [
                *([BUTTON_TOUCH] * 6),
            ],
            touch_index
            + [
                # 0,  # QR code leave press won't read index
                1,  # Decline to print
                4,  # Back to Mnemonic Backup
                3,  # Back to home init screen
            ],
        ),
    ]
    num = 0
    for case in cases:
        print(num)
        num = num + 1
        ctx = create_ctx(mocker, case[2], case[0], case[1], touch_seq=case[3])
        mnemonics = MnemonicsView(ctx)

        mocker.spy(mnemonics, "display_qr_codes")

        mnemonics.mnemonic()

        title = t("Plaintext QR")
        mnemonics.display_qr_codes.assert_called_with(
            ctx.wallet.key.mnemonic, title=title
        )

        assert ctx.input.wait_for_button.call_count == len(case[2])


def test_mnemonic_encrypted_qr(mocker, m5stickv, tdata):
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.wallet import Wallet
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV

    cases = [
        # 0 - 12W
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            None,
            [
                BUTTON_ENTER,  # QR Code
                *([BUTTON_PAGE] * 3),  # Move to Encrypted QR code
                BUTTON_ENTER,  # Select Encrypted QR code
                BUTTON_ENTER,  # Select Type key
                BUTTON_ENTER,  # type key 'a'
                BUTTON_PAGE_PREV,  # Move to 'Go' key
                BUTTON_ENTER,  # Select 'Go' key
                BUTTON_ENTER,  # Confirm to proceed
                BUTTON_ENTER,  # Confirm to add GCM cam entropy
                BUTTON_ENTER,  # Confirm to use fingerprint as ID
                BUTTON_ENTER,  # See QrCode and exit
                BUTTON_ENTER,  # Select 'Return to QR Viewer'
                BUTTON_ENTER,  # See QrCode and exit
                BUTTON_PAGE_PREV,  # Move 'Back to menu'
                BUTTON_ENTER,  # Select 'Back to menu'
                BUTTON_PAGE_PREV,  # Move to 'Back'
                BUTTON_ENTER,  # Select 'Back'
            ],
        ),
        # 1 - 24W
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            None,
            [
                BUTTON_ENTER,  # QR Code
                *([BUTTON_PAGE] * 3),  # Move to Encrypted QR code
                BUTTON_ENTER,  # Select Encrypted QR code
                BUTTON_ENTER,  # Select Type key
                BUTTON_ENTER,  # type key 'a'
                BUTTON_PAGE_PREV,  # Move to 'Go' key
                BUTTON_ENTER,  # Select 'Go' key
                BUTTON_ENTER,  # Confirm to proceed
                BUTTON_ENTER,  # Confirm to add GCM cam entropy
                BUTTON_ENTER,  # Confirm to use fingerprint as ID
                BUTTON_ENTER,  # See QrCode and exit
                BUTTON_ENTER,  # Select 'Return to QR Viewer'
                BUTTON_ENTER,  # See QrCode and exit
                BUTTON_PAGE_PREV,  # Move 'Back to menu'
                BUTTON_ENTER,  # Select 'Back to menu'
                BUTTON_PAGE_PREV,  # Move to 'Back'
                BUTTON_ENTER,  # Select 'Back'
            ],
        ),
        # 2 - 12W print
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                *([BUTTON_PAGE] * 3),  # Move to Encrypted QR code
                BUTTON_ENTER,  # Select Encrypted QR code
                BUTTON_ENTER,  # Select Type key
                BUTTON_ENTER,  # type key 'a'
                BUTTON_PAGE_PREV,  # Move to 'Go' key
                BUTTON_ENTER,  # Select 'Go' key
                BUTTON_ENTER,  # Confirm to proceed
                BUTTON_ENTER,  # Confirm to add GCM cam entropy
                BUTTON_ENTER,  # Confirm to use fingerprint as ID
                BUTTON_ENTER,  # See QrCode and exit
                BUTTON_ENTER,  # Select 'Return to QR Viewer'
                BUTTON_ENTER,  # See QrCode and exit
                *([BUTTON_PAGE] * 3),  # Move 'Print as QR'
                BUTTON_ENTER,  # Select 'Print as QR'
                BUTTON_ENTER,  # Confirm 'Print as QR thermal/adafruit'
                BUTTON_ENTER,  # See QrCode and exit
                BUTTON_PAGE_PREV,  # Move 'Back to menu'
                BUTTON_ENTER,  # Select 'Back to menu'
                BUTTON_PAGE_PREV,  # Move to 'Back'
                BUTTON_ENTER,  # Select 'Back'
            ],
        ),
        # 3 - 24W print
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                *([BUTTON_PAGE] * 3),  # Move to Encrypted QR code
                BUTTON_ENTER,  # Select Encrypted QR code
                BUTTON_ENTER,  # Select Type key
                BUTTON_ENTER,  # type key 'a'
                BUTTON_PAGE_PREV,  # Move to 'Go' key
                BUTTON_ENTER,  # Select 'Go' key
                BUTTON_ENTER,  # Confirm to proceed
                BUTTON_ENTER,  # Confirm to add GCM cam entropy
                BUTTON_ENTER,  # Confirm to use fingerprint as ID
                BUTTON_ENTER,  # See QrCode and exit
                BUTTON_ENTER,  # Select 'Return to QR Viewer'
                BUTTON_ENTER,  # See QrCode and exit
                *([BUTTON_PAGE] * 3),  # Move 'Print as QR'
                BUTTON_ENTER,  # Select 'Print as QR'
                BUTTON_ENTER,  # Confirm 'Print as QR thermal/adafruit'
                BUTTON_ENTER,  # See QrCode and exit
                BUTTON_PAGE_PREV,  # Move 'Back to menu'
                BUTTON_ENTER,  # Select 'Back to menu'
                BUTTON_PAGE_PREV,  # Move to 'Back'
                BUTTON_ENTER,  # Select 'Back'
            ],
        ),
        # 4 - 12W decline print
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                *([BUTTON_PAGE] * 3),  # Move to Encrypted QR code
                BUTTON_ENTER,  # Select Encrypted QR code
                BUTTON_ENTER,  # Select Type key
                BUTTON_ENTER,  # Type key 'a'
                BUTTON_PAGE_PREV,  # Move to 'Go' key
                BUTTON_ENTER,  # Select 'Go' key
                BUTTON_ENTER,  # Confirm to proceed
                BUTTON_ENTER,  # Confirm to add GCM cam entropy
                BUTTON_ENTER,  # Confirm to use fingerprint as ID
                BUTTON_ENTER,  # See QrCode and exit
                BUTTON_ENTER,  # Select 'Return to QR Viewer'
                BUTTON_ENTER,  # See QrCode and exit
                *([BUTTON_PAGE] * 3),  # Move to 'Print as QR'
                BUTTON_ENTER,  # Select 'Print as QR'
                BUTTON_PAGE_PREV,  # decline print
                BUTTON_ENTER,  # See qrcode and exit
                BUTTON_PAGE_PREV,  # Move to 'Back'
                BUTTON_ENTER,  # Select 'Back'
                BUTTON_PAGE_PREV,  # Move to back
                BUTTON_ENTER,  # Select 'Back'
            ],
        ),
        # 5 - 24W decline print
        (
            Wallet(tdata.SINGLESIG_24_WORD_KEY),
            MockPrinter(),
            [
                BUTTON_ENTER,  # QR Code
                *([BUTTON_PAGE] * 3),  # Move to Encrypted QR code
                BUTTON_ENTER,  # Select Encrypted QR code
                BUTTON_ENTER,  # Select Type key
                BUTTON_ENTER,  # Type key 'a'
                BUTTON_PAGE_PREV,  # Move to 'Go' key
                BUTTON_ENTER,  # Select 'Go' key
                BUTTON_ENTER,  # Confirm to proceed
                BUTTON_ENTER,  # Confirm to add GCM cam entropy
                BUTTON_ENTER,  # Confirm to use fingerprint as ID
                BUTTON_ENTER,  # See QrCode and exit
                BUTTON_ENTER,  # Select 'Return to QR Viewer'
                BUTTON_ENTER,  # See QrCode and exit
                *([BUTTON_PAGE] * 3),  # Move to 'Print as QR'
                BUTTON_ENTER,  # Select 'Print as QR'
                BUTTON_PAGE_PREV,  # decline print
                BUTTON_ENTER,  # See qrcode and exit
                BUTTON_PAGE_PREV,  # Move to 'Back'
                BUTTON_ENTER,  # Select 'Back'
                BUTTON_PAGE_PREV,  # Move to back
                BUTTON_ENTER,  # Select 'Back'
            ],
        ),
    ]

    I_VECTOR = b"OR\xa1\x93l>2q \x9e\x9dd\x05\x9e\xd7\x8e"
    mocker.patch(
        "krux.pages.capture_entropy.CameraEntropy.capture",
        mocker.MagicMock(return_value=I_VECTOR),
    )

    case_count = 0
    for case in cases:
        print(case_count)
        case_count += 1
        ctx = create_ctx(mocker, case[2], case[0], case[1])
        mnemonics = MnemonicsView(ctx)

        mocker.spy(mnemonics, "encrypt_qr_code")
        mnemonics.mnemonic()

        mnemonics.encrypt_qr_code.assert_called_once()
        assert ctx.input.wait_for_button.call_count == len(case[2])


def test_print_mnemonic_other_words(mocker, amigo, tdata):
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.input import BUTTON_PAGE_PREV, BUTTON_ENTER
    from krux.wallet import Wallet

    BTN_SEQ = [
        BUTTON_ENTER,  # WORDS
        BUTTON_ENTER,  # Exit view
        BUTTON_ENTER,  # Print
        BUTTON_PAGE_PREV,  # Move back
        BUTTON_ENTER,  # Exit
    ]

    printer = MockPrinter()

    def custom_create_printer():
        return printer

    ctx = create_ctx(mocker, BTN_SEQ, printer=printer)
    ctx.wallet = Wallet(tdata.SINGLESIG_24_WORD_KEY)

    mocker.patch("krux.printers.create_printer", new=custom_create_printer)
    mnemonics = MnemonicsView(ctx)

    mocker.spy(printer, "print_string")
    mocker.spy(mnemonics, "show_mnemonic")

    mnemonics.other_backup_formats()

    mnemonics.show_mnemonic.assert_called()

    # brush badge sing still venue panther kitchen please help panel bundle excess sign couch stove increase human once effort candy goat top tiny major"
    printer.print_string.assert_has_calls(
        [
            mocker.call("1:brush     13:sign\n"),
            mocker.call("2:badge     14:couch\n"),
            mocker.call("3:sing      15:stove\n"),
            mocker.call("4:still     16:increase\n"),
            mocker.call("5:venue     17:human\n"),
            mocker.call("6:panther   18:once\n"),
            mocker.call("7:kitchen   19:effort\n"),
            mocker.call("8:please    20:candy\n"),
            mocker.call("9:help      21:goat\n"),
            mocker.call("10:panel    22:top\n"),
            mocker.call("11:bundle   23:tiny\n"),
            mocker.call("12:excess   24:major\n"),
        ]
    )

    assert ctx.input.wait_for_button.call_count == len(BTN_SEQ)


def test_display_raw_entropy(mocker, amigo):
    from embit import bip39
    from embit.networks import NETWORKS
    from krux.key import Key, TYPE_SINGLESIG
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.input import BUTTON_ENTER
    from krux.wallet import Wallet

    mnemonic = (
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon "
        "abandon abandon about"
    )
    expected_entropy = " ".join(
        "%02X" % byte for byte in bip39.mnemonic_to_bytes(mnemonic)
    )

    ctx = create_ctx(
        mocker,
        [BUTTON_ENTER],
        Wallet(Key(mnemonic, TYPE_SINGLESIG, NETWORKS["main"])),
    )
    mnemonics = MnemonicsView(ctx)
    mocker.spy(mnemonics, "display_mnemonic")

    mnemonics.display_raw_entropy()

    mnemonics.display_mnemonic.assert_called_once_with(
        expected_entropy,
        title="原始熵",
        suffix="BIP39 熵: 128 位",
    )
    assert ctx.input.wait_for_button.call_count == 1


def test_display_steel_punch_numbers(mocker, amigo):
    from embit.networks import NETWORKS
    from krux.key import Key, TYPE_SINGLESIG
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.input import BUTTON_ENTER
    from krux.wallet import Wallet

    mnemonic = (
        "abandon abandon abandon abandon abandon abandon abandon abandon abandon "
        "abandon abandon about"
    )

    assert MnemonicsView._steel_punch_weights(0) == []
    assert MnemonicsView._steel_punch_weights(2047) == [
        1,
        2,
        4,
        8,
        16,
        32,
        64,
        128,
        256,
        512,
        1024,
    ]

    pages = MnemonicsView._format_steel_punch_pages(mnemonic)
    assert len(pages) == 2
    assert pages[0][:2] == ["01 abandon #0000", "打孔: 无需打孔"]
    assert pages[1][-3:] == ["12 about #0003", "前 6 位: 1 2", "后 5 位: 无"]

    ctx = create_ctx(
        mocker,
        [BUTTON_ENTER, BUTTON_ENTER],
        Wallet(Key(mnemonic, TYPE_SINGLESIG, NETWORKS["main"])),
    )
    mnemonics = MnemonicsView(ctx)

    mnemonics.display_steel_punch_numbers()

    titles = [
        call.args[0]
        for call in ctx.display.draw_hcentered_text.call_args_list
        if call.args
    ]
    drawn_lines = [
        call.args[2]
        for call in ctx.display.draw_string.call_args_list
        if len(call.args) >= 3
    ]
    assert "钢板打孔数字 1/2" in titles
    assert "钢板打孔数字 2/2" in titles
    assert "01 abandon #0000" in drawn_lines
    assert "12 about #0003" in drawn_lines
    assert "前 6 位: 1 2" in drawn_lines
    assert "后 5 位: 无" in drawn_lines
    assert ctx.input.wait_for_button.call_count == 2


def test_print_mnemonic_numbers_decimal(mocker, amigo, tdata):
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.input import BUTTON_PAGE_PREV, BUTTON_ENTER
    from krux.wallet import Wallet

    BTN_SEQ = [
        BUTTON_ENTER,  # DECIMAL
        BUTTON_ENTER,  # Exit view
        BUTTON_ENTER,  # Print
        BUTTON_PAGE_PREV,  # Move back
        BUTTON_ENTER,  # Exit
    ]

    printer = MockPrinter()

    def custom_create_printer():
        return printer

    ctx = create_ctx(mocker, BTN_SEQ, printer=printer)
    ctx.wallet = Wallet(tdata.SINGLESIG_24_WORD_KEY)

    mocker.patch("krux.printers.create_printer", new=custom_create_printer)
    mnemonics = MnemonicsView(ctx)

    mocker.spy(printer, "print_string")
    mocker.spy(mnemonics, "show_mnemonic")

    mnemonics.display_mnemonic_numbers()

    mnemonics.show_mnemonic.assert_called()

    # brush badge sing still venue panther kitchen please help panel bundle excess sign couch stove increase human once effort candy goat top tiny major"
    printer.print_string.assert_has_calls(
        [
            mocker.call("1:233       9:856       17:886\n"),
            mocker.call("2:139       10:1276     18:1236\n"),
            mocker.call("3:1610      11:242      19:565\n"),
            mocker.call("4:1710      12:628      20:266\n"),
            mocker.call("5:1939      13:1602     21:800\n"),
            mocker.call("6:1278      14:391      22:1831\n"),
            mocker.call("7:984       15:1717     23:1811\n"),
            mocker.call("8:1331      16:917      24:1075\n"),
        ]
    )

    assert ctx.input.wait_for_button.call_count == len(BTN_SEQ)


def test_print_mnemonic_numbers_hex(mocker, amigo, tdata):
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.input import BUTTON_PAGE_PREV, BUTTON_PAGE, BUTTON_ENTER
    from krux.wallet import Wallet

    BTN_SEQ = [
        BUTTON_PAGE,  # HEX
        BUTTON_ENTER,  # Confirm
        BUTTON_ENTER,  # Exit view
        BUTTON_ENTER,  # Print prompt
        BUTTON_PAGE,  # Move to OCT
        BUTTON_PAGE,  # Move to < back
        BUTTON_ENTER,  # press < back
    ]

    printer = MockPrinter()

    def custom_create_printer():
        return printer

    ctx = create_ctx(mocker, BTN_SEQ, printer=printer)
    ctx.wallet = Wallet(tdata.SINGLESIG_24_WORD_KEY)

    mocker.patch("krux.printers.create_printer", new=custom_create_printer)
    mnemonics = MnemonicsView(ctx)

    mocker.spy(printer, "print_string")
    mocker.spy(mnemonics, "show_mnemonic")

    mnemonics.display_mnemonic_numbers()

    mnemonics.show_mnemonic.assert_called()

    # brush badge sing still venue panther kitchen please help panel bundle excess sign couch stove increase human once effort candy goat top tiny major"
    printer.print_string.assert_has_calls(
        [
            mocker.call("1:E9        9:358       17:376\n"),
            mocker.call("2:8B        10:4FC      18:4D4\n"),
            mocker.call("3:64A       11:F2       19:235\n"),
            mocker.call("4:6AE       12:274      20:10A\n"),
            mocker.call("5:793       13:642      21:320\n"),
            mocker.call("6:4FE       14:187      22:727\n"),
            mocker.call("7:3D8       15:6B5      23:713\n"),
            mocker.call("8:533       16:395      24:433\n"),
        ]
    )

    assert ctx.input.wait_for_button.call_count == len(BTN_SEQ)


def test_print_mnemonic_numbers_oct(mocker, amigo, tdata):
    from krux.pages.home_pages.mnemonic_backup import MnemonicsView
    from krux.input import BUTTON_PAGE_PREV, BUTTON_PAGE, BUTTON_ENTER
    from krux.wallet import Wallet

    BTN_SEQ = [
        BUTTON_PAGE,  # HEX
        BUTTON_PAGE,  # OCT
        BUTTON_ENTER,  # Confirm
        BUTTON_ENTER,  # Exit view
        BUTTON_ENTER,  # Print prompt
        BUTTON_PAGE,  # Move to < back
        BUTTON_ENTER,  # press < back
    ]

    printer = MockPrinter()

    def custom_create_printer():
        return printer

    ctx = create_ctx(mocker, BTN_SEQ, printer=printer)
    ctx.wallet = Wallet(tdata.SINGLESIG_24_WORD_KEY)

    mocker.patch("krux.printers.create_printer", new=custom_create_printer)
    mnemonics = MnemonicsView(ctx)

    mocker.spy(printer, "print_string")
    mocker.spy(mnemonics, "show_mnemonic")

    mnemonics.display_mnemonic_numbers()

    mnemonics.show_mnemonic.assert_called()

    # brush badge sing still venue panther kitchen please help panel bundle excess sign couch stove increase human once effort candy goat top tiny major"
    printer.print_string.assert_has_calls(
        [
            mocker.call("1:351       9:1530      17:1566\n"),
            mocker.call("2:213       10:2374     18:2324\n"),
            mocker.call("3:3112      11:362      19:1065\n"),
            mocker.call("4:3256      12:1164     20:412\n"),
            mocker.call("5:3623      13:3102     21:1440\n"),
            mocker.call("6:2376      14:607      22:3447\n"),
            mocker.call("7:1730      15:3265     23:3423\n"),
            mocker.call("8:2463      16:1625     24:2063\n"),
        ]
    )

    assert ctx.input.wait_for_button.call_count == len(BTN_SEQ)
