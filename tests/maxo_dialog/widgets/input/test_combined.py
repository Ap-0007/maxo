from unittest.mock import AsyncMock

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.input.combined import CombinedInput
from maxo.dialogs.widgets.input.text import TextInput

from .conftest import create_text_message


async def test_combined_input_first_accepts(mock_manager: DialogManager) -> None:
    on_success1 = AsyncMock()
    on_success2 = AsyncMock()
    input1 = TextInput(id="text1", on_success=on_success1)
    input2 = TextInput(id="text2", on_success=on_success2)
    combined = CombinedInput(input1, input2)

    message = create_text_message("Test")
    result = await combined.process_message(message, None, mock_manager)

    assert result is True
    on_success1.assert_called_once()
    on_success2.assert_not_called()


async def test_combined_input_second_accepts(mock_manager: DialogManager) -> None:
    on_success1 = AsyncMock()
    on_success2 = AsyncMock()
    # First input rejects empty messages
    input1 = TextInput(
        id="text1",
        on_success=on_success1,
        filter=AsyncMock(return_value=False),
    )
    input2 = TextInput(id="text2", on_success=on_success2)
    combined = CombinedInput(input1, input2)

    message = create_text_message("Test")
    result = await combined.process_message(message, None, mock_manager)

    assert result is True
    on_success1.assert_not_called()
    on_success2.assert_called_once()


async def test_combined_input_all_reject(mock_manager: DialogManager) -> None:
    on_success1 = AsyncMock()
    on_success2 = AsyncMock()
    filter1 = AsyncMock(return_value=False)
    filter2 = AsyncMock(return_value=False)
    input1 = TextInput(id="text1", on_success=on_success1, filter=filter1)
    input2 = TextInput(id="text2", on_success=on_success2, filter=filter2)
    combined = CombinedInput(input1, input2)

    message = create_text_message("Test")
    result = await combined.process_message(message, None, mock_manager)

    assert result is False
    on_success1.assert_not_called()
    on_success2.assert_not_called()


async def test_combined_input_with_filter_accepts(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    input1 = TextInput(id="text1", on_success=on_success)
    filter_func = AsyncMock(return_value=True)
    combined = CombinedInput(input1, filter=filter_func)

    message = create_text_message("Test")
    result = await combined.process_message(message, None, mock_manager)

    assert result is True
    filter_func.assert_called_once()
    on_success.assert_called_once()


async def test_combined_input_with_filter_rejects(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    input1 = TextInput(id="text1", on_success=on_success)
    filter_func = AsyncMock(return_value=False)
    combined = CombinedInput(input1, filter=filter_func)

    message = create_text_message("Test")
    result = await combined.process_message(message, None, mock_manager)

    assert result is False
    filter_func.assert_called_once()
    on_success.assert_not_called()


async def test_combined_input_no_inputs(mock_manager: DialogManager) -> None:
    combined = CombinedInput()

    message = create_text_message("Test")
    result = await combined.process_message(message, None, mock_manager)

    assert result is False


async def test_combined_input_three_inputs(mock_manager: DialogManager) -> None:
    on_success1 = AsyncMock()
    on_success2 = AsyncMock()
    on_success3 = AsyncMock()
    input1 = TextInput(
        id="text1",
        on_success=on_success1,
        filter=AsyncMock(return_value=False),
    )
    input2 = TextInput(
        id="text2",
        on_success=on_success2,
        filter=AsyncMock(return_value=False),
    )
    input3 = TextInput(id="text3", on_success=on_success3)
    combined = CombinedInput(input1, input2, input3)

    message = create_text_message("Test")
    result = await combined.process_message(message, None, mock_manager)

    assert result is True
    on_success1.assert_not_called()
    on_success2.assert_not_called()
    on_success3.assert_called_once()


async def test_combined_input_empty_message(mock_manager: DialogManager) -> None:
    on_success1 = AsyncMock()
    on_success2 = AsyncMock()
    input1 = TextInput(id="text1", on_success=on_success1)
    input2 = TextInput(id="text2", on_success=on_success2)
    combined = CombinedInput(input1, input2)

    message = create_text_message("")
    result = await combined.process_message(message, None, mock_manager)

    # Both TextInput widgets reject empty messages
    assert result is False
    on_success1.assert_not_called()
    on_success2.assert_not_called()
