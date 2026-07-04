from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import RequestContact, RequestLocation
from maxo.dialogs.widgets.text import Const, Format
from maxo.types import RequestContactButton, RequestGeoLocationButton


async def test_request_contact_basic(mock_manager: DialogManager) -> None:
    """Test basic RequestContact widget rendering."""
    request_contact = RequestContact(text=Const("Share Contact"))

    keyboard = await request_contact.render_keyboard(data={}, manager=mock_manager)

    button = keyboard[0][0]
    assert isinstance(button, RequestContactButton)
    assert button.text == "Share Contact"


async def test_request_contact_with_data(mock_manager: DialogManager) -> None:
    """Test RequestContact with dynamic data."""
    request_contact = RequestContact(text=Format("{label}"))

    keyboard = await request_contact.render_keyboard(
        data={"label": "Share Your Contact"},
        manager=mock_manager,
    )

    button = keyboard[0][0]
    assert isinstance(button, RequestContactButton)
    assert button.text == "Share Your Contact"


async def test_request_location_basic(mock_manager: DialogManager) -> None:
    """Test basic RequestLocation widget rendering without quick parameter."""
    request_location = RequestLocation(text=Const("Share Location"))

    keyboard = await request_location.render_keyboard(data={}, manager=mock_manager)

    button = keyboard[0][0]
    assert isinstance(button, RequestGeoLocationButton)
    assert button.text == "Share Location"


async def test_request_location_with_quick(mock_manager: DialogManager) -> None:
    """Test RequestLocation widget with quick=True."""
    request_location = RequestLocation(text=Const("Quick Location"), quick=True)

    keyboard = await request_location.render_keyboard(data={}, manager=mock_manager)

    button = keyboard[0][0]
    assert isinstance(button, RequestGeoLocationButton)
    assert button.text == "Quick Location"
    assert button.quick is True


async def test_request_location_with_quick_false(mock_manager: DialogManager) -> None:
    """Test RequestLocation widget with quick=False."""
    request_location = RequestLocation(text=Const("Precise Location"), quick=False)

    keyboard = await request_location.render_keyboard(data={}, manager=mock_manager)

    button = keyboard[0][0]
    assert isinstance(button, RequestGeoLocationButton)
    assert button.text == "Precise Location"
    assert button.quick is False


async def test_request_location_with_data(mock_manager: DialogManager) -> None:
    """Test RequestLocation with dynamic data."""
    request_location = RequestLocation(text=Format("{label}"), quick=True)

    keyboard = await request_location.render_keyboard(
        data={"label": "Share Your Location"},
        manager=mock_manager,
    )

    button = keyboard[0][0]
    assert isinstance(button, RequestGeoLocationButton)
    assert button.text == "Share Your Location"
    assert button.quick is True
