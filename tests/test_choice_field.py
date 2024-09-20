import typing as t
import pytest
from zform.fields.select import ChoiceField
from zform.form import FormManager
from zform import ZFieldInfo
from pydantic import BaseModel


class TestChoiceField:
    def test_init(self):
        choices = [("a", "Option A"), ("b", "Option B")]
        field = ChoiceField(name="test", choices=choices)
        assert field._choices == choices
        assert not field.multiple

    def test_init_with_string_choices(self):
        choices = ["a", "b"]
        field = ChoiceField(name="test", choices=choices)
        assert field._choices == [("a", "a"), ("b", "b")]

    def test_multiple_by_annotation(self):
        field = ChoiceField(
            name="test", choices=["a", "b"], field_info_args={"annotation": t.List[str]}
        )
        assert field.multiple

    def test_init_with_multiple(self):
        field = ChoiceField(name="test", choices=["a", "b"], multiple=True)
        assert field.multiple

    def test_choice_values(self):
        choices = [("a", "Option A"), ("b", "Option B")]
        field = ChoiceField(name="test", choices=choices)
        assert field._choice_values == ["a", "b"]

    def test_python_type(self):
        field = ChoiceField(name="test", choices=["a", "b"])
        assert field.python_type is str

        field_multiple = ChoiceField(name="test", choices=["a", "b"], multiple=True)
        assert field_multiple.python_type == t.List[str]

    def test_validate_setup(self):
        with pytest.raises(AssertionError, match="Must provide 'choice'"):
            ChoiceField(name="test").validate_setup()

        field = ChoiceField(name="test", choices=["a", "b"])
        field.validate_setup()  # Should not raise an exception

    def test_get_render_context(self):
        choices = [("a", "Option A"), ("b", "Option B")]
        field = ChoiceField(name="test", choices=choices)
        field.data = "a"
        attrs, context = field.get_render_context({})

        assert context["choices"] == choices
        assert context["is_selected"]("a")
        assert not context["is_selected"]("b")

    def test_field_after_validation_single(self):
        choices = [("a", "Option A"), ("b", "Option B")]
        field = ChoiceField(name="test", choices=choices)

        assert field.field_after_validation("a", None) == "a"

        with pytest.raises(ValueError, match="Input should be in"):
            field.field_after_validation("c", None)

    def test_field_after_validation_multiple(self):
        choices = [("a", "Option A"), ("b", "Option B")]
        field = ChoiceField(name="test", choices=choices, multiple=True)

        assert field.field_after_validation(["a", "b"], None) == ["a", "b"]

        with pytest.raises(ValueError, match="Input should be in"):
            field.field_after_validation(["a", "c"], None)

        with pytest.raises(ValueError, match="Expected a list of values"):
            field.field_after_validation("a", None)

    def test_field_in_pydantic_model(self, create_context):
        class TestModel(BaseModel):
            choice: str = ZFieldInfo(
                default="a", zform_field=ChoiceField(choices=["a", "b"])
            )
            multi_choice: t.List[str] = ZFieldInfo(
                default_factory=list, zform_field=ChoiceField(choices=["x", "y", "z"])
            )

        form = FormManager.from_schema(
            TestModel, ctx=create_context({"choice": "b", "multi_choice": ["x", "z"]})
        )
        assert form.validate()
        assert form.raw_data == {"choice": "b", "multi_choice": ["x", "z"]}

        assert form.value
        assert form.value.choice == "b"
        assert form.value.multi_choice == ["x", "z"]

        form = FormManager.from_schema(
            TestModel, ctx=create_context({"choice": "c", "multi_choice": ["x", "w"]})
        )
        assert not form.validate()
        assert form.errors["choice"] == ["Value error, Input should be in ['a', 'b']"]
        assert form.errors["multi_choice"] == [
            "Value error, Input should be in ['x', 'y', 'z']"
        ]
