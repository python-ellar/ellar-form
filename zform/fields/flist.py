import typing as t

from starlette.datastructures import FormData
from ellar.common import IExecutionContext
from zform.constants import ZFORM_FIELD_ATTRIBUTES
from ellar.common.params.resolvers.base import ResolverResult
from zform.fields.utils import get_form_field_python_type
from ellar.pydantic.utils import annotation_is_sequence
from .base import FieldBase
from .widget import FieldWidget


class FieldListWidget(FieldWidget):
    field: "FieldList"

    # language=html
    template: str = """
        <div {{attrs}}>
            <input id="{{ field.id }}-next-index" value="{{ next_index }}" hidden>

            {% for item in field %}
                <div>
                    {{item.label()}}
                    {{item()}}
                </div>
            {% endfor %}
        </div>
        """

    def get_render_context(self) -> t.Dict:
        """
        Get the context for rendering the field template.

        Returns:
            Dict: A dictionary containing the field and the next index for rendering.
        """
        ctx = super().get_render_context()
        ctx.update(field=self, next_index=len(self.field.items))
        return ctx


class FieldList(FieldBase):
    """
    A form field that represents a list of other form fields.

    This class allows for the creation of dynamic lists of form fields, where each item
    in the list is an instance of another FieldBase subclass. It supports adding,
    clearing, and iterating over list items, as well as processing form data for the entire list.

    Example:
    ```python
        class MyModel(BaseModel):
            my_list: t.List[str] = ZFieldInfo(
                FieldList(StringField()), default=["value1", "value2"]
            )
    ```
    Example 2:
    ```python
        class MyModel(BaseModel):
            my_list: t.List[str] = Field(default=["value1", "value2"])
    ```

    Example 3:
    ```python
        class MyModel(BaseModel):
            my_list: t.List[Enum]
    ```

    Example 3:
    ```python
        my_list = FieldList(StringField())
        my_list = FieldList(EnumField(Enum))
    ```

    Note:
        - The list supports dynamic addition and removal of items.
        - It handles nested form data processing for each item in the list.
        - The class provides methods for managing the list's contents and rendering.
    """

    type = "list"
    widgetType: t.Type[FieldWidget] = FieldListWidget

    def __init__(
        self,
        field: FieldBase,
        **kwargs,
    ) -> None:
        # base field type for items in the list
        self._base_field = field
        self._base_field.name = "listItem[placeholder]"
        self._base_field.validate_setup()

        if t.TYPE_CHECKING:  # pragma: no cover
            base_field_type = self._base_field.python_type
            self._items: t.List[base_field_type]

        # list of field instances
        self._items = []

        super().__init__(**kwargs)

    @property
    def base_field(self) -> FieldBase:
        return self._base_field

    def _get_new_field_at(self, alias: str) -> FieldBase:
        """
        Create a new instance of the base field with the given alias.

        Args:
            alias (str): The alias for the new field instance.

        Returns:
            FieldBase: A new instance of the base field type.
        """
        kwargs = dict(getattr(self._base_field, ZFORM_FIELD_ATTRIBUTES, {}))
        kwargs.update(alias=alias, name=self.name)
        instance = self._base_field.create_from_annotation(
            annotation=get_form_field_python_type(self._base_field), **kwargs
        )
        return instance

    def validate_setup(self) -> None:
        """
        Ensure the field's annotation is a Sequence type.

        Raises:
            AssertionError: If the annotation is not a Sequence.
        """
        assert annotation_is_sequence(
            self.model_field.type_
        ), "Annotation must be a Sequence"

    @property
    def items(self) -> t.List[FieldBase]:
        """
        Get the list of items in the field.

        Returns:
            List[FieldBase]: The list of items in the field.
        """
        return list(self._items)

    @property
    def python_type(self) -> t.Type:
        """
        Get the Python type of the field.

        Returns:
            Type: The Python type representing a List of the base field's type.
        """
        return t.List[self._base_field.python_type]

    def process(
        self, data: t.Any, suppress_error: bool = True, **kwargs: t.Any
    ) -> None:
        """
        Process input data for the list field.

        Args:
            data (Any): The input data to process, expected to be a list.
            suppress_error (bool): Whether to suppress validation errors.
        """
        self._items.clear()

        if isinstance(data, list):
            for item_data in data:
                self.add_item().process(item_data, suppress_error=suppress_error)

    async def process_form_data(
        self, ctx: IExecutionContext, body: t.Any, **kwargs: t.Any
    ) -> ResolverResult:
        """
        Process form data for the entire list of fields.

        Args:
            ctx (IExecutionContext): The execution context.
            body (Any): The form body data.

        Returns:
            ResolverResult: The result of processing the form data for all list items.
        """
        form_data = await ctx.switch_to_http_connection().get_request().form()
        indices = self._extra_indices(form_data)

        values = []
        raw_data = {}
        errors = {}

        for index in indices:
            key = f"{self.id}.{index}"
            field = self._get_new_field_at(key)

            self._items.append(field)
            res = await field.process_form_data(ctx, body=body)

            values.append(res.data[self.name] if res.data else None)
            raw_data[str(index)] = res.raw_data[self.name]

            if res.errors:
                errors.setdefault(self.model_field.alias, []).extend(res.errors)

        if not values and self.default:
            values = self.default

        if not values and not self.default:
            errors.setdefault(self.model_field.alias, []).append(
                dict(
                    loc=(self.model_field.alias,),
                    msg="Input must be a list",
                    type="type_error",
                )
            )

        return ResolverResult(
            data={self.model_field.alias: values or self.default},
            errors=errors.get(self.model_field.alias, []),
            raw_data={self.model_field.alias: raw_data},
        )

    def _extra_indices(self, form_data: FormData) -> t.List[int]:
        """
        Extract and sort the indices from form data keys.

        Args:
            form_data (FormData): The form data to extract indices from.

        Returns:
            List[int]: A sorted list of indices found in the form data keys.
        """
        return sorted(
            {
                int(name[len(self.id) + 1 :].split(".", maxsplit=1)[0])
                for name in form_data
                if name.startswith(self.id)
                and name[len(self.id) + 1 :].split(".", maxsplit=1)[0].isdigit()
            }
        )

    def clear(self) -> None:
        """
        Clear all items from the list.
        """
        super().clear()
        self._items.clear()

    def add_item(self) -> FieldBase:
        """
        Add a new item to the list and return it.

        Returns:
            FieldBase: The newly added field instance.
        """
        index = len(self._items)
        new_field = self._get_new_field_at(f"{self.id}.{index}")

        self._items.append(new_field)
        return new_field

    def __iter__(self) -> t.Iterator[FieldBase]:
        """
        Iterate over the list items, ensuring at least one item exists.

        Returns:
            Iterator[FieldBase]: An iterator over the list items.
        """
        if len(self._items) == 0:
            self.add_item()

        return iter(self._items)
