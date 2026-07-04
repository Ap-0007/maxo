from unittest.mock import AsyncMock

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.input.text import TextInput

from .conftest import create_message_no_body, create_text_message, dialog_protocol


async def test_text_input_basic(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    text_input: TextInput[str] = TextInput(id="text", on_success=on_success)

    message = create_text_message("Hello World")
    result = await text_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    on_success.assert_called_once()
    assert text_input.get_value(mock_manager) == "Hello World"


async def test_text_input_with_type_factory(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    text_input: TextInput[int] = TextInput(
        id="number",
        type_factory=int,
        on_success=on_success,
    )

    message = create_text_message("42")
    result = await text_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    on_success.assert_called_once()
    # Check that the callback received the converted value
    call_args = on_success.call_args
    assert call_args[0][3] == 42  # data parameter
    assert text_input.get_value(mock_manager) == 42


async def test_text_input_type_factory_error(mock_manager: DialogManager) -> None:
    on_error = AsyncMock()
    text_input: TextInput[int] = TextInput(
        id="number",
        type_factory=int,
        on_error=on_error,
    )

    message = create_text_message("not a number")
    result = await text_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    on_error.assert_called_once()
    # Check that error was passed
    call_args = on_error.call_args
    assert isinstance(call_args[0][3], ValueError)


async def test_text_input_empty_message(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    text_input: TextInput[str] = TextInput(id="text", on_success=on_success)

    message = create_text_message("")
    result = await text_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is False
    on_success.assert_not_called()


async def test_text_input_no_body(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    text_input: TextInput[str] = TextInput(id="text", on_success=on_success)

    message = create_message_no_body()
    result = await text_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is False
    on_success.assert_not_called()


async def test_text_input_with_filter(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    filter_func = AsyncMock(return_value=True)
    text_input: TextInput[str] = TextInput(
        id="text",
        on_success=on_success,
        filter=filter_func,
    )

    message = create_text_message("Test")
    result = await text_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    filter_func.assert_called_once()
    on_success.assert_called_once()


async def test_text_input_filter_rejects(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    filter_func = AsyncMock(return_value=False)
    text_input: TextInput[str] = TextInput(
        id="text",
        on_success=on_success,
        filter=filter_func,
    )

    message = create_text_message("Test")
    result = await text_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is False
    filter_func.assert_called_once()
    on_success.assert_not_called()


async def test_text_input_get_value_none(mock_manager: DialogManager) -> None:
    text_input: TextInput[str] = TextInput(id="text")

    value = text_input.get_value(mock_manager)

    assert value is None


async def test_text_input_managed(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    text_input: TextInput[str] = TextInput(id="text", on_success=on_success)

    message = create_text_message("Managed Test")
    await text_input.process_message(message, dialog_protocol(), mock_manager)

    managed = text_input.managed(mock_manager)
    assert managed.get_value() == "Managed Test"


async def test_text_input_float_factory(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    text_input: TextInput[float] = TextInput(
        id="decimal",
        type_factory=float,
        on_success=on_success,
    )

    message = create_text_message("3.14")
    result = await text_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    on_success.assert_called_once()
    call_args = on_success.call_args
    assert call_args[0][3] == 3.14
    assert text_input.get_value(mock_manager) == 3.14


async def test_text_input_custom_type_factory(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()

    def uppercase_factory(text: str) -> str:
        return text.upper()

    text_input: TextInput[str] = TextInput(
        id="upper",
        type_factory=uppercase_factory,
        on_success=on_success,
    )

    message = create_text_message("hello")
    result = await text_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    on_success.assert_called_once()
    call_args = on_success.call_args
    assert call_args[0][3] == "HELLO"
    assert text_input.get_value(mock_manager) == "HELLO"
