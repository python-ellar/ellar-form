import typing as t
from pydantic import EmailStr

from ellar.pydantic.types import AnyUrl
from .base import FieldBase


class StringField(FieldBase):
    type: str = "text"

    def __init__(
        self,
        placeholder: t.Optional[str] = None,
        field_info_args: t.Optional[t.Union[t.Dict[str, t.Any], t.Any]] = None,
        max_length: t.Optional[int] = None,
        min_length: t.Optional[int] = None,
        **kwargs: t.Any,
    ) -> None:
        self.max_length = max_length
        self.min_length = min_length

        if field_info_args is not None:
            self.max_length = field_info_args.get("max_length")
            self.min_length = field_info_args.get("min_length")

        kwargs.update(
            maxlength=self.max_length,
            minlength=self.min_length,
            placeholder=placeholder,
        )
        super().__init__(**kwargs, field_info_args=field_info_args)

    def update_field_info_args(self, field_info_args: t.Dict) -> None:
        super().update_field_info_args(field_info_args)
        if self.max_length is not None and field_info_args.get("max_length") is None:
            field_info_args.update({"max_length": self.max_length})

        if self.min_length is not None and field_info_args.get("min_length") is None:
            field_info_args.update({"min_length": self.min_length})

    @property
    def python_type(self) -> t.Type[t.Any]:
        return str


class TextAreaField(StringField):
    # language=html
    template = """
    {% if help_text %}
        <div>
          <textarea {{attrs}}></textarea>
          <small>{{help_text}}</small>
        </div>
    {% else %}
        <textarea {{attrs}}></textarea>
    {% endif %}
    """

    def __init__(self, row: int = 6, cols: int = 30, **kwargs: t.Any) -> None:
        super().__init__(**kwargs, row=row, cols=cols)


class EmailField(StringField):
    type: str = "email"

    @property
    def python_type(self) -> t.Type[t.Any]:
        return EmailStr


class URLField(StringField):
    type: str = "url"

    @property
    def python_type(self) -> t.Type[t.Any]:
        return AnyUrl


class PhoneField(StringField):
    type: str = "phone"


class ColorField(StringField):
    type: str = "color"


class PasswordField(StringField):
    type: str = "password"
