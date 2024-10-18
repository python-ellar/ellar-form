from decimal import Decimal
from zform.fields.numbers import IntegerField, FloatField, DecimalField, RangeField
from pydantic import BaseModel
from zform.form import FormManager
from zform import ZFieldInfo


class TestIntegerField:
    def test_init(self):
        field = IntegerField(
            name="age", max=100, min=0, placeholder="Enter a number", step=2
        )
        assert field.type == "number"
        assert field.max == 100
        assert field.min == 0
        assert field.attrs["placeholder"] == "Enter a number"
        assert field.step == 2

    def test_python_type(self):
        field = IntegerField(name="age")
        assert field.python_type is int

    def test_field_in_pydantic_model(self, create_context):
        class TestModel(BaseModel):
            number: int = ZFieldInfo(IntegerField, default=0, le=100, ge=0)

        form = FormManager.from_schema(TestModel, ctx=create_context({"number": 50}))
        assert form.get_field("number").max == 100
        assert form.get_field("number").min == 0
        assert form.validate()

        assert form.raw_data == {"number": 50}
        assert form.value
        assert form.value.number == 50

        form = FormManager.from_schema(TestModel, ctx=create_context({"number": 101}))
        assert not form.validate()
        assert form.errors["number"] == ["Input should be less than or equal to 100"]

    def test_render_html(self):
        field = IntegerField(
            name="age",
            max=100,
            min=0,
            placeholder="Enter a number",
            step=2,
            field_info_args={"annotation": int},
        )
        html = field.widget.render()
        assert 'type="number"' in html
        assert 'name="age"' in html
        assert 'max="100"' in html
        assert 'min="0"' in html
        assert 'placeholder="Enter a number"' in html
        assert 'step="2"' in html


class TestFloatField:
    def test_init(self):
        field = FloatField(name="weight", field_info_args={"annotation": float})
        assert field.type == "number"

    def test_python_type(self):
        field = FloatField(name="weight", field_info_args={"annotation": float})
        assert field.python_type is float

    def test_field_in_pydantic_model(self, create_context):
        class TestModel(BaseModel):
            number: float = ZFieldInfo(FloatField(), default=0.0)

        form = FormManager.from_schema(TestModel, ctx=create_context({"number": 3.14}))
        assert form.validate()
        assert form.raw_data == {"number": 3.14}
        assert form.value
        assert form.value.number == 3.14

    def test_render_html(self):
        field = FloatField(
            name="weight",
            max=100.5,
            min=0.5,
            placeholder="Enter a float",
            step=0.1,
            field_info_args={"annotation": float},
        )
        html = field.widget.render()
        assert 'type="number"' in html
        assert 'name="weight"' in html
        assert 'max="100.5"' in html
        assert 'min="0.5"' in html
        assert 'placeholder="Enter a float"' in html
        assert 'step="0.1"' in html


class TestDecimalField:
    def test_init(self):
        field = DecimalField(
            name="price", max=100, min=0, placeholder="Enter a decimal", step="0.01"
        )
        assert field.type == "number"
        assert field.max == 100
        assert field.min == 0
        assert field.attrs["placeholder"] == "Enter a decimal"
        assert field.step == "0.01"
        assert field.field_info_args["multiple_of"] == "0.01"
        assert field.field_info_args["le"] == 100
        assert field.field_info_args["ge"] == 0
        assert field.field_info_args["alias"] == "price"

    def test_python_type(self):
        field = DecimalField(name="price")
        assert field.python_type is Decimal

    def test_field_in_pydantic_model(self, create_context):
        class TestModel(BaseModel):
            number: Decimal = ZFieldInfo(
                DecimalField(max=100, min=0), default=Decimal("0")
            )

        form = FormManager.from_schema(
            TestModel, ctx=create_context({"number": "50.5"})
        )
        assert form.validate()
        assert form.raw_data == {"number": "50.5"}
        assert form.value
        assert form.value.number == Decimal("50.5")

        form = FormManager.from_schema(
            TestModel, ctx=create_context({"number": "100.1"})
        )
        assert not form.validate()

    def test_render_html(self):
        field = DecimalField(
            name="price", max=100, min=0, placeholder="Enter a decimal", step="0.01"
        )
        html = str(field.widget.render())
        assert 'type="number"' in html
        assert 'name="price"' in html
        assert 'max="100"' in html
        assert 'min="0"' in html
        assert 'placeholder="Enter a decimal"' in html
        assert 'step="0.01"' in html


class TestRangeField:
    def test_init(self):
        field = RangeField(name="volume", max=100, min=0, step=5)
        assert field.type == "range"
        assert field.max == 100
        assert field.min == 0
        assert field.step == 5

        assert field.field_info_args["multiple_of"] == 5
        assert field.field_info_args["le"] == 100
        assert field.field_info_args["ge"] == 0
        assert field.field_info_args["alias"] == "volume"

    def test_init_with_le_gt(self):
        field = RangeField(name="volume", max=100, min=0, step=5)
        assert field.max == 100
        assert field.min == 0
        assert field.step == 5

        assert field.field_info_args["le"] == 100
        assert field.field_info_args["ge"] == 0
        assert field.field_info_args["multiple_of"] == 5
        assert field.field_info_args["alias"] == "volume"

    def test_python_type(self):
        field = RangeField(name="volume")
        assert field.python_type is float

    def test_field_in_pydantic_model(self, create_context):
        class TestModel(BaseModel):
            number: float = ZFieldInfo(
                default=0.0, zform_field=RangeField(max=100, min=0)
            )

        form = FormManager.from_schema(TestModel, ctx=create_context({"number": 50.0}))
        assert form.validate()
        assert form.raw_data == {"number": 50.0}
        assert form.value
        assert form.value.number == 50.0

        form = FormManager.from_schema(TestModel, ctx=create_context({"number": 101.0}))
        assert not form.validate()

    def test_render_html(self):
        field = RangeField(name="volume", max=100, min=0, step=5)
        html = field.widget.render()
        assert 'type="range"' in html
        assert 'name="volume"' in html
        assert 'max="100"' in html
        assert 'min="0"' in html
        assert 'step="5"' in html
