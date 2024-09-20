import pytest
import typing as t

from zform import FormManager
from zform.fields.flist import FieldList
from zform.fields.string import StringField

from pydantic import BaseModel


@pytest.fixture
def field_list():
    return FieldList(
        StringField(), name="xys", field_info_args={"annotation": t.List[str]}
    )


def test_field_list_initialization(field_list):
    assert isinstance(field_list._base_field, StringField)
    assert field_list.name == "xys"
    assert len(field_list._items) == 0


def test_add_item(field_list):
    new_field = field_list.add_item()
    assert len(field_list._items) == 1
    assert isinstance(new_field, StringField)
    assert new_field.name == "xys.0"


def test_clear_items(field_list):
    field_list.add_item()
    field_list.add_item()
    field_list.clear()
    assert len(field_list._items) == 0


@pytest.mark.asyncio
async def test_process_form_data(field_list, create_context):
    ctx = create_context({"xys.0": "value1", "xys.1": "value2"})
    result = await field_list.process_form_data(ctx, None)

    assert result.data["xys"] == ["value1", "value2"]
    assert result.errors == []
    assert result.raw_data["xys"] == {"0": "value1", "1": "value2"}


def test_extra_indices(field_list):
    form_data = {
        "xys.0": "value0",
        "xys.1": "value1",
        "xys.3": "value3",
        "other_field": "other_value",
    }
    indices = field_list._extra_indices(form_data)
    assert indices == [0, 1, 3]


def test_get_new_field_at(field_list):
    new_field = field_list._get_new_field_at("xys.2")
    assert isinstance(new_field, StringField)
    assert new_field.name == "xys.2"


def test_field_list_iteration(field_list):
    field_list.add_item()
    field_list.add_item()
    assert len(list(field_list._items)) == 2
    for item in field_list._items:
        assert isinstance(item, StringField)


def test_field_list_indexing(field_list):
    field_list.add_item()
    field_list.add_item()
    assert isinstance(field_list._items[0], StringField)
    assert field_list._items[0].name == "xys.0"
    assert field_list._items[1].name == "xys.1"


def test_field_list_len(field_list):
    assert len(field_list._items) == 0
    field_list.add_item()
    field_list.add_item()
    assert len(field_list._items) == 2


def test_process_with_list_data(field_list):
    data = ["value1", "value2", "value3"]
    field_list.process(data)

    assert len(field_list._items) == 3
    for i, item in enumerate(field_list):
        assert isinstance(item, StringField)
        assert item.value == data[i]


def test_process_with_single_item_list(field_list):
    data = ["single_value"]
    field_list.process(data)

    assert len(field_list._items) == 1


def test_process_with_non_list_data(field_list):
    data = "non_list_value"
    field_list.process(data)

    assert len(field_list._items) == 0


def test_process_with_empty_list(field_list):
    data = []
    field_list.process(data)

    assert len(field_list._items) == 0


def test_process_with_suppress_error_false(field_list):
    data = ["value1", "value2"]
    field_list.process(data, suppress_error=False)

    assert len(field_list._items) == 2
    for i, item in enumerate(field_list._items):
        assert isinstance(item, StringField)
        assert item.value == data[i]


def test_field_list_with_pydantic_model(create_context):
    class TestModel(BaseModel):
        xys: t.List[str]

    form = FormManager.from_schema(
        TestModel, ctx=create_context({"xys.0": "value1", "xys.1": "value2"})
    )
    field_list: FieldList = form.get_field("xys")

    assert isinstance(field_list.base_field, StringField)
    assert field_list.name == "xys"
    assert len(list(field_list)) == 1

    assert form.validate()
    assert form.value.xys == ["value1", "value2"]

    form = FormManager.from_schema(TestModel, ctx=create_context({}))
    assert form.validate() is False
    assert form.errors["xys"]
