import typing as t

from ellar.common import IExecutionContext
from ellar.common.params import IRouteParameterResolver
from ellar.common.params.resolvers.base import ResolverResult
from ellar.pydantic import ModelField
from zform.fields.base import FieldBase
from zform.form import FormManager


class ZFormResolver(IRouteParameterResolver):
    """
    Resolver for FormManager object in route parameters.

    This class is responsible for creating and resolving ZFormManager instances
    during request processing.

    Attributes:
        form_manager_type (Type[FormManager]): The FormManager class to be instantiated.

    Args:
        model_field (ModelField): The model field associated with this resolver.
        fields (List[ZFormFieldBase]): The list of zform fields to be used in the ZFormManager.

    Methods:
        resolve: Asynchronously resolves the ZFormManager instance during request processing.
        create_raw_data: Creates a dictionary with the raw form data.
    """

    form_manager_type: t.Type[FormManager] = FormManager

    def __init__(self, model_field: ModelField, fields: t.List["FieldBase"]) -> None:
        self.__model_field = model_field
        self.__fields = fields

    @property
    def model_field(self) -> ModelField:
        return self.__model_field

    def create_raw_data(self, data: t.Any) -> t.Dict:
        return {self.model_field.name: data}

    async def resolve(
        self,
        ctx: IExecutionContext,
        *args: t.Any,
        body: t.Optional[t.Any] = None,
        **kwargs: t.Any,
    ) -> t.Tuple:
        validate_on_write = self.model_field.field_info.json_schema_extra.get(  # type:ignore[union-attr]
            "validate_on_write", True
        )

        form_manager = self.form_manager_type(
            ctx=ctx,
            resolvers=self.__fields,
            model_field=self.model_field,
            body=body,
            validate_on_write=validate_on_write,
        )

        # instead of processing the model field, we create a new FormManager
        # instance and allow the user to manually trigger the validation by calling the .validate() method
        return ResolverResult(
            {self.model_field.name: form_manager},
            [],
            raw_data=self.create_raw_data(None),
        )
