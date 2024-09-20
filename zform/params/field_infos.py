import typing as t

from ellar.common.constants import MULTI_RESOLVER_FORM_GROUPED_KEY, MULTI_RESOLVER_KEY
from ellar.common.exceptions import ImproperConfiguration
from ellar.common.params import IRouteParameterResolver
from ellar.common.params.params import FormFieldInfo
from ellar.common.params.resolvers import BaseRouteParameterResolver
from ellar.pydantic import ModelField, FieldInfo
from zform.fields.base import FieldBase
from zform.params.resolvers import ZFormResolver


class ZFormInfo(FormFieldInfo):
    """
    ZFormInfo is a specialized FormFieldInfo class for handling ZForm fields in Ellar.

    This class extends the functionality of FormFieldInfo to work specifically
    with ZForm fields in the Ellar framework. It provides custom logic for
    creating resolvers, handling multiple resolvers, and managing ZForm-specific
    configurations.

    ZFormInfo is responsible for:
    - Creating and managing ZForm fields
    - Enforcing ZForm-specific rules and configurations
    - Integrating with Ellar's form handling system

    This class plays a crucial role in the ZForm ecosystem, bridging the gap
    between Ellar's form handling and ZForm's custom field implementations.

    Note: The actual form processing and validation occur in `ZFormManager`, which is
    instantiated automatically by Ellar during request processing and destroyed at
    the end of the request.
    """

    def create_resolver(
        self, model_field: ModelField
    ) -> t.Union[BaseRouteParameterResolver, IRouteParameterResolver]:
        multiple_resolvers = model_field.field_info.json_schema_extra.pop(  # type:ignore[union-attr]
            MULTI_RESOLVER_KEY, []
        )
        is_grouped = model_field.field_info.json_schema_extra.pop(  # type:ignore[union-attr]
            MULTI_RESOLVER_FORM_GROUPED_KEY, False
        )

        if multiple_resolvers:
            resolver = self.bulk_resolver(
                model_field=model_field,
                resolvers=multiple_resolvers,  # type:ignore[arg-type]
                is_grouped=is_grouped,
            )
            if self._ellar_body:
                if (
                    len(multiple_resolvers) > 1
                    and len(
                        [
                            item
                            for item in multiple_resolvers
                            if isinstance(item, ZFormResolver)
                        ]
                    )
                    > 1
                ):
                    raise ImproperConfiguration("Only one ZForm[Schema] is allow")
                # TODO: raise exception if resolver body of type Zform exist more than once
                return resolver
            # create ZForm Object
            return ZFormResolver(model_field, fields=multiple_resolvers)

        raise ImproperConfiguration("Can only resolve multiple resolvers")


class ZFieldInfo(FieldInfo):
    """
    A custom field info class for ZForm fields.

    This class extends Pydantic's FieldInfo to include ZForm-specific functionality.

    Attributes:
        zform_field (FieldBase): The underlying ZForm field instance.
    """

    def __init__(
        self,
        zform_field: t.Union[t.Type[FieldBase], FieldBase],
        default: t.Any = ...,
        **kwargs,
    ):
        super().__init__(default=default, **kwargs)
        self.zform_field = (
            zform_field if isinstance(zform_field, FieldBase) else zform_field()
        )
