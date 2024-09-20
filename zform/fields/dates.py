import datetime
import typing as t
from zform.fields.utils.timezones import common_timezones

from .select import ChoiceField
from .numbers import IntegerField


class TimeZoneField(ChoiceField):
    def __init__(
        self,
        time_zones: t.Union[
            t.Sequence[str], t.Sequence[t.Tuple[t.Any, str]], None
        ] = None,
        **kwargs: t.Any,
    ) -> None:
        if time_zones is None or not time_zones:
            time_zones = [
                # (value, key)
                (x, x.replace("_", " "))
                for x in common_timezones
            ]
        kwargs.update(choices=time_zones)
        super().__init__(**kwargs)

        if self._field_info:
            if not self.model_field.required:
                self._choices.insert(0, (" ", "Select Time Zone"))
        self._coerce_type = str


class DateTimeLocalField(IntegerField):
    type = "datetime-local"

    def __init__(
        self, data_alt_format: t.Optional[str] = "F j, Y  H:i:S", **kwargs: t.Any
    ) -> None:
        super().__init__(**kwargs, data_alt_format=data_alt_format)

    @property
    def python_type(self) -> t.Type:
        return datetime.datetime


class DateTimeField(IntegerField):
    type = "datetime"

    @property
    def python_type(self) -> t.Type:
        return datetime.datetime


class DateField(IntegerField):
    type = "date"

    @property
    def python_type(self) -> t.Type:
        return datetime.date


class TimeField(IntegerField):
    type = "time"

    def __init__(
        self, data_alt_format: t.Optional[str] = "H:i:S", **kwargs: t.Any
    ) -> None:
        super().__init__(**kwargs, data_alt_format=data_alt_format)

    @property
    def python_type(self) -> t.Type:
        return datetime.time
