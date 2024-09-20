import pytest
from pydantic import BaseModel
from zform.fields import ObjectField, StringField, IntegerField
from zform.fields.base import FieldBase


class SampleSchema(BaseModel):
    name: str
    age: int


@pytest.fixture
def object_field():
    return ObjectField(
        name="sample", fields=[StringField(name="name"), IntegerField(name="age")]
    )


@pytest.fixture
def schema_object_field():
    return ObjectField(schema=SampleSchema, name="sample")


def test_init_with_fields(object_field):
    assert len(list(object_field)) == 2
    assert isinstance(object_field._fields[0], StringField)
    assert isinstance(object_field._fields[1], IntegerField)


def test_init_with_schema(schema_object_field):
    assert len(list(schema_object_field)) == 2
    assert all(isinstance(field, FieldBase) for field in schema_object_field)


def test_validate_setup():
    with pytest.raises(AssertionError):
        ObjectField().validate_setup()


def test_get_render_context(object_field):
    attrs, context = object_field.get_render_context({})
    assert "fields" in context
    assert len(context["fields"]) == 2


def test_name_formatter(object_field):
    formatted_name = object_field._name_formatter("test")
    assert formatted_name.startswith(object_field.id)
    assert formatted_name.endswith("test")


@pytest.mark.asyncio
async def test_process_form_data(object_field, create_context):
    ctx = create_context({"sample.name": "John", "sample.age": "30"})
    result = await object_field.process_form_data(ctx, body=None)

    assert result.data == {"sample": {"name": "John", "age": 30}}
    assert not result.errors
    assert result.raw_data == {"sample": {"name": "John", "age": "30"}}


@pytest.mark.asyncio
async def test_process_form_data_with_errors(object_field, create_context):
    ctx = create_context({"sample.name": "John ", "sample.age": "not_an_integer"})
    result = await object_field.process_form_data(ctx, body=None)

    assert "name" in result.data["sample"]
    assert result.errors
    assert "age" in result.errors[0]["msg"]


def test_process(object_field):
    data = {"name": "Alice", "age": 25}
    object_field.process(data)

    assert object_field._fields[0]._value == "Alice"
    assert object_field._fields[1]._value == 25


def test_python_type_with_schema(schema_object_field):
    assert schema_object_field.python_type == SampleSchema


def test_python_type_without_schema(object_field):
    assert object_field.python_type is dict
