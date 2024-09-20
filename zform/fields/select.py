import typing as t
from functools import cached_property
from pydantic import ValidationInfo

from ellar.reflect import fail_silently
from .string import StringField
from ellar.common.compatible import AttributeDict
from ellar.pydantic.utils import annotation_is_sequence


class ChoiceField(StringField):
    _coerce_type: t.Callable = str

    # language=html
    template: str = """
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

    def __init__(
        self,
        choices: t.Union[t.Sequence[str], t.Sequence[t.Tuple[t.Any, str]], None] = None,
        multiple: bool = False,
        field_info_args: t.Optional[t.Union[AttributeDict, t.Dict[str, t.Any]]] = None,
        **kwargs: t.Any,
    ) -> None:
        self.multiple = multiple
        self._choices: t.List[t.Tuple[t.Any, str]] = [
            (c, c) if isinstance(c, str) else c for c in (choices or [])
        ]
        if field_info_args and field_info_args.annotation:
            self.multiple = annotation_is_sequence(field_info_args.annotation)
        super().__init__(
            multiple=self.multiple, field_info_args=field_info_args, **kwargs
        )

    @cached_property
    def _choice_values(self) -> t.List[str]:
        return [choice[0] for choice in self._choices]

    @cached_property
    def python_type(self) -> t.Type:
        return t.List[str] if self.multiple else str

    def validate_setup(self) -> None:
        super().validate_setup()
        assert self._choices, "Must provide 'choice'"

    def get_render_context(self, attrs: t.Dict) -> t.Tuple[t.Dict, t.Dict]:
        data = attrs.pop("value", self.data)
        # ensure data is in coerce type
        data = [
            fail_silently(self._coerce_type, i) or i
            for i in (data if isinstance(data, (list, tuple)) else [data])
        ]

        return attrs, dict(
            is_selected=lambda v: (self._coerce_type(v) in data or [])
            if v is not None
            else False,
            choices=self._choices,
            multiple=self.multiple,
        )

    def field_after_validation(self, v: t.Any, info: ValidationInfo) -> t.Any:
        if self.multiple:
            return self.field_after_for_multiple_validation(v, info)

        if not v.strip() and not self.model_field.required:
            return ""

        if v not in self._choice_values:
            raise ValueError("Input should be in {}".format(self._choice_values[:10]))

        return v

    def field_after_for_multiple_validation(
        self, v: t.Any, info: ValidationInfo
    ) -> t.Any:
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
