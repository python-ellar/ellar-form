"""Traditional Form package integrated with Pydantic models for an Ellar python web framework"""

__version__ = "0.1.2"
import typing as t

from typing_extensions import Annotated

from .form import FormManager
from .params.decorators import ZFieldDecorator as ZFieldInfo

__all__ = ["ZForm", "ZFieldInfo", "FormManager"]

if t.TYPE_CHECKING:  # pragma: no cover
    from .params.decorators import ZFormDecorator

    # mypy cheats
    T = t.TypeVar("T")

    ZForm = Annotated[FormManager[T], ZFormDecorator()]

else:
    from ellar.utils.functional import LazyStrImport
    from ellar.common.params.decorators import _ParamShortcut
    from ellar.common.params.args.base import add_resolver_generator
    from zform.params.resolver_gen import ZFormResolverGenerator
    from zform.params.field_infos import ZFormInfo

    # add the resolver generator to the registry
    add_resolver_generator(ZFormInfo, ZFormResolverGenerator)
    ZForm = _ParamShortcut(LazyStrImport("zform.params.decorators:ZFormDecorator"))
