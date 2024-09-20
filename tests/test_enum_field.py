import typing as t
import enum
from pydantic import BaseModel

from zform import FormManager, ZFieldInfo
from zform.fields import FieldList
from zform.fields.enum import EnumField


class Color(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class NumberEnum(enum.IntEnum):
    ONE = 1
    TWO = 2
    THREE = 3


def test_enum_field_initialization():
    field = EnumField(name="color", enum=Color, field_info_args={"default": Color.RED})
    assert field.enum == Color
    assert field._choices == [("red", "RED"), ("green", "GREEN"), ("blue", "BLUE")]
    assert field._coerce_type is str


def test_enum_field_with_int_enum():
    field = EnumField(enum=NumberEnum, name="number", field_info_args={})
    assert field.enum == NumberEnum
    assert field._choices == [(1, "ONE"), (2, "TWO"), (3, "THREE")]
    assert field._coerce_type is int


def test_enum_field_default_value():
    field = EnumField(enum=Color, name="color", field_info_args={"default": Color.RED})
    assert field.default == "red"


def test_enum_field_python_type():
    field = EnumField(enum=Color, name="color")
    assert field.python_type == Color

    field_multiple = EnumField(enum=Color, name="colors", multiple=True)
    assert field_multiple.python_type == t.List[Color]


def test_enum_field_process():
    field = EnumField(enum=Color, name="color")
    field.process("green")
    assert field.value == Color.GREEN
    assert field.data == "green"


def test_enum_field_render():
    field = EnumField(enum=Color, name="color")
    rendered = field.render()
    assert '<select class="" id="color" name="color" required>' in rendered
    assert 'name="color"' in rendered
    assert "<option value='red'>RED</option>" in rendered
    assert "<option value='green'>GREEN</option>" in rendered
    assert "<option value='blue'>BLUE</option>" in rendered


def test_enum_field_validation():
    field = EnumField(enum=Color, name="color")
    field.process("invalid", suppress_error=False)
    assert field.errors
    assert "Input should be 'red', 'green' or 'blue'" in field.errors[0]["msg"]

    field.process("green", suppress_error=False)
    assert not field.errors
    assert field.value == Color.GREEN


def test_enum_field_multiple():
    field = EnumField(enum=Color, name="color", multiple=True)
    field.process(["red", "green"], suppress_error=False)
    assert field.value == [Color.RED, Color.GREEN]
    assert field.data == ["red", "green"]


def test_enum_field_render_multiple():
    field = EnumField(
        enum=Color,
        name="color",
        multiple=True,
        field_info_args={"default": [Color.RED, Color.GREEN]},
    )
    field.load()
    rendered = field.render()
    assert '<select class="" id="color" multiple name="color">' in rendered
    assert 'name="color"' in rendered
    assert "<option value='red' selected>RED</option>" in rendered
    assert "<option value='green' selected>GREEN</option>" in rendered
    assert "<option value='blue'>BLUE</option>" in rendered


def test_enum_field_validation_multiple():
    field = EnumField(enum=Color, name="color", multiple=True)
    field.process(["red", "invalid"], suppress_error=False)
    assert field.errors
    assert "Input should be 'red', 'green' or 'blue'" in field.errors[0]["msg"]

    field.process(["red", "green"], suppress_error=False)
    assert not field.errors
    assert field.value == [Color.RED, Color.GREEN]


def test_enum_with_pydantic_model(create_context):
    class User(BaseModel):
        color: Color

    form_manager = FormManager.from_schema(User, ctx=create_context({"color": "green"}))
    assert isinstance(form_manager.get_field("color"), EnumField)
    assert form_manager.validate()

    assert form_manager.value.color == Color.GREEN


def test_enum_with_pydantic_model_default(create_context):
    class User(BaseModel):
        color: Color = Color.RED

    form_manager = FormManager.from_schema(User, ctx=create_context({}))
    assert isinstance(form_manager.get_field("color"), EnumField)
    assert form_manager.validate()

    assert form_manager.value.color == Color.RED


def test_enum_with_pydantic_model_multiple(create_context):
    class User(BaseModel):
        color: t.List[Color]

    form_manager = FormManager.from_schema(
        User, ctx=create_context({"color.0": "red", "color.1": "green"})
    )
    assert isinstance(form_manager.get_field("color"), FieldList)
    assert form_manager.validate()

    assert form_manager.value.color == [Color.RED, Color.GREEN]


def test_enum_with_pydantic_model_multiple_default_as_field_list(create_context):
    class User(BaseModel):
        color: t.List[Color] = [Color.RED, Color.GREEN]

    form_manager = FormManager.from_schema(User, ctx=create_context({}))
    assert isinstance(form_manager.get_field("color"), FieldList)
    assert form_manager.validate()

    assert form_manager.value.color == [Color.RED, Color.GREEN]


def test_enum_with_pydantic_model_multiple_default(create_context):
    class User(BaseModel):
        color: t.List[Color] = ZFieldInfo(EnumField(), default=[Color.RED, Color.GREEN])

    form_manager = FormManager.from_schema(User, ctx=create_context({}))

    assert isinstance(form_manager.get_field("color"), EnumField)
    assert form_manager.validate()

    assert form_manager.value.color == [Color.RED, Color.GREEN]
