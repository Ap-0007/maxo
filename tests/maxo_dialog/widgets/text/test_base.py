from magic_filter import F

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.text import Const, Multi


async def test_add_const(mock_manager: DialogManager) -> None:
    text = Const("Hello, ") + Const("world!")
    res = await text.render_text({}, mock_manager)
    assert res == "Hello, world!"


async def test_add_add(mock_manager: DialogManager) -> None:
    text = Const("Hello, ") + Const("world") + Const("!")
    res = await text.render_text({}, mock_manager)
    assert res == "Hello, world!"


async def test_add_str(mock_manager: DialogManager) -> None:
    text = Const("Hello, ") + "world!"
    res = await text.render_text({}, mock_manager)
    assert res == "Hello, world!"


async def test_add_str_rght(mock_manager: DialogManager) -> None:
    text = "Hello, " + Const("world!")
    res = await text.render_text({}, mock_manager)
    assert res == "Hello, world!"


async def test_or(mock_manager: DialogManager) -> None:
    text = Const("A") | Const("B")
    res = await text.render_text({}, mock_manager)
    assert res == "A"


async def test_ror_str(mock_manager: DialogManager) -> None:
    text = "A" | Const("B")
    res = await text.render_text({}, mock_manager)
    assert res == "A"


async def test_or_condition(mock_manager: DialogManager) -> None:
    text = Const("A", when=F["a"]) | Const("B", when=F["b"]) | Const("C")
    res = await text.render_text({"a": True}, mock_manager)
    assert res == "A"
    res = await text.render_text({"b": True}, mock_manager)
    assert res == "B"
    res = await text.render_text({}, mock_manager)
    assert res == "C"


async def test_text_hidden_by_when_returns_empty(mock_manager: DialogManager) -> None:
    text = Const("hidden", when=F["show"])

    assert await text.render_text({}, mock_manager) == ""


async def test_multi_iadd_and_add_reduce_nesting(mock_manager: DialogManager) -> None:
    text = Multi(Const("A"), sep="")

    text += "B"
    text = "0" + text + Const("C")

    assert await text.render_text({}, mock_manager) == "0ABC"


async def test_or_iadd_and_reverse_or(mock_manager: DialogManager) -> None:
    text = Const("", when=F["missing"]) | Const("")

    text |= "fallback"

    assert await text.render_text({}, mock_manager) == "fallback"
    assert await ("prefix" | text).render_text({}, mock_manager) == "prefix"
