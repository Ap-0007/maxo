from typing import Any, cast

from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.widgets.kbd import Button, Column, Group, Row, Url
from maxo.dialogs.widgets.text import Case, Const, Format, Jinja, Multi
from maxo.types import LinkButton


class DummyManager:
    def __init__(
        self,
        preview: bool = False,
        middleware_data: dict[str, Any] | None = None,
    ) -> None:
        self._preview = preview
        self.middleware_data = middleware_data or {}
        self._page = 0

    def is_preview(self) -> bool:
        return self._preview


class DummyTemplate:
    def __init__(self, template: str) -> None:
        self.template = template

    async def render_async(self, data: dict[str, Any]) -> str:
        return self.template.format_map(data)

    def render(self, data: dict[str, Any]) -> str:
        return self.template.format_map(data)


class DummyEnv:
    is_async = False

    def get_template(self, template: str) -> DummyTemplate:
        return DummyTemplate(template)


async def test_const_and_multi_render() -> None:
    manager = dialog_manager()
    text = Const("Hello") + " " + Const("world")
    multi = Multi(Const("Hello"), Const("world"), sep=" ")

    assert await text.render_text({}, manager) == "Hello world"
    assert await multi.render_text({}, manager) == "Hello world"


async def test_format_render_and_preview() -> None:
    manager = dialog_manager()
    preview_manager = dialog_manager(preview=True)

    assert await Format("Hello, {name}!").render_text({"name": "Alice"}, manager) == (
        "Hello, Alice!"
    )
    assert await Format("Hello, {name:>5}!").render_text(
        {"name": "A"},
        preview_manager,
    ) == ("Hello,     A!")


async def test_case_render_and_find() -> None:
    case = Case(
        {
            0: Const("zero"),
            1: Const("one"),
        },
        selector=lambda data, _widget, _manager: data["value"] % 2,
    )

    assert await case.render_text({"value": 2}, dialog_manager()) == "zero"
    assert await case.render_text({"value": 3}, dialog_manager()) == "one"
    assert case.find("missing") is None


async def test_jinja_render_with_direct_environment() -> None:
    manager = dialog_manager(middleware_data={"DialogsJinjaEnvironment": DummyEnv()})
    widget = Jinja("Hello, {name}!")

    assert await widget.render_text({"name": "Alice"}, manager) == "Hello, Alice!"


async def test_keyboard_row_column_group_url() -> None:
    manager = dialog_manager()
    row = Row(Button(Const("1"), id="a"), Button(Const("2"), id="b"))
    column = Column(Button(Const("1"), id="a"), Button(Const("2"), id="b"))
    group = Group(Button(Const("1"), id="a"), Button(Const("2"), id="b"), width=2)
    url = Url(Const("Open"), Const("https://example.com"))

    row_keyboard = await row.render_keyboard({}, manager)
    column_keyboard = await column.render_keyboard({}, manager)
    group_keyboard = await group.render_keyboard({}, manager)
    url_keyboard = await url.render_keyboard({}, manager)

    assert len(row_keyboard) == 1
    assert len(column_keyboard) == 2
    assert len(group_keyboard) == 1
    assert isinstance(url_keyboard[0][0], LinkButton)
    assert url_keyboard[0][0].url == "https://example.com"


def dialog_manager(
    *,
    preview: bool = False,
    middleware_data: dict[str, Any] | None = None,
) -> DialogManager:
    # cast нужен для легковесного объекта с минимальным набором полей протокола.
    return cast(
        DialogManager,
        DummyManager(preview=preview, middleware_data=middleware_data),
    )
