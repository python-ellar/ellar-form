import typing as t
from ellar.common import IExecutionContext
from ellar.core import current_injector
from ellar.pydantic import ModelField, create_model_field
from ellar.reflect import reflect
from ellar.threading import execute_coroutine
from zform.constants import ZFORM_MANAGER_CREATE_PARAMETERS
from zform.fields.base import FieldBase
from zform.fields.utils import format_errors

T = t.TypeVar("T")

_DICT_MODEL_FIELD = create_model_field(name="Form", type_=dict)


class FormManager(t.Generic[T]):
    """
    A form management class for processing and validating form data.

    This class manages form fields, handles data population, validation,
    and error tracking. It works with Ellar's execution context and
    Pydantic model fields.

    During request processing, FormManager is instantiated automatically
    by Ellar and request context it along with the ZForm fields for processing and at the end of the request,
    it is automatically destroyed and its data is discarded.

    It is important to note that FormManager, defers input field validation
    and processing until the `form.validate()` method is called. And after validation,
    the form data is automatically populated into the Pydantic model field.

    Attributes:
        errors (dict): Stores validation errors.
        data (dict): Processed form data.
        obj (Any): Object used for populating form data.
        value (Any): Validated form value.
        model_field (ModelField): Pydantic model field for the form.

    Args:
        ctx (IExecutionContext): Ellar execution context.
        resolvers (List[Union[Any, FormFieldBase]]): List of form field resolvers.
        model_field (ModelField): Pydantic model field for the form.
        body (Any, optional): Request body data.
        validate_on_write (bool, optional): Whether to validate on write operations. Defaults to True.

    Example:
        ```python
        from pydantic import BaseModel, EmailStr
        from ellar.common import ModuleRouter, render_template
        from zform import ZForm

        class UserFormModel(BaseModel):
            password: str
            email: EmailStr

        router = ModuleRouter('/')

        @router.http_route("login", methods=["post", "get"])
        def login(form: ZForm[UserFormModel]):
            if form.validate():
                return render_template("successful.html")

            return render_template("login.html", form=form)

        # inline usage
        @router.http_route("login/another", methods=["post", "get"])
        async def login_another(ctx: IExecutionContext):
            form = ZFormManager.from_schema(UserFormModel, ctx=ctx)

            if await form.validate():
                return render_template("successful.html")

            return render_template("login.html", form=form)
        ```

    This example demonstrates how to use ZFormManager with a Pydantic model
    to handle form validation in an Ellar route handler.
    """

    value: t.Optional[T]

    # _instances: WeakValueDictionary = WeakValueDictionary()
    # _ref_counts: t.Dict[t.Any, int] = {}
    #
    # def __new__(cls, *args, **kwargs):
    #     # Convert mutable types to immutable ones for hashing
    #     hashable_args = tuple(
    #         tuple(arg) if isinstance(arg, list) else arg for arg in args
    #     )
    #     hashable_kwargs = frozenset(
    #         (k, tuple(v) if isinstance(v, list) else v) for k, v in kwargs.items()
    #     )
    #
    #     key = (cls, hashable_args, hashable_kwargs)
    #
    #     instance = cls._instances.get(key)
    #     if instance is None:
    #         instance = super().__new__(cls, *args, **kwargs)
    #         cls._instances[key] = instance
    #         cls._ref_counts[key] = 0
    #     cls._ref_counts[key] += 1
    #     return instance

    # def __new__(cls, *args: t.Any, **kwargs: t.Any) -> "FormManager[T]":
    #     key = secrets.token_urlsafe(32)
    #
    #     instance = super().__new__(cls, *args, **kwargs)
    #     cls._instances[key] = instance
    #
    #     return instance

    # __slots__ = (
    #     "__model_field",
    #     "errors",
    #     "__fields",
    #     "_value",
    #     "_body",
    #     "_data",
    #     "_ctx",
    #     "_obj",
    #     "_validate_on_write",
    #     "raw_data",
    # )

    def __init__(
        self,
        resolvers: t.List[t.Union[t.Any, "FieldBase"]],
        model_field: ModelField,
        body: t.Optional[t.Any] = None,
        ctx: t.Optional[IExecutionContext] = None,
        validate_on_write: bool = True,
    ) -> None:
        self.__model_field = model_field
        self.errors = {}

        self._value: t.Optional[T] = None
        self._body = body
        self._ctx = ctx

        self._data: t.Optional[t.Dict] = None
        self._obj: t.Optional[t.Any] = None
        self._validate_on_write = validate_on_write

        self.raw_data: t.Optional[t.Dict] = None

        self._fields: t.Dict[str, "FieldBase"] = {
            item.name: self._initialize_field(item) for item in resolvers
        }

    def _initialize_field(self, field: FieldBase) -> FieldBase:
        return field.load()

    def __del__(self):
        """
        Clears the field data when the form is destroyed.
        """
        self.clear()
        # key = next((k for k, v in self._instances.items() if v is self), None)
        # if key:
        #     self._ref_counts[key] -= 1
        #     if self._ref_counts[key] == 0:
        #         self.clear()
        #         del self._instances[key]
        #         del self._ref_counts[key]

    def clear(self):
        """
        Explicitly clear the field data.
        """
        for field in self:
            field.clear()

    @property
    def data(self) -> t.Optional[t.Dict]:
        """
        Returns the processed form data.

        Returns:
            Optional[Dict]: The processed form data.
        """
        return self._data

    @property
    def obj(self) -> t.Optional[t.Any]:
        """
        Returns the object used for populating form data.

        Returns:
            Optional[Any]: The object used for populating form data.
        """
        return self._obj

    @property
    def value(self) -> t.Optional[T]:
        """
        Returns the validated form value.

        Returns:
            Optional[T]: The validated form value.
        """
        return self._value

    @property
    def model_field(self) -> ModelField:
        """
        Returns the Pydantic model field for the form.

        Returns:
            ModelField: The Pydantic model field for the form.
        """
        return self.__model_field

    def populate_form(
        self,
        obj: t.Any = None,
        data: t.Dict = None,
        field_context: t.Optional[t.Dict[str, t.Any]] = None,
        **kwargs: t.Any,
    ) -> None:
        """
        Populates the form with data from an object or dictionary.

        Args:
            obj (Any, optional): The object to populate the form with.
            data (Dict, optional): The dictionary to populate the form with.
            field_context (Dict[str, Any], optional): The field context for form population. Defaults to None.
            **kwargs (Any): Additional keyword arguments for form population.
        """
        self._obj = obj
        self._data = data
        field_context = field_context or {}

        kwargs = dict(data or {}, **kwargs)

        for name, field in self._fields.items():
            # TODO: for inline filters
            if obj is not None and hasattr(obj, name):
                data = getattr(obj, name)
            elif name in kwargs:
                data = kwargs[name]
            else:
                data = None

            field.process(data, suppress_error=True, field_context=field_context)

    def validate(self) -> bool:
        """
        Validates the form data synchronously.

        Returns:
            bool: True if the form data is valid, False otherwise.
        """
        return execute_coroutine(self.validate_async())

    async def validate_async(self) -> bool:
        """
        Validates the form data asynchronously.

        Returns:
            bool: True if the form data is valid, False otherwise.
        """
        ctx = self._ctx or current_injector.get(IExecutionContext)
        assert ctx is not None, "Execution context is required"

        method = ctx.switch_to_http_connection().get_request().method.lower()

        if self._validate_on_write and method not in ["post", "patch", "put"]:
            return False

        await self.process_form(ctx, body=self._body)
        return len(self.errors) == 0

    async def process_form(
        self,
        ctx: IExecutionContext,
        body: t.Optional[t.Any] = None,
    ) -> None:
        """
        Processes the form fields and populates the form data and errors.
        """
        data, errors, self.raw_data = await self._process_form_fields_data(
            ctx, body=body, by_alias=True
        )
        if not errors:
            v_, errors = self.model_field.validate(data, {}, loc=("form",))

            if not errors:
                self._value = v_

            if errors:
                self.errors = {"form": format_errors(errors)}
            return
        self.errors = errors

    async def _process_form_fields_data(
        self, ctx: IExecutionContext, body: t.Any, by_alias: bool = False
    ) -> t.Tuple[t.Dict, t.Dict, t.Dict]:
        """
        Processes the form data and returns the values, errors, and raw data.

        Args:
            ctx (IExecutionContext): The execution context.
            body (Any): The request body data.
            by_alias (bool, optional): Whether to use field aliases. Defaults to False.

        Returns:
            Tuple[Dict, Dict, Dict]: The processed values, errors, and raw data.
        """
        values: t.Dict[str, t.Any] = {}
        errors = {}
        raw_data = {}

        for field in self:
            res_ = await field.process_form_data(ctx=ctx, body=body)
            if res_.data:
                value = (
                    res_.data
                    if not by_alias
                    else {field.model_field.alias: res_.data[field.model_field.name]}
                )
                values.update(value)
            if res_.errors:
                errors.setdefault(field.model_field.name, []).extend(
                    format_errors(res_.errors)
                )
            raw_data.update(res_.raw_data)
        return values, errors, raw_data

    def populate_obj(self, obj):
        """
        Populates the given object with form data.

        Args:
            obj (Any): The object to populate with form data.
        """

    def __iter__(self) -> t.Iterator[FieldBase]:
        """
        Returns an iterator over the form fields.

        Returns:
            Iterator[FieldBase]: An iterator over the form fields.
        """
        return iter(self._fields.values())

    def __contains__(self, item: t.Any) -> bool:
        """
        Checks if the form contains the specified field.

        Args:
            item (Any): The field to check.

        Returns:
            bool: True if the form contains the field, False otherwise.
        """
        return item in self._fields

    def get_field(self, field_name: str) -> FieldBase:
        """
        Returns the form field with the specified name.

        Args:
            field_name (str): The name of the form field.

        Returns:
            FieldBase: The form field with the specified name.
        """
        return self._fields[field_name]

    @classmethod
    def from_schema(
        cls,
        schema: t.Type[T],
        *,
        ctx: t.Optional[IExecutionContext] = None,
        validate_on_write: bool = True,
        **kwargs: t.Any,
    ) -> "FormManager[T]":
        """
        Creates a FormManager instance from a Pydantic schema.

        Args:
            schema (Type[T]): The Pydantic schema to create the FormManager from.
            ctx (IExecutionContext, optional): The execution context. Defaults to None.
            validate_on_write (bool, optional): Whether to validate on write operations. Defaults to True.
            **kwargs (Any): Additional keyword arguments for the FormManager.

        Returns:
            FormManager: A FormManager instance created from the Pydantic schema.
        """
        from zform.params.resolver_gen import generate_fields_from_schema

        # Check if the FormManager process for this schema has already been created
        init_parameters = reflect.get_metadata(ZFORM_MANAGER_CREATE_PARAMETERS, schema)
        if init_parameters:
            return cls(
                **init_parameters,
                ctx=ctx,
                validate_on_write=validate_on_write,
            )

        form_fields = kwargs.get("resolvers", generate_fields_from_schema(schema))
        model_field = kwargs.get(
            "model_field",
            create_model_field(name="Form", type_=schema),
        )

        kwargs.update({"resolvers": form_fields, "model_field": model_field})

        # Cache the resolvers and model field for later use
        reflect.define_metadata(ZFORM_MANAGER_CREATE_PARAMETERS, dict(kwargs), schema)

        return cls(**kwargs, ctx=ctx, validate_on_write=validate_on_write)

    @classmethod
    def from_fields(
        cls,
        fields: t.List[FieldBase],
        ctx: t.Optional[IExecutionContext] = None,
        validate_on_write: bool = True,
    ) -> "FormManager[dict]":
        """
        Creates a FormManager instance from a list of FieldBase instances.

        Args:
            fields (List[FieldBase]): The list of FieldBase instances.
            ctx (IExecutionContext, optional): The execution context. Defaults to None.
            validate_on_write (bool, optional): Whether to validate on write operations. Defaults to True.

        Returns:
            FormManager: A FormManager instance created from the list of FieldBase instances.
        """
        return cls(
            resolvers=fields,
            model_field=_DICT_MODEL_FIELD,
            ctx=ctx,
            validate_on_write=validate_on_write,
        )
