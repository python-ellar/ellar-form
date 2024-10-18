import enum
import typing as t
from enum import Enum, IntEnum
from zform.fields.utils import get_type

from ellar.common.exceptions import ImproperConfiguration
from pydantic import ValidationInfo
from ellar.pydantic.utils import lenient_issubclass

from .select import ChoiceField


class _DefaultEnum(enum.Enum):
    DEFAULT = "default"


class EnumField(ChoiceField):
    def __init__(
        self,
        enum: t.Type[Enum] = _DefaultEnum,
        **kwargs: t.Any,
    ) -> None:
        self.enum = enum
        super().__init__(**kwargs)

        type_ = get_type(self.field_info_args.annotation)
        if not lenient_issubclass(type_, Enum):
            raise ImproperConfiguration(
                f"EnumField Expected a Enum type but got {type_}"
            )
        if self.enum is not _DefaultEnum and self.enum != type_:
            raise ImproperConfiguration(
                f"Annotation {type_} is not the same as the enum {self.enum}"
            )

        if self.enum is _DefaultEnum:
            self.enum = type_

        self._coerce_type = int if lenient_issubclass(self.enum, IntEnum) else str
        self._choices = [(e.value, e.name.replace("_", " ")) for e in self.enum]

    def validate_setup(self) -> None:
        super().validate_setup()

    def field_after_validation(self, v: t.Any, info: ValidationInfo) -> t.Any:
        return v

    @property
    def default(self) -> t.Any:
        if isinstance(self._default, enum.Enum):
            return self._default.value

        return self._default

    @default.setter
    def default(self, value: t.Any) -> t.Any:
        self._default = value

    @property
    def python_type(self) -> t.Type:
        if self.multiple:
            return t.List[self.enum]
        return self.enum
