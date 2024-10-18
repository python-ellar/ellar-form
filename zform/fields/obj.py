import typing as t
import uuid

from ellar.common import IExecutionContext
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.params.resolvers.base import ResolverResult
from ellar.pydantic.utils import lenient_issubclass
from zform.fields.utils import format_errors
from pydantic import BaseModel

from .base import FieldBase
from .widget import FieldWidget


class ObjectFieldWidget(FieldWidget):
    field: "ObjectField"
    # language=HTML
    template: str = """
        <fieldset {{attrs}}>
            {% for field in fields %}
                <div>
                    {{field.label()}}
                    {{field()}}
                </div>
            {% endfor %}
        </fieldset>
        """

    def get_render_context(self) -> t.Dict:
        ctx = super().get_render_context()
        ctx.update(fields=list(self.field))
        return ctx


class ObjectField(FieldBase):
    """
    Represents a collection of other fields, can be used for embedded mongodb documents.

    Attributes:
        type (str): The type of the field, defaults to "json".
        _fields: t.Optional[t.Sequence[ZFormFieldBase]]: List of child fields.
        schema (Optional[Type[BaseModel]]): Pydantic schema for the object.

    Example:
        ```python
        class FormSerializer(BaseModel):
            config: dict = ZFieldInfo(
                ObjectField(
                    fields=[
                        StringField("key", default="Okay"),
                        IntegerField("value", help_text="multiple of 5")
                    ]
                )
            )
        ```
    Example 2:
        ```python
        Class ObjectSchema(Serializer):
            key: str
            value: int = Field(IntegerField(help_text="multiple of 5"))

        Class FormSerializer(BaseModel):
            config: ObjectSchema = ZFieldInfo(ObjectField)
        ```
    """

    type: t.Optional[str] = "json"
    widgetType: t.Type[FieldWidget] = ObjectFieldWidget

    def __init__(
        self,
        fields: t.Optional[t.Sequence[FieldBase]] = None,
        schema: t.Optional[t.Type[BaseModel]] = None,
        **kwargs: t.Any,
    ) -> None:
        self.schema = schema

        kwargs.setdefault("id", kwargs.get("name", f"object_{uuid.uuid4().hex[:5]}"))
        super().__init__(**kwargs)

        self._fields: t.List[FieldBase] = list(fields or [])

        for field in self:
            field.validate_setup()

        if lenient_issubclass(self.field_info_args.annotation, BaseModel):
            if schema is not None and self.field_info_args.annotation != schema:
                raise ImproperConfiguration(
                    f"Annotation {self.field_info_args.annotation} is not the same as the provided schema {schema}."
                )

            if self._fields:
                raise ImproperConfiguration(
                    "You cannot provide both fields and schema to ZFormObjectField."
                )
            self.schema = self.field_info_args.annotation
        self.setup()

    def setup(self) -> None:
        if self._fields:
            self._propagate_id()

        if not self._fields and self.schema:
            from zform.params.resolver_gen import generate_fields_from_schema

            self._fields = generate_fields_from_schema(
                self.schema, format_name=self._name_formatter
            )

        # if not self._fields and not self.schema:
        #     raise ImproperConfiguration(
        #         "ObjectField must have either 'schema' or 'fields' defined."
        #     )

    def validate_setup(self) -> None:
        """Validate that either schema or fields are provided."""
        assert self.schema or self._fields, "Must provide either 'schema' or 'fields'"

    def _propagate_id(self) -> None:
        """Update child fields' IDs by adding this field's ID as prefix."""
        original_fields = list(self._fields)
        self._fields.clear()

        for form_field in original_fields:
            instance = form_field.rebuild(
                name=form_field.name,
                alias=self._name_formatter(form_field.name),
            )
            self._fields.append(instance)

    def _name_formatter(self, name: str) -> str:
        """
        Format the name of a child field.

        Args:
            name: Original name of the child field.

        Returns:
            str: Formatted name including this field's ID.
        """
        if self.field_info_args.alias:
            return (
                self.field_info_args.alias
                + ("." if self.field_info_args.alias else "")
                + name
            )
        return self.id + ("." if self.id else "") + name

    def __iter__(self) -> t.Iterator[FieldBase]:
        """
        Iterate over child fields.

        Returns:
            Iterator of child FieldBase objects.
        """
        return iter(self._fields)

    async def _process_form_data(
        self, ctx: IExecutionContext, body: t.Any
    ) -> t.Tuple[t.Dict, t.Dict, t.Dict]:
        """
        Process form data for all child fields.

        Args:
            ctx: Execution context.
            body: Form data.

        Returns:
            Tuple of processed values, errors, and raw data.
        """
        values: t.Dict[str, t.Any] = {}
        errors = {}
        raw_data = {}

        for field in self:
            res_ = await field.process_form_data(ctx=ctx, body=body)
            if res_.data:
                value = {field.name: res_.data[field.model_field.name]}
                values.update(value)
            if res_.errors:
                errors.setdefault(field.model_field.name, []).extend(
                    format_errors(res_.errors)
                )
            raw_data.update({field.name: res_.raw_data[field.model_field.name]})
        return values, errors, raw_data

    async def process_form_data(
        self, ctx: IExecutionContext, body: t.Any, **kwargs: t.Any
    ) -> ResolverResult:
        """
        Process and validate form data for this object field.

        Args:
            ctx: Execution context.
            body: Form data.

        Returns:
            ResolverResult containing processed data, errors, and raw data.
        """
        values, errors, raw_data = await self._process_form_data(ctx, body=body)
        if not errors:
            v_, errors = self.model_field.validate(values, {}, loc=("form",))

            if not errors:
                self._value = v_

            if errors:
                self.errors = {self.name: format_errors(errors)}

            return ResolverResult(
                {self.name: v_},
                errors or [self.errors] if self.errors else [],
                {self.name: raw_data},
            )

        self.errors = errors
        return ResolverResult(
            {self.name: values}, [{"msg": errors}], {self.name: raw_data}
        )

    def process(
        self, data: t.Dict, suppress_error: bool = True, **kwargs: t.Any
    ) -> None:
        """
        Process input data for this field.

        Args:
            data: Input data to process.
            suppress_error: Whether to suppress validation errors.
        """
        if data is None:
            data = {}

        for item in self:
            if isinstance(data, dict):
                field_data = data.get(item.name)
            else:
                field_data = getattr(data, item.name, None)

            item.process(field_data, suppress_error=suppress_error)

    @property
    def python_type(self) -> t.Type[t.Any]:
        if self.schema:
            return self.schema
        return dict
