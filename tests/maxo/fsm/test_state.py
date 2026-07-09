import pytest

from maxo.fsm.state import State, StatesGroup, any_state, default_state


class TestState:
    def test_empty_state(self) -> None:
        state = State()

        assert state._state is None
        assert state._group_name is None
        assert state._group is None
        assert state.state is None
        assert str(state) == "<State ''>"

        with pytest.raises(RuntimeError, match="This state is not in any group"):
            _ = state.group

    def test_any_state(self) -> None:
        state = State("*")

        assert state.state == "*"
        assert state == "*"
        assert any_state.state == "*"
        assert str(state) == "<State '*'>"

    def test_default_state(self) -> None:
        assert default_state.state is None
        assert default_state == State()

    def test_alone_state_uses_at_group_placeholder(self) -> None:
        state = State("test")

        assert state.state == "@:test"
        assert state == "@:test"
        assert state != "test"
        assert str(state) == "<State '@:test'>"

    def test_alone_state_with_group_name(self) -> None:
        state = State("test", group_name="Test")

        assert state.state == "Test:test"
        assert state == "Test:test"

    def test_state_hash_uses_resolved_state_name(self) -> None:
        assert hash(State("test", group_name="Group")) == hash("Group:test")

    def test_state_parent_must_be_states_group(self) -> None:
        class NotStatesGroup:
            pass

        with pytest.raises(TypeError, match="Group must be subclass of StatesGroup"):
            State().set_parent(NotStatesGroup)  # type: ignore[arg-type]


class TestStatesGroup:
    def test_empty_group(self) -> None:
        class MyGroup(StatesGroup):
            pass

        assert MyGroup.__states__ == ()
        assert MyGroup.__state_names__ == ()
        assert MyGroup.__all_childs__ == ()
        assert MyGroup.__all_states__ == ()
        assert MyGroup.__all_states_names__ == ()
        assert MyGroup.__parent__ is None
        assert MyGroup.__full_group_name__ == "MyGroup"
        assert str(MyGroup) == "<StatesGroup 'MyGroup'>"
        assert str(MyGroup()) == "StatesGroup MyGroup"

    def test_group_with_states(self) -> None:
        class MyGroup(StatesGroup):
            state1 = State()
            state2 = State("custom")

        assert MyGroup.__states__ == (MyGroup.state1, MyGroup.state2)
        assert MyGroup.__state_names__ == ("MyGroup:state1", "MyGroup:custom")
        assert MyGroup.__all_states__ == (MyGroup.state1, MyGroup.state2)
        assert MyGroup.__all_states_names__ == (
            "MyGroup:state1",
            "MyGroup:custom",
        )
        assert MyGroup.state1.state == "MyGroup:state1"
        assert MyGroup.state1.group is MyGroup
        assert MyGroup.state2.state == "MyGroup:custom"
        assert MyGroup.state2.group is MyGroup

    def test_nested_group(self) -> None:
        class MyGroup(StatesGroup):
            state1 = State()

            class Nested(StatesGroup):
                state1 = State()

        assert MyGroup.__states__ == (MyGroup.state1,)
        assert MyGroup.__all_childs__ == (MyGroup.Nested,)
        assert MyGroup.__all_states__ == (MyGroup.state1, MyGroup.Nested.state1)
        assert MyGroup.Nested.__parent__ is MyGroup
        assert MyGroup.__full_group_name__ == "MyGroup"
        assert MyGroup.Nested.__full_group_name__ == "MyGroup.Nested"
        assert MyGroup.Nested.state1.state == "MyGroup.Nested:state1"
        assert MyGroup.Nested.state1.group is MyGroup.Nested
        assert MyGroup.Nested.state1 in MyGroup
        assert MyGroup.Nested.state1 in MyGroup.Nested
        assert MyGroup.state1 in MyGroup
        assert MyGroup.state1 not in MyGroup.Nested
        assert MyGroup.Nested in MyGroup
        assert "MyGroup.Nested:state1" in MyGroup
        assert "unknown" not in MyGroup
        assert 42 not in MyGroup
        assert MyGroup.Nested.get_root() is MyGroup

    def test_iterates_over_all_states(self) -> None:
        class Group(StatesGroup):
            x = State()
            y = State()

        assert tuple(Group) == (Group.x, Group.y)
