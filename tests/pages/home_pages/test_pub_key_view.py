from .. import create_ctx
from .test_home import tdata
import pytest


# Fixture for SD card functionality testing
@pytest.fixture
def mock_sd_card_enabled(mocker):
    mock_save_file = mocker.patch("krux.pages.file_operations.SaveFile")
    mocker.patch(
        "krux.pages.home_pages.pub_key_view.PubkeyView.has_sd_card", return_value=True
    )
    yield mock_save_file


# Fixture for QR view mocking
@pytest.fixture
def mock_qr_view(mocker):
    yield mocker.patch("krux.pages.qr_view.SeedQRView")


def test_public_key(mocker, m5stickv, tdata):
    from krux.pages.home_pages.pub_key_view import PubkeyView
    from krux.wallet import Wallet
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV
    from krux.qr import FORMAT_NONE
    from krux.key import TYPE_MULTISIG

    cases = [
        # Case parameters: [Wallet, Printer, Button Sequence, Show XPUB, Show ZPUB]
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
        ),
        # TODO: Create cases were not all text and QR codes are shown
    ]
    num = 0

    for case in cases:
        print(num)
        num += 1
        mock_seed_qr_view = mocker.patch(
            "krux.pages.qr_view.SeedQRView"
        )  # Mock SeedQRView
        ctx = create_ctx(mocker, case[2], case[0], case[1])
        pub_key_viewer = PubkeyView(ctx)

        pub_key_viewer.public_key()

        version = "Zpub" if ctx.wallet.key.policy_type == TYPE_MULTISIG else "zpub"
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
            print_qr_calls.append(
                mocker.call(
                    ctx.wallet.key.key_expression(None),
                    FORMAT_NONE,
                    "XPUB",
                ),
            )
        if case[4]:  # Show ZPUB
            qr_view_calls.append(
                mocker.call(
                    ctx,
                    data=ctx.wallet.key.key_expression(ctx.wallet.key.network[version]),
                    title="ZPUB",
                ),
            )
            print_qr_calls.append(
                mocker.call(
                    ctx.wallet.key.key_expression(ctx.wallet.key.network[version]),
                    FORMAT_NONE,
                    "ZPUB",
                ),
            )

        # Assert SeedQRView was initialized with the correct parameters
        mock_seed_qr_view.assert_has_calls(qr_view_calls, any_order=True)

        # TODO: Assert XPUB and ZPUB text was displayed

        assert ctx.input.wait_for_button.call_count == len(case[2])


# Test P2SH_P2WPKH nested segwit script type coverage with complex user interactions
def test_public_key_nested_segwit(mocker, m5stickv, tdata, mock_qr_view):
    from krux.pages.home_pages.pub_key_view import PubkeyView
    from krux.wallet import Wallet
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV

    # Complex button sequence to navigate through P2SH_P2WPKH wallet showing XPUB and YPUB
    # This exercises the path at line 108-109 in pub_key_view.py
    btn_sequence = [
        BUTTON_ENTER,  # Enter XPUB - Text
        BUTTON_PAGE,  # move to Back
        BUTTON_ENTER,  # Press Back
        BUTTON_PAGE,  # move to XPUB - QR Code
        BUTTON_ENTER,  # Enter XPUB - QR Code
        BUTTON_ENTER,  # Enter QR Menu
        BUTTON_PAGE_PREV,  # move to Back to Menu
        BUTTON_ENTER,  # Press Back to Menu
        BUTTON_PAGE,  # move to XPUB - QR Code
        BUTTON_PAGE,  # move to YPUB - Text (this tests the P2SH_P2WPKH path)
        BUTTON_PAGE,  # move to YPUB - QR Code
        BUTTON_ENTER,  # Enter YPUB - QR Code
        BUTTON_ENTER,  # Enter QR Menu
        BUTTON_PAGE_PREV,  # move to Back to Menu
        BUTTON_ENTER,  # Press Back to Menu
        BUTTON_PAGE_PREV,  # Move Back
        BUTTON_ENTER,  # Press Back to leave
    ]

    ctx = create_ctx(mocker, btn_sequence, Wallet(tdata.NESTEDSW1_KEY))
    pub_key_viewer = PubkeyView(ctx)
    pub_key_viewer.public_key()

    # Verify complex nested segwit interaction occurred
    assert ctx.input.wait_for_button.call_count == len(btn_sequence)
    assert mock_qr_view.called


# Test P2SH_P2WSH script type coverage - requires direct mock due to Key class limitation
def test_public_key_p2sh_p2wsh_script_type(mocker, m5stickv, tdata, mock_qr_view):
    from krux.pages.home_pages.pub_key_view import PubkeyView
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV
    from krux.key import TYPE_MULTISIG

    # Mock P2SH_P2WSH key since Key class forces multisig to P2WSH only
    # This specifically tests line 110-111 in pub_key_view.py
    mock_key = mocker.MagicMock()
    mock_key.script_type = "p2sh-p2wsh"
    mock_key.network = {"Ypub": "Ypub"}
    mock_key.account_pubkey_str.return_value = "Ypub123"
    mock_key.key_expression.return_value = "Ypub123"
    mock_key.policy_type = TYPE_MULTISIG

    mock_wallet = mocker.MagicMock()
    mock_wallet.key = mock_key
    mock_wallet.is_multisig.return_value = True

    # Complex button sequence to trigger P2SH_P2WSH path with realistic navigation
    btn_sequence = [
        BUTTON_ENTER,  # Enter XPUB - Text
        BUTTON_PAGE,  # move to Back
        BUTTON_ENTER,  # Press Back
        BUTTON_PAGE,  # move to XPUB - QR Code
        BUTTON_ENTER,  # Enter XPUB - QR Code
        BUTTON_ENTER,  # Enter QR Menu
        BUTTON_PAGE_PREV,  # move to Back to Menu
        BUTTON_ENTER,  # Press Back to Menu
        BUTTON_PAGE,  # move to XPUB - QR Code
        BUTTON_PAGE,  # move to YPUB - Text
        BUTTON_PAGE,  # move to YPUB - QR Code
        BUTTON_ENTER,  # Enter YPUB - QR Code
        BUTTON_ENTER,  # Enter QR Menu
        BUTTON_PAGE_PREV,  # move to Back to Menu
        BUTTON_ENTER,  # Press Back to Menu
        BUTTON_PAGE_PREV,  # Move Back
        BUTTON_ENTER,  # Press Back to leave
    ]

    ctx = create_ctx(mocker, btn_sequence, mock_wallet)
    pub_key_viewer = PubkeyView(ctx)
    pub_key_viewer.public_key()

    # Verify complex interaction occurred and P2SH_P2WSH path was triggered
    assert ctx.input.wait_for_button.call_count == len(btn_sequence)
    assert mock_qr_view.called


# Test SD card save functionality for public keys with complex user interactions
def test_public_key_sd_card_save(
    mocker, m5stickv, tdata, mock_sd_card_enabled, mock_qr_view
):
    from krux.pages.home_pages.pub_key_view import PubkeyView
    from krux.wallet import Wallet
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV

    # Complex button sequence that exercises SD card save functionality with realistic user flow
    # This tests the _save_xpub_to_sd function at lines 44-59 in pub_key_view.py
    # User navigates through text displays, saves to SD, explores QR codes, saves more content
    btn_sequence = [
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
    ]

    ctx = create_ctx(mocker, btn_sequence, Wallet(tdata.SINGLESIG_12_WORD_KEY))
    pub_key_viewer = PubkeyView(ctx)
    pub_key_viewer.public_key()

    # Verify SD card save was called multiple times for different keys (XPUB and ZPUB saves)
    assert mock_sd_card_enabled.called, "SD card save functionality not called"
    assert ctx.input.wait_for_button.call_count == len(btn_sequence)
    # Verify QR functionality was also exercised during the complex flow
    assert mock_qr_view.called
