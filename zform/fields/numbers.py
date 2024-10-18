import decimal
import typing as t
from .base import FieldBase
from .widget import FieldWidget


class NumberFieldWidget(FieldWidget):
    field: "IntegerField"

    def get_html_attrs(self, **extra_attrs: t.Any) -> t.Dict:
        attrs = super().get_html_attrs(**extra_attrs)
        attrs.update(step=self.field.step, max=self.field.max, min=self.field.min)
        return attrs


class IntegerField(FieldBase):
    type = "number"
    widgetType: t.Type[FieldWidget] = NumberFieldWidget

    def __init__(
        self,
        placeholder: t.Optional[str] = None,
        step: t.Union[str, int, None] = None,
        max: t.Optional[int] = None,
        min: t.Optional[int] = None,
        **kwargs: t.Any,
    ) -> None:
        self.step = step
        self.max = max
        self.min = min
        super().__init__(**kwargs, placeholder=placeholder)

    def update_field_info_args(self, field_info_args: t.Dict) -> None:
        super().update_field_info_args(field_info_args)
        if self.max is not None and field_info_args.get("lt") is None:
            field_info_args.update({"le": self.max})

        if self.min is not None and field_info_args.get("gt") is None:
            field_info_args.update({"ge": self.min})

        if (
            self.step
            and self.step != "any"
            and field_info_args.get("multiple_of") is None
        ):
            field_info_args.update({"multiple_of": self.step})

        self.step = self.step or field_info_args.get("multiple_of")
        self.max = self.max or field_info_args.get("le", field_info_args.get("lt"))
        self.min = self.min or field_info_args.get("ge", field_info_args.get("gt"))

    @property
    def python_type(self) -> t.Type:
        return int


class DecimalField(IntegerField):
    def __init__(self, step: t.Union[str, int, None] = "any", **kwargs: t.Any) -> None:
        super().__init__(step=step, **kwargs)

    @property
    def python_type(self) -> t.Type:
        return decimal.Decimal


class RangeField(IntegerField):
    type = "range"

    @property
    def python_type(self) -> t.Type:
        return float


class FloatField(RangeField):
    type = "number"

    def __init__(
        self,
        placeholder: t.Optional[str] = None,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs, placeholder=placeholder)
