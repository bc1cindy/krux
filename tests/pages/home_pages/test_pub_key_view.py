from .. import create_ctx
from .test_home import tdata
import pytest


@pytest.fixture
def mock_save_file(mocker):
    mock_save_file = mocker.patch("krux.pages.file_operations.SaveFile.save_file")
    mocker.patch(
        "krux.pages.home_pages.pub_key_view.PubkeyView.has_sd_card", return_value=True
    )
    return mock_save_file


@pytest.fixture
def mock_seed_qr_view(mocker):
    mock_seed_qr_view = mocker.patch("krux.pages.qr_view.SeedQRView")
    return mock_seed_qr_view


def test_public_key(mocker, m5stickv, tdata, mock_seed_qr_view):
    from krux.pages.home_pages.pub_key_view import PubkeyView
    from krux.wallet import Wallet
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV
    from krux.qr import FORMAT_NONE
    from krux.key import TYPE_MULTISIG

    cases = [
        # Case parameters: [Wallet, Printer, Button Sequence, Show XPUB, Show ZPUB, Show YPUB]
        # 0 - Singlesig - Show all text and QR codes
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            None,
            [
                BUTTON_ENTER,  # Enter XPUB - Text
                BUTTON_PAGE,  # move to Back
                BUTTON_ENTER,  # Press Back
                BUTTON_PAGE,  # move to XPUB - QR Code
                BUTTON_ENTER,  # Enter XPUB - QR Code
                BUTTON_ENTER,  # Enter QR Menu
                BUTTON_PAGE_PREV,  # move to Back to Menu
                BUTTON_ENTER,  # Press Back to Menu
                BUTTON_PAGE,  # move to XPUB - QR Code
                BUTTON_PAGE,  # move to ZPUB - Text
                BUTTON_PAGE,  # move to ZPUB - QR Code
                BUTTON_ENTER,  # Enter ZPUB - QR Code
                BUTTON_ENTER,  # Enter QR Menu
                BUTTON_PAGE_PREV,  # move to Back to Menu
                BUTTON_ENTER,  # Press Back to Menu
                BUTTON_PAGE_PREV,  # Move Back
                BUTTON_ENTER,  # Press Back to leave
            ],
            True,
            True,
            False,
        ),
        # 1 - Multisig - Show all text and QR codes
        (
            Wallet(tdata.MULTISIG_12_WORD_KEY),
            None,
            [
                BUTTON_ENTER,  # Enter XPUB - Text
                BUTTON_PAGE,  # move to Back
                BUTTON_ENTER,  # Press Back
                BUTTON_PAGE,  # move to XPUB - QR Code
                BUTTON_ENTER,  # Enter XPUB - QR Code
                BUTTON_ENTER,  # Enter QR Menu
                BUTTON_PAGE_PREV,  # move to Back to Menu
                BUTTON_ENTER,  # Press Back to Menu
                BUTTON_PAGE,  # move to XPUB - QR Code
                BUTTON_PAGE,  # move to ZPUB - Text
                BUTTON_PAGE,  # move to ZPUB - QR Code
                BUTTON_ENTER,  # Enter ZPUB - QR Code
                BUTTON_ENTER,  # Enter QR Menu
                BUTTON_PAGE_PREV,  # move to Back to Menu
                BUTTON_ENTER,  # Press Back to Menu
                BUTTON_PAGE_PREV,  # Move Back
                BUTTON_ENTER,  # Press Back to leave
            ],
            True,
            True,
            False,
        ),
        # 2 - Singlesig Nested Segwit - Show all text and QR codes
        (
            Wallet(tdata.NESTEDSW1_KEY),
            None,
            [
                BUTTON_ENTER,  # Enter XPUB - Text
                BUTTON_PAGE,  # move to Back
                BUTTON_ENTER,  # Press Back
                BUTTON_PAGE,  # move to XPUB - QR Code
                BUTTON_ENTER,  # Enter XPUB - QR Code
                BUTTON_ENTER,  # exit the qrcode and enter in QR Menu
                BUTTON_PAGE_PREV,  # move to Back to Menu
                BUTTON_ENTER,  # Press Back to Menu
                *([BUTTON_PAGE] * 2),  # move to YPUB - text
                BUTTON_ENTER,  # Enter YPUB - text
                BUTTON_PAGE,  # move to Back
                BUTTON_ENTER,  # press Back
                *([BUTTON_PAGE] * 3),  # move to YPUB - QR Code
                BUTTON_ENTER,  # Enter YPUB - QR code
                BUTTON_ENTER,  # exit the qrcode and enter in QR Menu
                BUTTON_PAGE_PREV,  # move to Back to Menu
                BUTTON_ENTER,  # Press Back to Menu
                BUTTON_PAGE_PREV,  # Move Back
                BUTTON_ENTER,  # Press Back to leave
            ],
            False,
            False,
            True,
        ),
        # TODO: 3 - Multisig Nested Segwit - YPUB but no print
    ]
    num = 0

    for case in cases:
        print(num)
        num += 1
        ctx = create_ctx(mocker, case[2], case[0], case[1])
        pub_key_viewer = PubkeyView(ctx)

        pub_key_viewer.public_key()
        qr_view_calls = []
        print_qr_calls = []

        if case[3]:  # Show XPUB
            qr_view_calls.append(
                mocker.call(
                    ctx,
                    data=ctx.wallet.key.key_expression(None),
                    title="XPUB",
                ),
            )
            if case[1]:  # If printer is available
                print_qr_calls.append(
                    mocker.call(
                        ctx.wallet.key.key_expression(None),
                        FORMAT_NONE,
                        "XPUB",
                    ),
                )

        if case[4]:  # Show ZPUB
            version = "Zpub" if ctx.wallet.key.policy_type == TYPE_MULTISIG else "zpub"
            qr_view_calls.append(
                mocker.call(
                    ctx,
                    data=ctx.wallet.key.key_expression(ctx.wallet.key.network[version]),
                    title="ZPUB",
                ),
            )
            if case[1]:  # If printer is available
                print_qr_calls.append(
                    mocker.call(
                        ctx.wallet.key.key_expression(ctx.wallet.key.network[version]),
                        FORMAT_NONE,
                        "ZPUB",
                    ),
                )

        if case[5]:  # Show YPUB
            version = "Ypub" if ctx.wallet.key.policy_type == TYPE_MULTISIG else "ypub"
            qr_view_calls.append(
                mocker.call(
                    ctx,
                    data=ctx.wallet.key.key_expression(ctx.wallet.key.network[version]),
                    title="YPUB",
                ),
            )
            if case[1]:  # If printer is available
                print_qr_calls.append(
                    mocker.call(
                        ctx.wallet.key.key_expression(ctx.wallet.key.network[version]),
                        FORMAT_NONE,
                        "YPUB",
                    ),
                )

        # actual
        print(mock_seed_qr_view.call_args_list)

        # expected
        print(qr_view_calls)
        # Assert SeedQRView was initialized with the correct parameters
        mock_seed_qr_view.assert_has_calls(qr_view_calls, any_order=True)

        # Assert print_qr_view was called with the correct parameters
        ctx.printer.print_qr.assert_has_calls(print_qr_calls, any_order=True)

        # TODO: Assert XPUB and ZPUB text was displayed
        assert ctx.input.wait_for_button.call_count == len(case[2])


def test_public_key_sd_card_save(
    mocker, m5stickv, tdata, mock_save_file, mock_seed_qr_view
):
    from krux.pages.home_pages.pub_key_view import PubkeyView
    from krux.wallet import Wallet
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV

    cases = [
        # Case parameters: [Wallet, Print, Button Sequence, xpub]
        # 0 - Singlesig - Save XPUB and ZPUB to SD card
        (
            Wallet(tdata.SINGLESIG_12_WORD_KEY),
            None,
            [
                BUTTON_ENTER,  # Enter XPUB - Text
                BUTTON_ENTER,  # Enter Save to SD (first save operation - tests line 66-72)
                BUTTON_PAGE,  # move to Back
                BUTTON_ENTER,  # Press Back
                BUTTON_PAGE,  # move to XPUB - QR Code
                BUTTON_ENTER,  # Enter XPUB - QR Code
                BUTTON_ENTER,  # Enter QR Menu
                BUTTON_PAGE_PREV,  # move to Back to Menu
                BUTTON_ENTER,  # Press Back to Menu
                BUTTON_PAGE,  # move to XPUB - QR Code
                BUTTON_PAGE,  # move to ZPUB - Text
                BUTTON_ENTER,  # Enter ZPUB - Text
                BUTTON_ENTER,  # Enter Save to SD (second save operation)
                BUTTON_PAGE,  # move to Back
                BUTTON_ENTER,  # Press Back
                BUTTON_PAGE,  # move to ZPUB - QR Code
                BUTTON_ENTER,  # Enter ZPUB - QR Code
                BUTTON_ENTER,  # Enter QR Menu
                BUTTON_PAGE_PREV,  # move to Back to Menu
                BUTTON_ENTER,  # Press Back to Menu
                BUTTON_PAGE_PREV,  # Move Back
                BUTTON_ENTER,  # Press Back to leave
            ],
            True,  # Show XPUB
            True,  # Show ZPUB
        ),
    ]

    num = 0
    for case in cases:
        print(num)
        num += 1
        ctx = create_ctx(mocker, case[2], case[0], case[1])
        pub_key_viewer = PubkeyView(ctx)

        pub_key_viewer.public_key()
        sd_card_save_calls = []

        # TODO set a dynamic way to verify calls
        # and add more cases
        if case[3]:
            sd_card_save_calls.append(
                mocker.call(
                    "[55f8fc5d/84h/0h/0h]xpub6DPMTPxGMqdtzMwpqT1dDQaVdyaEppEm2qYSaJ7ANsuES7HkNzrXJst1Ed8D7NAnijUdgSDUFgph1oj5LKKAD5gyxWNhNP2AuDqaKYqzphA",
                    "XPUB",
                    "XPUB",
                    "XPUB:",
                    ".pub",
                    save_as_binary=False,
                )
            )

        if case[4]:
            sd_card_save_calls.append(
                mocker.call(
                    "[55f8fc5d/84h/0h/0h]zpub6s3t4jJ6fCirgxL4WAasdamVyus8i4Dks4at95tw8tezYJvCtKBeZ1CHH33P7BUdY1iFBPQbB1XnnNxCmi9BoZ4BhBmYYCf9Sfxs6jY8Ycw",
                    "ZPUB",
                    "ZPUB",
                    "ZPUB:",
                    ".pub",
                    save_as_binary=False,
                )
            )

        # Verify SD card save was called multiple times for different keys (XPUB and ZPUB saves)
        mock_save_file.assert_has_calls(sd_card_save_calls, any_order=False)
        assert ctx.input.wait_for_button.call_count == len(case[2])

        # TODO Verify QR functionality was also exercised during the complex flow
        assert mock_seed_qr_view.called
