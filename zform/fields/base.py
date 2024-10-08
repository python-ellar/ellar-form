import abc
import typing as t
import jinja2
from ellar.common import IExecutionContext
from ellar.common.compatible import AttributeDict
from ellar.common.params.params import FormFieldInfo
from ellar.common.params.resolvers import FormParameterResolver, IRouteParameterResolver
from ellar.common.params.resolvers.base import ResolverResult
from ellar.pydantic import ModelField, create_model_field
from ellar.reflect import fail_silently
from zform.constants import ZFORM_FIELD_ATTRIBUTES
from zform.fields.utils import format_errors, html_params, get_form_field_python_type
from markupsafe import Markup
from pydantic import AfterValidator, BeforeValidator
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Annotated

T_ = t.TypeVar("T_")


class FormLabel:
    """
    An HTML form label.

    Attributes:
        field_id (str): The ID of the associated form field.
        text (str): The text content of the label.
    """

    # language=html
    template = """
        <label for="{{field_id}}">{{text}}</label>
        """

    def __init__(self, field_id: t.Optional[str], text: t.Optional[str]):
        self.field_id = field_id
        self.text = text

    def __html__(self) -> str:
        """
        Return the HTML representation of the label.

        Returns:
            str: The HTML string of the label.
        """
        return self()

    def __call__(self, **kwargs) -> str:
        """
        Render the label as an HTML string.

        Args:
            **kwargs: Additional HTML attributes for the label.

        Returns:
            str: The rendered HTML string of the label.
        """
        content = jinja2.Template(self.template).render(
            text=self.text, field_id=self.field_id
        )
        return Markup(content)


class FieldBaseMeta(type):
    def __call__(cls, *args: t.Any, **kwargs: t.Any):
        field_info_args = kwargs.pop("field_info_args", None)

        instance = super(FieldBaseMeta, cls).__call__(
            *args,
            **kwargs,
            field_info_args=AttributeDict(field_info_args)
            if field_info_args is not None
            else None,
        )

        if field_info_args:
            instance.validate_setup()
            instance.on_field_ready()

        # backup init kwargs and args for later use
        setattr(instance, ZFORM_FIELD_ATTRIBUTES, dict(kwargs, args=args))

        return instance


class FieldBase(metaclass=FieldBaseMeta):
    """
    Base class for form fields in ZForm.

    Attributes:
        type (str): The type of the form field.
        name (str): The name of the form field.
        id (str): The ID of the form field.
        attrs (dict): Additional HTML attributes for the field.
        label (FormLabel): The label associated with the field.
        help_text (str): Help text for the field.
    """

    type: t.Optional[str] = None

    # language=HTML
    template = """
        {% if help_text %}
            <div>
              <input type="{{type}}" {{attrs}}>
              <small>{{help_text}}</small>
            </div>
        {% else %}
            <input type="{{type}}" {{attrs}}>
        {% endif %}
    """

    def __init__(
        self,
        name: t.Optional[str] = None,
        *,
        class_: str = "",
        id: t.Optional[str] = None,
        label: t.Optional[str] = None,
        disabled: t.Optional[bool] = False,
        read_only: t.Optional[bool] = False,
        field_info_args: t.Optional[t.Union[AttributeDict, t.Dict]] = None,
        **attrs: t.Any,
    ) -> None:
        # A field is fully configured when __field_info_args__ is provided
        assert self.type

        self._value = None
        self.name = name or "no-name"
        self.id = id

        self._data = None
        self.raw_data = None
        self.errors = []
        self._default = None
        self.attrs = AttributeDict(
            attrs,
            **{
                "disabled": disabled,
                "read_only": read_only,
                "class": class_,
            },
        )
        self.help_text = None
        self.label = None

        self._field_info_args = AttributeDict(
            field_info_args or self.build_field_info_args()
        )
        self.update_field_info_args(self._field_info_args)
        self._field_info: t.Optional[FieldInfo] = None
        self.__resolver: t.Optional[IRouteParameterResolver] = None

        if self._field_info_args:
            self._field_info_args.setdefault("alias", self.name)
            self.__apply_model_field()
            if not id:
                self.id = self._field_info.alias

            self.attrs.update(
                {
                    "required": self._field_info.is_required(),
                    "title": self._field_info.title,
                }
            )
            self.label = FormLabel(self.id, label or self.name.capitalize())
            self.help_text = self.help_text or self._field_info_args.description

    @property
    def field_info_args(self) -> AttributeDict:
        """
        Get the field info arguments.

        Returns:
            t.Dict: The field info arguments.
        """
        return self._field_info_args

    @property
    def default(self) -> t.Any:
        """
        Get the default value of the field.

        Returns:
            t.Any: The default value of the field.
        """
        return self._default

    @property
    def resolver(self) -> t.Optional[IRouteParameterResolver]:
        """
        Get the resolver associated with the field.

        Returns:
            t.Optional[IRouteParameterResolver]: The resolver instance, or None if not set.
        """
        return self.__resolver

    @property
    def required(self) -> bool:
        """
        Check if the field is required.

        Returns:
            bool: True if the field is required, False otherwise.
        """
        return self.__resolver.model_field.required

    @property
    def data(self) -> t.Any:
        """
        Get the data associated with the field.

        Returns:
            t.Any: The data associated with the field.
        """
        return self.raw_data if self.raw_data else self._data

    @data.setter
    def data(self, value: t.Any) -> None:
        """
        Set the data associated with the field.

        Args:
            value: The data to set.
        """
        self._data = value

    @default.setter
    def default(self, value: t.Any) -> None:
        """
        Set the default value of the field.

        Args:
            value: The default value to set.
        """
        self.process(value, suppress_error=True)
        self._default = value

    @property
    def model_field(self) -> ModelField:
        """
        Get the model field associated with the form field.

        Returns:
            ModelField: The model field instance.
        """
        return self.__resolver.model_field

    @property
    def value(self) -> T_:
        """
        Get the processed value of the field.

        Returns:
            T_: The processed value of the field.
        """
        return self._value

    def clear(self):
        """
        Clear all field inputs and validation.
        """
        self.raw_data = None
        self.errors = []
        self._data = None
        self._value = None

    def validate_setup(self) -> None:
        """
        Validate the setup of the field.

        Raises:
            AssertionError: If the name is not set.
        """
        assert self.name, "Name is required"

    def process(self, data: t.Any, suppress_error: bool = True) -> None:
        """
        Process the input data for the field.

        Args:
            data: The input data to process.
            suppress_error: Whether to suppress validation errors.
        """
        self.errors.clear()
        v_, errors_ = self.model_field.validate(
            data, {"processing_data": True}, loc=(self.__class__.__name__,)
        )

        if not errors_:
            self._value = v_
            # export to JSON for UI to understand
            self.data = fail_silently(self.model_field.serialize, v_) or v_

        if not suppress_error:
            self.errors = errors_

    def load(self) -> "FieldBase":
        """
        Load the default value into the form field.

        Returns:
            FieldBase: The field instance with the default value loaded.
        """
        self.process(self.default, suppress_error=True)
        return self

    def __call__(
        self, as_paragraph: bool = False, as_table: bool = False, **kwargs
    ) -> str:
        """
        Render the field as an HTML string.

        Args:
            as_paragraph: Whether to render the field wrapped in a paragraph.
            as_table: Whether to render the field as a table row.
            **kwargs: Additional HTML attributes for the field.

        Returns:
            str: The rendered HTML string of the field.
        """
        return self.render(**kwargs)

    def __html__(self) -> str:
        """
        Return the HTML representation of the field.

        Returns:
            str: The HTML string of the field.
        """
        return self()

    def get_render_context(self, attrs: t.Dict) -> t.Tuple[t.Dict, t.Dict]:
        return attrs, {}

    def render(self, **kwargs) -> str:
        """
        Render the field as an HTML input element.

        Args:
            **attrs: Additional HTML attributes for the input element.

        Returns:
            str: The rendered HTML string of the input element.
        """

        kwargs.setdefault("name", self.model_field.alias)
        kwargs.setdefault("id", self.id)
        kwargs.setdefault("value", self.data)

        attrs, ctx = self.get_render_context(dict(self.attrs, **kwargs))
        content = jinja2.Template(self.template).render(
            help_text=self.help_text,
            type=t.cast(t.Any, self.type),
            attrs=html_params(**attrs),
            **ctx,
        )
        return Markup(content)

    def render_as_p(self, **kwargs) -> str:
        """
        Render the field as a paragraph.

        Args:
            **kwargs: Additional HTML attributes for the paragraph.

        Returns:
            str: The rendered HTML string of the paragraph.
        """
        return self(as_paragraph=True, **kwargs)

    def render_as_table(self, **kwargs) -> str:
        """
        Render the field as a table row.

        Args:
            **kwargs: Additional HTML attributes for the table row.

        Returns:
            str: The rendered HTML string of the table row.
        """
        return self(as_table=True, **kwargs)

    def populate_obj(self, obj, name):
        """
        Populates `obj.<name>` with the field's data.

        :note: This is a destructive operation. If `obj.<name>` already exists,
               it will be overridden. Use with caution.
        """
        setattr(obj, name, self.value)

    def _form_after_validator(self, v: t.Any, info: ValidationInfo) -> t.Any:
        if info.context.get("processing_data"):
            return v
        return self.field_after_validation(v, info)

    def _form_before_validator(self, v: t.Any, info: ValidationInfo) -> t.Any:
        if info.context.get("processing_data"):
            return v
        return self.field_before_validation(v, info)

    def __apply_model_field(self) -> None:
        """
        Create a new model field and subscribe to pre- and post-validation.

        Raises:
            AssertionError: If the name is not set.
        """
        assert self.name, "Name is required at this point."
        # Extra field validations
        annotation = Annotated[
            self._field_info_args.annotation,
            BeforeValidator(self._form_before_validator),
            AfterValidator(self._form_after_validator),
        ]
        # Create new FormFieldInfo
        self._field_info = FormFieldInfo(
            **dict(self._field_info_args, annotation=annotation)
        )

        # Create ModelField for Form Resolver
        new_model_field = create_model_field(
            name=self.name,
            type_=self._field_info.annotation,
            default=self._field_info.default,
            alias=self._field_info.alias,
            field_info=self._field_info,
        )

        self.__resolver = FormParameterResolver(new_model_field)

    async def process_form_data(
        self, ctx: IExecutionContext, body: t.Any
    ) -> ResolverResult:
        """
        Process form data for the field.

        Args:
            ctx: The execution context.
            body: The form data.

        Returns:
            ResolverResult: The result of the form data processing.
        """
        res = await self.__resolver.resolve(ctx, body=body)
        _, self.raw_data = dict(res.raw_data).popitem()
        self.errors = format_errors(res.errors)

        if not res.errors:
            self._value = res.data[self.model_field.name]

        return res

    def on_field_ready(self) -> None:
        """
        Perform extra field computations when the field is ready.
        """
        default = self._field_info.get_default(call_default_factory=True)
        self.default = (
            None if default is ... or default is PydanticUndefined else default
        )

    def field_after_validation(self, v: t.Any, info: ValidationInfo) -> t.Any:
        """
        Perform extra post-form field validation.

        Args:
            v: The field value.
            info: Validation info.

        Returns:
            t.Any: The processed field value.
        """
        return v

    def field_before_validation(self, v: t.Any, info: ValidationInfo) -> t.Any:
        """
        Perform extra pre-form field validation.

        Args:
            v: The field value.
            info: Validation info.

        Returns:
            t.Any: The processed field value.
        """
        return v

    @property
    @abc.abstractmethod
    def python_type(self) -> t.Type:
        """
        Get the Python type of the field.

        Returns:
            t.Type: The Python type of the field.
        """

    def rebuild(
        self,
        annotation: t.Any = None,
        name: t.Optional[str] = None,
        alias: t.Optional[str] = None,
        default: t.Any = None,
        default_factory: t.Optional[t.Callable] = None,
    ) -> "FieldBase":
        """
        Rebuild a form field with updated attributes and metadata.

        This function takes an existing form field and creates a new instance with
        potentially modified attributes such as name, alias, and annotation.

        Args:
            annotation (Optional[Any], optional): New type annotation for the field. Defaults to None.
            name (Optional[str], optional): New name for the field. Defaults to None.
            alias (Optional[str], optional): New alias for the field. Defaults to None.
            default (Optional[t.Any], optional): New default value for the field. Defaults to None.
            default_factory (Optional[t.Callable], optional): New default factory for the field. Defaults to None.

        Returns:
            Union[_TFormField, ZFormFieldBase]: A new instance of the form field with updated attributes.

        Notes:
            - If name or alias is not provided, they default to the original field's name.
            - The function preserves the original default and default_factory values.
            - The new field is created using the original field's class and updated arguments.
        """
        z_field_info_args: dict = self.__dict__[ZFORM_FIELD_ATTRIBUTES]
        field_info_args = z_field_info_args.get("field_info_args", {})

        default = default or field_info_args.get("default", ...)
        default_factory = default_factory or field_info_args.get(
            "default_factory", None
        )

        name = name or self.name
        alias = alias or name

        z_field_info_args.update(
            name=name,
            field_info_args=AttributeDict(
                **field_info_args,
                alias=alias,
                annotation=annotation or get_form_field_python_type(self),
                default=default,
                default_factory=default_factory,
            ),
        )
        args = z_field_info_args.pop("args", ())

        return self.__class__(*args, **z_field_info_args)

    @classmethod
    def create_from_annotation(
        cls,
        annotation: t.Any,
        name: t.Optional[str] = None,
        alias: t.Optional[str] = None,
        default: t.Any = None,
        default_factory: t.Optional[t.Callable] = None,
        **kwargs: t.Any,
    ) -> "FieldBase":
        """
        Create a new field instance from an annotation.

        Args:
            annotation: The annotation to create the field from.
            name (Optional[str], optional): New name for the field. Defaults to None.
            alias (Optional[str], optional): New alias for the field. Defaults to None.
            default (Optional[t.Any], optional): New default value for the field. Defaults to None.
            default_factory (Optional[t.Callable], optional): New default factory for the field. Defaults to None.
            **kwargs: Additional keyword arguments for field creation.

        Returns:
            FieldBase: The new field instance.
        """

        name = name or ""

        field_info_args = kwargs.pop("field_info_args", {})
        args = kwargs.pop("args", ())

        field_info_args.update(
            alias=alias or name,
            annotation=annotation,
            default=default or ...,
            default_factory=default_factory,
        )

        kwargs["field_info_args"] = field_info_args
        return cls(*args, name=name, **kwargs)

    def build_field_info_args(self) -> t.Dict:
        """
        Build the field info arguments.

        Returns:
            t.Dict: The field info arguments.
        """
        return {"annotation": self.python_type}

    def update_field_info_args(self, field_info_args: t.Dict) -> None:
        """
        Update the field info arguments with additional attributes.

        Args:
            field_info_args (t.Dict): The field info arguments to update.
        """
        field_info_args.setdefault("annotation", self.python_type)
