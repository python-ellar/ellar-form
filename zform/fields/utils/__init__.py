import typing as t

from markupsafe import escape
from typing_extensions import get_origin, Annotated, get_args
from ellar.pydantic.types import UnionType
from ellar.pydantic.utils import annotation_is_sequence

if t.TYPE_CHECKING:  # pragma: no cover
    from zform.fields.base import FieldBase

_TFormField = t.TypeVar("_TFormField")


def get_form_field_python_type(field: "FieldBase") -> t.Type:
    """
    Get the Python type of a form field.

    Args:
        field: The form field instance.

    Returns:
        t.Type: The Python type of the form field.
    """
    field.validate_setup()

    if field._field_info:
        return get_type(field.model_field.type_)

    return field.python_type


def format_errors(errors: t.List[t.Dict]) -> t.List[t.Dict[str, t.Any]]:
    return [i["msg"] for i in errors]


def is_annotated(type_: t.Any) -> bool:
    origin_ = get_origin(type_)
    return origin_ is Annotated or origin_ is UnionType or origin_ is t.Union


def get_type(type_: t.Any) -> t.Type:
    """
    Recursively resolve and return the base type of a given type annotation.

    This function handles various type annotations, including Annotated types,
    sequence types, and nested type origins.

    Args:
        type_ (t.Any): The type annotation to resolve.

    Returns:
        t.Type: The resolved base type.

    Raises:
        Exception: If the type cannot be resolved or is invalid.

    Notes:
        - For Annotated types, it resolves to the first argument.
        - For sequence types, it resolves to the type of the first element.
        - For types with origins, it recursively resolves the origin.
    """
    if is_annotated(type_):
        first_arg, *extra_args = get_args(type_)
        return get_type(first_arg)

    if annotation_is_sequence(type_):
        first_arg, *extra_args = get_args(type_)
        return get_type(first_arg)

    if get_origin(type_) is None:
        return type_
    elif isinstance(get_origin(type_), type):
        try:
            return get_type(get_origin(type_))
        except Exception as e:
            raise e

    print(f"Failed to get type for {type_}")
    raise Exception(f"Invalid Type: {type_}")


def clean_key(key):
    key = key.rstrip("_")
    if key.startswith("data_") or key.startswith("aria_"):
        key = key.replace("_", "-")
    return key


def html_params(**kwargs: t.Any) -> str:
    """
    Generate HTML attribute syntax from inputted keyword arguments.

    Args:
        **kwargs: Arbitrary keyword arguments representing HTML attributes.

    Returns:
        str: A string of HTML attributes.

    Notes:
        - The output is sorted by keys for consistent results.
        - Suffixing reserved keywords like 'class' and 'for' with an underscore allows their use.
        - Attributes starting with 'data_' or 'aria_' have underscores replaced with hyphens.
        - Boolean values have special handling:
          * True generates compact output (e.g., checked=True becomes simply "checked")
          * False or None are ignored and generate no output.

    Examples:
        >>> html_params(data_attr='user.name', aria_labeledby='name')
        'data-attr="user.name" aria-labeledby="name"'
        >>> html_params(name='text1', id='f', class_='text')
        'class="text" id="f" name="text1"'
        >>> html_params(checked=True, readonly=False, name="text1", abc="hello")
        'abc="hello" checked name="text1"'
    """
    params = []
    for k, v in sorted(kwargs.items()):
        k = clean_key(k)
        if v is True:
            params.append(k)
        elif v is False or v is None:
            pass
        else:
            params.append(f'{str(k)}="{escape(v)}"')
    return " ".join(params)
