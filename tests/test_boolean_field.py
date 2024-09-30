from zform.fields.boolean import BooleanField
from pydantic import BaseModel, Field
from zform import FormManager


class TestBooleanField:
    def test_init(self):
        field = BooleanField(name="active")
        assert field.type == "checkbox"
        assert field.python_type is bool

    def test_python_type(self):
        field = BooleanField(name="active")
        assert field.python_type is bool

    def test_process_form_data(self, create_context):
        class TestModel(BaseModel):
            active: bool

        form = FormManager.from_schema(
            TestModel, ctx=create_context({"active": "true"})
        )
        field = form.get_field("active")
        assert field.python_type is bool

        assert form.validate()
        assert form.value.active is True

        form = FormManager.from_schema(
            TestModel, ctx=create_context({"active": "false"})
        )
        field = form.get_field("active")
        assert field.python_type is bool

        assert form.validate()
        assert form.value.active is False

    def test_process_form_data_with_default(self, create_context):
        class TestModel(BaseModel):
            active: bool = True

        form = FormManager.from_schema(TestModel, ctx=create_context({}))
        field = form.get_field("active")
        assert field.python_type is bool

        assert form.validate()
        assert form.value.active is True

    def test_process_form_data_with_default_factory(self, create_context):
        class TestModel(BaseModel):
            active: bool = Field(default_factory=lambda: True)

        form = FormManager.from_schema(TestModel, ctx=create_context({}))
        field = form.get_field("active")
        assert field.python_type is bool

        assert form.validate()
        assert form.value.active is True

    def test_render_html(self):
        field = BooleanField(name="active")
        field.process(True)
        html = str(field())
        assert 'type="checkbox"' in html
        assert 'name="active"' in html
        assert "checked" in html

    def test_render_html_with_help_text(self):
        field = BooleanField(name="active", help_text="Active")
        html = str(field())
        assert 'type="checkbox"' in html
        assert 'name="active"' in html
        assert "checked" not in html
        assert "Active" in html

    def test_render_html_checkbox(self):
        field = BooleanField(name="agree")
        html = str(field())
        assert 'type="checkbox"' in html
        assert 'name="agree"' in html
