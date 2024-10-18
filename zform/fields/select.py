import typing as t
from functools import cached_property
from pydantic import ValidationInfo

from ellar.reflect import fail_silently
from .string import StringField
from ellar.common.compatible import AttributeDict
from ellar.pydantic.utils import annotation_is_sequence
from .widget import FieldWidget


class ChoiceFieldWidget(FieldWidget):
    """
    Choice field widget for rendering a select dropdown.
    """

    field: "ChoiceField"

    # language=html
    template = """
        {% if help_text %}
            <div>
              <select {{attrs}}>
                    {% for value, name in choices %}
                        <option value='{{value}}' {%if is_selected(value) %} selected {%endif%}>{{name}}</option>
                    {% endfor %}
              </select>
              <small>{{help_text}}</small>
            </div>
        {% else %}
            <select {{attrs}}>
                {% for value, name in choices %}
                    {%if is_selected(value) %}
                        <option value='{{value}}' selected>{{name}}</option>
                    {% else %}
                        <option value='{{value}}'>{{name}}</option>
                    {%endif%}
                {% endfor %}
            </select>
        {% endif %}
    """

    def get_html_attrs(self, **extra_attrs: t.Any) -> t.Dict:
        attrs = super().get_html_attrs(**extra_attrs)
        attrs.update(multiple=self.field.multiple)
        attrs.pop("value", None)
        return attrs

    def get_render_context(self) -> t.Dict:
        ctx = super().get_render_context()
        data = self.field.data
        # ensure data is in coerce type
        data = [
            fail_silently(self.field._coerce_type, i) or i
            for i in (data if isinstance(data, (list, tuple)) else [data])
        ]
        ctx.update(
            dict(
                is_selected=lambda v: (self.field._coerce_type(v) in data or [])
                if v is not None
                else False,
                choices=self.field._choices,
                multiple=self.field.multiple,
            )
        )

        return ctx


class ChoiceField(StringField):
    _coerce_type: t.Callable = str
    widgetType: t.Type[FieldWidget] = ChoiceFieldWidget

    def __init__(
        self,
        choices: t.Union[t.Sequence[str], t.Sequence[t.Tuple[t.Any, str]], None] = None,
        choices_loader: t.Optional[
            t.Callable[[], t.Union[t.Sequence[str], t.Sequence[t.Tuple[t.Any, str]]]]
        ] = None,
        multiple: bool = False,
        field_info_args: t.Optional[t.Union[AttributeDict, t.Dict[str, t.Any]]] = None,
        **kwargs: t.Any,
    ) -> None:
        self.multiple = multiple
        self._choices: t.List[t.Tuple[t.Any, str]] = [
            (c, c) if isinstance(c, str) else c for c in (choices or [])
        ]
        self._choices_loader = choices_loader
        super().__init__(field_info_args=field_info_args, **kwargs)
        self.multiple = annotation_is_sequence(self._field_info_args.annotation)

    def _get_choices(self) -> t.Union[t.Sequence[str], t.Sequence[t.Tuple[t.Any, str]]]:
        if self._choices_loader:
            self._choices = self._choices_loader()
        return self._choices

    @cached_property
    def _choice_values(self) -> t.List[str]:
        return [choice[0] for choice in self._choices]

    @cached_property
    def python_type(self) -> t.Type:
        return t.List[str] if self.multiple else str

    def validate_setup(self) -> None:
        super().validate_setup()
        choices = self._get_choices()
        assert choices, "Must provide 'choice'"

    def field_after_form_validation_action(self, v: t.Any) -> t.Any:
        if self.multiple:
            return self.field_after_for_multiple_form_validation_action(v)

        if not v.strip() and not self.model_field.required:
            return ""

        if v not in self._choice_values:
            raise ValueError("Input should be in {}".format(self._choice_values[:10]))

        return v

    def field_after_for_multiple_form_validation_action(self, v: t.Any) -> t.Any:
        if not v and not self.model_field.required:
            return v

        if not isinstance(v, list):
            raise ValueError("Expected a list of values")

        for i in v:
            if i not in self._choice_values:
                raise ValueError(
                    "Input should be in {}".format(self._choice_values[:10])
                )
        return v

    def field_after_validation(self, v: t.Any, info: ValidationInfo) -> t.Any:
        return self.field_after_form_validation_action(v)

    def field_after_for_multiple_validation(
        self, v: t.Any, info: ValidationInfo
    ) -> t.Any:
        return self.field_after_for_multiple_form_validation_action(v)
