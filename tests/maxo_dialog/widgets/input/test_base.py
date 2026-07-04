from unittest.mock import AsyncMock

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.input.base import ContentTypeFilter, MessageInput
from maxo.enums import AttachmentType

from .conftest import (
    create_photo_message,
    create_text_message,
    dialog_protocol,
    empty_ctx,
    setup_mock_manager,
)


async def test_message_input_basic(mock_manager: DialogManager) -> None:
    setup_mock_manager(mock_manager)
    handler = AsyncMock()
    message_input = MessageInput(func=handler, id="input")

    message = create_text_message("Test")
    result = await message_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    handler.assert_called_once_with(message, message_input, mock_manager)


async def test_message_input_with_text_content_type(
    mock_manager: DialogManager,
) -> None:
    setup_mock_manager(mock_manager)
    handler = AsyncMock()
    message_input = MessageInput(
        func=handler,
        content_types=AttachmentType.TEXT,
        id="input",
    )

    message = create_text_message("Test")
    result = await message_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    handler.assert_called_once()


async def test_message_input_with_text_content_type_rejects_photo(
    mock_manager: DialogManager,
) -> None:
    message = create_photo_message()
    setup_mock_manager(mock_manager, message)
    handler = AsyncMock()
    message_input = MessageInput(
        func=handler,
        content_types=AttachmentType.TEXT,
        id="input",
    )

    result = await message_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is False
    handler.assert_not_called()


async def test_message_input_with_photo_content_type(
    mock_manager: DialogManager,
) -> None:
    message = create_photo_message()
    setup_mock_manager(mock_manager, message)
    handler = AsyncMock()
    message_input = MessageInput(
        func=handler,
        content_types=AttachmentType.PHOTO,
        id="input",
    )

    result = await message_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    handler.assert_called_once()


async def test_message_input_with_multiple_content_types(
    mock_manager: DialogManager,
) -> None:
    setup_mock_manager(mock_manager)
    handler = AsyncMock()
    message_input = MessageInput(
        func=handler,
        content_types=[AttachmentType.TEXT, AttachmentType.PHOTO],
        id="input",
    )

    text_message = create_text_message("Test")
    result = await message_input.process_message(
        text_message,
        dialog_protocol(),
        mock_manager,
    )
    assert result is True

    photo_message = create_photo_message()
    result = await message_input.process_message(
        photo_message,
        dialog_protocol(),
        mock_manager,
    )
    assert result is True

    assert handler.call_count == 2


async def test_message_input_with_custom_filter(mock_manager: DialogManager) -> None:
    setup_mock_manager(mock_manager)
    handler = AsyncMock()
    filter_func = AsyncMock(return_value=True)
    message_input = MessageInput(func=handler, filter=filter_func, id="input")

    message = create_text_message("Test")
    result = await message_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    filter_func.assert_called_once()
    handler.assert_called_once()


async def test_message_input_with_custom_filter_rejects(
    mock_manager: DialogManager,
) -> None:
    setup_mock_manager(mock_manager)
    handler = AsyncMock()
    filter_func = AsyncMock(return_value=False)
    message_input = MessageInput(func=handler, filter=filter_func, id="input")

    message = create_text_message("Test")
    result = await message_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is False
    filter_func.assert_called_once()
    handler.assert_not_called()


async def test_message_input_with_both_filters(mock_manager: DialogManager) -> None:
    setup_mock_manager(mock_manager)
    handler = AsyncMock()
    filter_func = AsyncMock(return_value=True)
    message_input = MessageInput(
        func=handler,
        content_types=AttachmentType.TEXT,
        filter=filter_func,
        id="input",
    )

    message = create_text_message("Test")
    result = await message_input.process_message(
        message,
        dialog_protocol(),
        mock_manager,
    )

    assert result is True
    filter_func.assert_called_once()
    handler.assert_called_once()


async def test_content_type_filter_text() -> None:
    content_filter = ContentTypeFilter([AttachmentType.TEXT])
    message = create_text_message("Test")

    result = await content_filter(message, empty_ctx())

    assert result is True


async def test_content_type_filter_photo() -> None:
    content_filter = ContentTypeFilter([AttachmentType.PHOTO])
    message = create_photo_message()

    result = await content_filter(message, empty_ctx())

    assert result is True


async def test_content_type_filter_rejects_wrong_type() -> None:
    content_filter = ContentTypeFilter([AttachmentType.TEXT])
    message = create_photo_message()

    result = await content_filter(message, empty_ctx())

    assert result is False


async def test_content_type_filter_multiple_types() -> None:
    content_filter = ContentTypeFilter([AttachmentType.TEXT, AttachmentType.PHOTO])

    text_message = create_text_message("Test")
    assert await content_filter(text_message, empty_ctx()) is True

    photo_message = create_photo_message()
    assert await content_filter(photo_message, empty_ctx()) is True
