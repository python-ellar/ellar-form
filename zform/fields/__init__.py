import decimal
import enum as enumMeta
import typing as t
from datetime import date, datetime, time

from pydantic import BaseModel, EmailStr
from ellar.pydantic import lenient_issubclass
from typing_extensions import get_origin
from .select import ChoiceField
from .base import FieldBase
from .dates import (
    DateField,
    DateTimeField,
    DateTimeLocalField,
    TimeField,
    TimeZoneField,
)
from .enum import EnumField
from .obj import ObjectField
from .numbers import (
    DecimalField,
    IntegerField,
    RangeField,
    FloatField,
)
from .string import (
    ColorField,
    EmailField,
    PasswordField,
    PhoneField,
    StringField,
    TextAreaField,
    URLField,
)
from .boolean import BooleanField
from .flist import FieldList
from .files import FileField, ImageFileField
from starlette.datastructures import UploadFile
from ellar.common.datastructures import UploadFile as EllarUploadFile
from .widget import FieldWidget
from .label import FormLabel

__ZFORM_TYPES__ = {
    int: IntegerField,
    float: FloatField,
    str: StringField,
    decimal.Decimal: DecimalField,
    date: DateField,
    time: TimeField,
    datetime: DateTimeField,
    enumMeta.EnumMeta: EnumField,
    list: FieldList,
    tuple: FieldList,
    set: FieldList,
    dict: ObjectField,
    UploadFile: FileField,
    EllarUploadFile: FileField,
    EmailStr: EmailField,
    bool: BooleanField,
}


def add_form_type(type_: t.Type[FieldBase], form_type: t.Type[FieldBase]) -> None:
    """
    Add a new form type to the registry.

    Args:
        type_ (Type[FieldBase]): The type to add.
        form_type (Type[FieldBase]): The form type to add.
    """
    __ZFORM_TYPES__[type_] = form_type


def get_field_by_annotation(
    annotation: t.Any, raise_exception: bool = True
) -> t.Type[FieldBase]:
    """
    Get the appropriate Field class for a given type.

    Args:
        annotation (Any): The type to find a corresponding Field for.
        raise_exception (bool, optional): Whether to raise an exception if no matching field is found. Defaults to True.

    Returns:
        Type[FieldBase]: The corresponding Field class.

    Raises:
        Exception: If raise_exception is True and no matching field is found.
    """
    origin_type_ = get_origin(annotation) or annotation

    if lenient_issubclass(origin_type_, BaseModel):
        origin_type_ = dict

    _default_available = __ZFORM_TYPES__.get(type(origin_type_))
    form_field = __ZFORM_TYPES__.get(origin_type_, _default_available)

    if raise_exception and form_field is None:
        raise Exception(f"Type Annotation is not supported. {annotation}")

    return form_field


__all__ = [
    "FormLabel",
    "DateField",
    "DateTimeField",
    "DateTimeLocalField",
    "TimeField",
    "TimeZoneField",
    "EnumField",
    "ObjectField",
    "DecimalField",
    "IntegerField",
    "RangeField",
    "FloatField",
    "ColorField",
    "EmailField",
    "PasswordField",
    "PhoneField",
    "StringField",
    "TextAreaField",
    "URLField",
    "FieldList",
    "get_field_by_annotation",
    "add_form_type",
    "BooleanField",
    "FileField",
    "ImageFileField",
    "FieldBase",
    "ChoiceField",
    "FieldWidget",
]
