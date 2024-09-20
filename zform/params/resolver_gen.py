import typing as t
from ellar.pydantic import lenient_issubclass, FieldInfo, BaseModel

from ellar.common.compatible import AttributeDict
from ellar.common.constants import MULTI_RESOLVER_KEY
from ellar.common.params.args.resolver_generators import BulkArgsResolverGenerator
from ellar.reflect import reflect
from zform.fields import utils, FieldList, get_field_by_annotation
from zform.constants import ZFORM_FIELD_ATTRIBUTES, ZFORM_RESOLVER_GEN_RESULTS
from zform.fields.base import FieldBase
from zform.params.field_infos import ZFieldInfo


def __format_name__(name: str) -> str:
    return name


def check_field_list(
    field: t.Type["FieldBase"], annotation: t.Type, field_name: str
) -> t.Dict[str, t.Any]:
    """
    Check if the field is a FieldList and return the sub_field if it is.

    Args:
        field (Type[FieldBase]): The field type.
        annotation (Type): The field annotation.
        field_name (str): The field name.

    Returns:
        Dict[str, Any]: A dictionary containing the sub_field if it is a FieldList.
    """

    if lenient_issubclass(field, FieldList):
        type_ = utils.get_type(annotation)
        sub_field = get_field_by_annotation(type_)

        sub_field_instance = sub_field.create_from_annotation(
            annotation, name=field_name
        )

        return {"field": sub_field_instance}

    return {}


def generate_fields_from_schema(
    schema: BaseModel, format_name: t.Optional[t.Callable[[str], str]] = None
) -> t.List[FieldBase]:
    """
    Generate a list of FieldBase instances from a Pydantic BaseModel schema.

    Args:
        schema (BaseModel): The Pydantic model to generate fields from.
        format_name (Optional[Callable[[str], str]]): A function to format field names.
            Defaults to __format_name__ if not provided.

    Returns:
        List[FieldBase]: A list of FieldBase instances representing the form fields.
    """
    form_fields = reflect.get_metadata(ZFORM_RESOLVER_GEN_RESULTS, schema)

    if form_fields:
        return form_fields

    format_name = format_name or __format_name__
    form_fields = []

    for name, field in schema.model_fields.items():
        _field_info_attributes_set: dict = getattr(field, "_attributes_set", {})
        field_info_args = {}

        if isinstance(field, ZFieldInfo):
            field_info_args = getattr(
                field.zform_field,
                ZFORM_FIELD_ATTRIBUTES,
                {},
            )
            field_type = type(field.zform_field)
        else:
            field_type = get_field_by_annotation(field.annotation)
            field_info_args.update(
                check_field_list(
                    field_type, field.annotation, field_name=f"{name}-sub_field"
                )
            )

        field_info_args.update(
            name=name,
            field_info_args=AttributeDict(
                _field_info_attributes_set,
                alias=format_name(field.alias or field.validation_alias or name),
                annotation=field.annotation,
            ),
        )

        args = field_info_args.pop("args", ())
        instance = field_type(*args, **field_info_args)
        form_fields.append(instance)

    reflect.define_metadata(ZFORM_RESOLVER_GEN_RESULTS, form_fields, schema)
    return form_fields


class ZFormResolverGenerator(BulkArgsResolverGenerator):
    """
    A resolver generator for ZForm fields.

    This class extends BulkArgsResolverGenerator to provide custom resolution
    for ZForm fields based on Pydantic models.
    """

    generate_fields_from_schema = staticmethod(generate_fields_from_schema)

    def generate_resolvers(self, body_field_class: t.Type[FieldInfo]) -> None:
        form_fields = self.generate_fields_from_schema(self.pydantic_outer_type)

        if isinstance(self.param_field.field_info.json_schema_extra, dict):
            self.param_field.field_info.json_schema_extra[MULTI_RESOLVER_KEY] = (
                form_fields  # type:ignore[assignment]
            )
