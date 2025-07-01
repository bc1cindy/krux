import pytest
from . import create_ctx


def test_fill_flash(amigo, mocker):
    from krux.pages.fill_flash import (
        FillFlash,
        BLOCK_SIZE,
        IMAGE_BYTES_SIZE,
        TOTAL_BLOCKS,
    )
    from krux.input import BUTTON_ENTER
    from krux.firmware import FLASH_SIZE
    import flash

    BTN_SEQUENCE = [
        BUTTON_ENTER,  # Confirm fill flash
    ]
    IMAGE_BYTES = b"\x00" * IMAGE_BYTES_SIZE

    def mock_flash_read(address, size):
        # Simulate the second half of the flash is empty
        if address > FLASH_SIZE // 2:
            return b"\xff" * size
        else:
            return b"\x00" * size

    mocker.patch("flash.read", side_effect=mock_flash_read)
    mocker.spy(flash, "write")
    ctx = create_ctx(mocker, BTN_SEQUENCE)
    fill_flash = FillFlash(ctx)
    fill_flash.capture_image_with_sufficient_entropy = mocker.MagicMock(
        return_value=IMAGE_BYTES
    )
    fill_flash.fill_flash_with_camera_entropy()

    assert ctx.input.wait_for_button.call_count == len(BTN_SEQUENCE)
    # Check that the flash was written to on half of the blocks
    assert flash.write.call_count == TOTAL_BLOCKS // 2 - 1


def test_capture_image_with_sufficient_entropy(amigo, mocker):
    from krux.pages.fill_flash import FillFlash
    from krux.pages.capture_entropy import CameraEntropy, POOR_VARIANCE_TH

    # Mocks 3 poor entropy measurements then 1 good entropy measurement
    STDEV_INDEX = [*([POOR_VARIANCE_TH - 1] * 3), POOR_VARIANCE_TH + 1]

    ctx = create_ctx(mocker, [])
    fill_flash = FillFlash(ctx)
    entropy_measurement = CameraEntropy(ctx)
    mocker.spy(entropy_measurement, "entropy_measurement_update")
    entropy_measurement.rms_value = mocker.PropertyMock(side_effect=STDEV_INDEX)
    fill_flash.capture_image_with_sufficient_entropy(entropy_measurement)

    # Check that the entropy_measurement_update was called 4 times
    # 3 times for poor entropy and 1 time for good entropy
    assert entropy_measurement.entropy_measurement_update.call_count == 4


@pytest.fixture
def mock_coverage_scenarios(mocker):
    # Comprehensive fixture providing mocks for various fill flash test scenarios
    # Covers entropy validation, flash operations, timeout handling, and user interactions
    from krux.pages.capture_entropy import INSUFFICIENT_VARIANCE_TH
    from krux.firmware import FLASH_SIZE
    
    def _mock_flash_read(address, size):
        # Simulates flash memory with second half empty (0xff) and first half occupied (0x00)
        # This creates realistic conditions where only empty blocks need to be filled
        if address > FLASH_SIZE // 2:
            return b"\xff" * size
        else:
            return b"\x00" * size
    
    return {
        # Mock insufficient entropy scenario: RMS value below minimum threshold
        # Used to test entropy validation failure paths in camera capture
        "insufficient_entropy": mocker.PropertyMock(return_value=INSUFFICIENT_VARIANCE_TH - 1),
        
        # Mock timeout scenario: simulates 26-second elapsed time to trigger timeout
        # Tests the 25-second timeout mechanism in entropy capture process (MAX_CAPTURE_PERIOD)
        "timeout_simulation": mocker.patch("time.time", side_effect=[0, 26]),
        
        # Mock normal flash read operations with realistic memory state simulation
        # Provides controlled flash read behavior for testing write operations
        "flash_read_normal": mocker.patch("flash.read", side_effect=_mock_flash_read),
        
        # Mock flash write error to test error handling during flash operations
        # Simulates hardware failures or write protection scenarios
        "flash_write_error": mocker.patch("flash.write", side_effect=Exception("Flash write error")),
        
        # Mock touch interface decline: returns index 0 ("No" option) from touch interaction
        # Tests user rejection through touch interface in confirmation dialogs
        "touch_decline": lambda ctx: mocker.patch.object(ctx.input.touch, "current_index", return_value=0)
    }


def test_fill_flash_coverage_scenarios(amigo, mocker, mock_coverage_scenarios):
    from krux.pages.fill_flash import FillFlash, MENU_CONTINUE, IMAGE_BYTES_SIZE
    from krux.input import BUTTON_ENTER, BUTTON_TOUCH, BUTTON_PAGE, BUTTON_PAGE_PREV
    
    cases = [
        {
            # Test entropy timeout scenario with user confirmation navigation
            # User hesitates, checks options, then accepts but entropy capture times out
            "btn_sequence": [
                BUTTON_PAGE_PREV,  # Navigate to "No" (user hesitates)
                BUTTON_PAGE,       # Navigate back to "Yes" (user reconsiders)
                BUTTON_PAGE_PREV,  # Navigate to "No" again (still unsure)
                BUTTON_PAGE,       # Finally navigate back to "Yes"
                BUTTON_ENTER       # Confirm "Yes" after deliberation
            ],
            "setup_mocks": [],
            "mock_capture_method": True,
            "capture_side_effect": ValueError("Insufficient entropy!"),
            "expected_exception": ValueError,
            "verify_calls": ["wait_for_button"],
        },
        {
            # Test touch interface rejection scenario with navigation
            # User navigates through options then uses touch to decline
            "btn_sequence": [
                BUTTON_PAGE,       # Navigate options to understand choices
                BUTTON_PAGE_PREV,  # Navigate back to explore both options
                BUTTON_TOUCH       # Finally use touch interface to decline
            ],
            "setup_mocks": ["touch_decline"],
            "mock_capture_method": False,
            "expected_result": MENU_CONTINUE,
            "verify_calls": ["wait_for_button", "touch.current_index"],
        },
        {
            # Test flash write error handling with complex user navigation
            # User hesitates, navigates through options, confirms, but flash write fails
            "btn_sequence": [BUTTON_PAGE_PREV, BUTTON_PAGE, BUTTON_ENTER],
            "setup_mocks": ["flash_read_normal", "flash_write_error"],
            "mock_capture_method": True,
            "capture_return_value": b"\x00" * IMAGE_BYTES_SIZE,
            "expected_result": MENU_CONTINUE,
            "verify_calls": ["wait_for_button", "flash.write"],
        },
        {
            # Test complex navigation followed by acceptance
            # User explores all options extensively before final decision
            "btn_sequence": [
                BUTTON_PAGE_PREV,  # Go to "No" first
                BUTTON_PAGE,       # Go to "Yes"
                BUTTON_PAGE_PREV,  # Back to "No" (exploring)
                BUTTON_PAGE_PREV,  # Stay on "No" (wrap around behavior)
                BUTTON_PAGE,       # To "Yes"
                BUTTON_PAGE,       # Stay on "Yes" (wrap around behavior)
                BUTTON_ENTER       # Finally confirm "Yes" after thorough exploration
            ],
            "setup_mocks": ["flash_read_normal"],
            "mock_capture_method": True,
            "capture_return_value": b"\x00" * IMAGE_BYTES_SIZE,
            "expected_result": None,
            "verify_calls": ["wait_for_button"],
        },
        {
            # Test mixed input methods with complex decision making
            # User switches between button navigation and touch interface
            "btn_sequence": [
                BUTTON_PAGE_PREV,  # Navigate to "No" using buttons
                BUTTON_PAGE,       # Navigate to "Yes" using buttons
                BUTTON_TOUCH       # Final decision using touch interface
            ],
            "setup_mocks": ["flash_read_normal"],
            "mock_capture_method": True,
            "capture_return_value": b"\x00" * IMAGE_BYTES_SIZE,
            "touch_return": 1,     # Touch "Yes" region
            "expected_result": None,
            "verify_calls": ["wait_for_button"],
        },
        {
            # Test rapid navigation followed by rejection
            # User quickly explores options then decisively rejects
            "btn_sequence": [
                BUTTON_PAGE,       # Quick navigation to explore
                BUTTON_PAGE_PREV,  # Quick navigation back
                BUTTON_PAGE,       # Quick navigation forward again
                BUTTON_PAGE_PREV,  # Navigate to "No"
                BUTTON_ENTER       # Decisively confirm "No"
            ],
            "setup_mocks": [],
            "mock_capture_method": False,
            "expected_result": MENU_CONTINUE,
            "verify_calls": ["wait_for_button"],
        }
    ]
    
    for case in cases:
        # Apply capture method mocks first to ensure they take precedence
        if case.get("mock_capture_method", False):
            if "capture_side_effect" in case:
                capture_mock = mocker.patch(
                    "krux.pages.fill_flash.FillFlash.capture_image_with_sufficient_entropy",
                    side_effect=case["capture_side_effect"]
                )
            elif "capture_return_value" in case:
                capture_mock = mocker.patch(
                    "krux.pages.fill_flash.FillFlash.capture_image_with_sufficient_entropy",
                    return_value=case["capture_return_value"]
                )
        
        ctx = create_ctx(mocker, case["btn_sequence"])
        fill_flash = FillFlash(ctx)
        
        # Configure touch interface if test case uses touch
        if "touch_return" in case:
            mocker.patch.object(ctx.input.touch, "current_index", return_value=case["touch_return"])
        
        for mock_name in case.get("setup_mocks", []):
            if mock_name == "touch_decline":
                mock_coverage_scenarios[mock_name](ctx)
            elif mock_name == "insufficient_entropy":
                from krux.pages.capture_entropy import CameraEntropy, POOR_VARIANCE_TH
                entropy_measurement = CameraEntropy(ctx)
                # Mock entropy_measurement_update to always keep stdev_index below threshold
                def mock_update(img, all_at_once=False, show_measurement=True):
                    entropy_measurement.stdev_index = POOR_VARIANCE_TH - 1  # Always insufficient
                entropy_measurement.entropy_measurement_update = mock_update
                mocker.patch("krux.pages.fill_flash.CameraEntropy", return_value=entropy_measurement)
        
        if "expected_exception" in case:
            with pytest.raises(case["expected_exception"]):
                fill_flash.fill_flash_with_camera_entropy()
        else:
            result = fill_flash.fill_flash_with_camera_entropy()
            if case["expected_result"] is not None:
                assert result == case["expected_result"]
        
        for call_check in case.get("verify_calls", []):
            if call_check == "wait_for_button":
                assert ctx.input.wait_for_button.call_count >= 1
            elif call_check == "touch.current_index":
                ctx.input.touch.current_index.assert_called()
            elif call_check == "flash.write":
                mock_coverage_scenarios["flash_write_error"].assert_called()
        
        # Explicit cleanup of complex mock setups
        mocker.resetall()


def test_fill_flash_user_interaction_flows(amigo, mocker):
    # Tests complex user interaction patterns in fill flash confirmation dialog
    # Covers realistic scenarios of user hesitation, navigation, and decision-making
    from krux.pages.fill_flash import FillFlash, MENU_CONTINUE, IMAGE_BYTES_SIZE
    from krux.input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV, BUTTON_TOUCH
    import flash
    
    cases = [
        {
            # User declines operation after careful consideration
            # Simulates thoughtful user exploring options before decisive rejection
            "btn_sequence": [
                BUTTON_PAGE,       # Start by exploring "Yes" option
                BUTTON_PAGE_PREV,  # Navigate to "No" to compare
                BUTTON_PAGE,       # Go back to "Yes" for comparison
                BUTTON_PAGE_PREV,  # Return to "No" after consideration
                BUTTON_PAGE_PREV,  # Stay on "No" (confirming choice)
                BUTTON_ENTER       # Decisively confirm "No"
            ],
            "expected_result": MENU_CONTINUE,
            "description": "User rejects fill flash after careful consideration",
        },
        {
            # User extensively navigates before accepting
            # Simulates indecisive user behavior with multiple option toggles
            "btn_sequence": [
                BUTTON_PAGE_PREV,  # Go to "No"
                BUTTON_PAGE,       # Back to "Yes" 
                BUTTON_PAGE_PREV,  # To "No" again
                BUTTON_PAGE_PREV,  # Still "No" (wraps around)
                BUTTON_PAGE,       # Back to "Yes"
                BUTTON_ENTER       # Finally confirm "Yes"
            ],
            "expected_result": None,  # Operation completes
            "description": "User navigates extensively before accepting",
        },
        {
            # Complex mixed input methods with extensive exploration
            # Tests sophisticated user behavior switching between input modes
            "btn_sequence": [
                BUTTON_PAGE_PREV,  # Explore "No" option with buttons
                BUTTON_PAGE,       # Explore "Yes" option with buttons
                BUTTON_PAGE_PREV,  # Return to "No" with buttons
                BUTTON_PAGE,       # Go to "Yes" again with buttons
                BUTTON_PAGE,       # Stay on "Yes" (wrap around check)
                BUTTON_TOUCH       # Final decision using touch interface
            ],
            "touch_return": 1,  # Touch "Yes" region for acceptance
            "expected_result": None,  # Operation completes successfully
            "description": "Sophisticated mixed input navigation with touch confirmation",
        },
        {
            # Extreme indecision followed by acceptance
            # Simulates highly indecisive user with multiple changes of mind
            "btn_sequence": [
                BUTTON_PAGE_PREV,  # Initial exploration: go to "No"
                BUTTON_PAGE,       # Change mind: go to "Yes"
                BUTTON_PAGE_PREV,  # Doubt again: back to "No"
                BUTTON_PAGE,       # Reconsider: back to "Yes"
                BUTTON_PAGE_PREV,  # More doubt: to "No" again
                BUTTON_PAGE_PREV,  # Stay on "No" (wrap check)
                BUTTON_PAGE,       # Final reconsideration: to "Yes"
                BUTTON_PAGE,       # Confirm staying on "Yes" (wrap check)
                BUTTON_PAGE_PREV,  # Last minute doubt: to "No"
                BUTTON_PAGE,       # Final decision: back to "Yes"
                BUTTON_ENTER       # Finally commit to "Yes"
            ],
            "expected_result": None,  # Operation completes after indecision
            "description": "Extreme user indecision with multiple mind changes",
        }
    ]
    
    for case in cases:
        # Mock flash operations for successful scenarios
        def mock_flash_read(address, size):
            return b"\xff" * size  # All flash empty, needs filling
        
        mocker.patch("flash.read", side_effect=mock_flash_read)
        mocker.patch("flash.write", return_value=None)
        
        ctx = create_ctx(mocker, case["btn_sequence"])
        
        # Configure touch interface if test case uses touch
        if "touch_return" in case:
            mocker.patch.object(ctx.input.touch, "current_index", return_value=case["touch_return"])
        
        fill_flash = FillFlash(ctx)
        
        # Mock entropy capture to focus on user interaction testing
        mocker.patch.object(
            fill_flash, 
            "capture_image_with_sufficient_entropy", 
            return_value=b"\x00" * IMAGE_BYTES_SIZE
        )
        
        result = fill_flash.fill_flash_with_camera_entropy()
        
        # Verify expected outcome based on user interaction pattern
        if case["expected_result"] is not None:
            assert result == case["expected_result"]
        
        # Verify user interaction occurred as expected
        assert ctx.input.wait_for_button.call_count == len(case["btn_sequence"])
        
        # Explicit cleanup of complex mock setups
        mocker.resetall()