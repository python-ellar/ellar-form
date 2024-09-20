import typing as t
import functools
from ellar.common.params.params import ParamFieldInfo
from ellar.pydantic.types import Undefined
from zform.fields.base import FieldBase

from .field_infos import ZFieldInfo, ZFormInfo

_Unset: t.Any = Undefined


class _ZFormDecorator:
    field_info: t.Callable = functools.partial(ZFormInfo, embed=True)

    @classmethod
    def __create__(
        cls,
        default: t.Any = ...,
        *,
        default_factory: t.Union[t.Callable[[], t.Any], None] = _Unset,
        media_type: str = "application/x-www-form-urlencoded",
        alias: t.Optional[str] = None,
        alias_priority: t.Union[int, None] = _Unset,
        validation_alias: t.Union[str, None] = None,
        serialization_alias: t.Union[str, None] = None,
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        gt: t.Optional[float] = None,
        ge: t.Optional[float] = None,
        lt: t.Optional[float] = None,
        le: t.Optional[float] = None,
        min_length: t.Optional[int] = None,
        max_length: t.Optional[int] = None,
        pattern: t.Optional[str] = None,
        discriminator: t.Union[str, None] = None,
        strict: t.Union[bool, None] = _Unset,
        multiple_of: t.Union[float, None] = _Unset,
        allow_inf_nan: t.Union[bool, None] = _Unset,
        max_digits: t.Union[int, None] = _Unset,
        decimal_places: t.Union[int, None] = _Unset,
        examples: t.Optional[t.List[t.Any]] = None,
        deprecated: t.Optional[bool] = None,
        include_in_schema: bool = True,
        json_schema_extra: t.Union[t.Dict[str, t.Any], None] = None,
        validate_on_write: bool = True,
        **extra: t.Any,
    ) -> ParamFieldInfo:
        """
        Defines an expected body object in websocket Route Function Parameter
        """
        return cls.field_info(
            default=default,
            default_factory=default_factory,
            alias=alias,
            title=title,
            description=description,
            gt=gt,
            ge=ge,
            lt=lt,
            le=le,
            min_length=min_length,
            max_length=max_length,
            discriminator=discriminator,
            multiple_of=multiple_of,
            allow_inf_nan=allow_inf_nan,
            max_digits=max_digits,
            decimal_places=decimal_places,
            pattern=pattern,
            alias_priority=alias_priority,
            validation_alias=validation_alias,
            serialization_alias=serialization_alias,
            strict=strict,
            json_schema_extra=json_schema_extra,
            examples=examples,
            include_in_schema=include_in_schema,
            deprecated=deprecated,
            validate_on_write=validate_on_write,
            media_type=media_type,
            **extra,
        )


class _ZFormFieldDecorator(_ZFormDecorator):
    field_info: t.Callable = functools.partial(ZFieldInfo)

    @classmethod
    def __create__(
        cls,
        zform_field: t.Optional[t.Union[t.Type[FieldBase], FieldBase]] = None,
        default: t.Any = ...,
        **kwargs: t.Any,
    ) -> t.Any:
        assert zform_field is not None, "zform_field must be provided"
        return super().__create__(default=default, zform_field=zform_field, **kwargs)


ZFieldDecorator = _ZFormFieldDecorator.__create__
ZFormDecorator = _ZFormDecorator.__create__
