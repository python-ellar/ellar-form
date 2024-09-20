import typing as t
from ellar.common.datastructures import UploadFile
from .base import FieldBase
from ellar.common.compatible import AttributeDict
from ellar.pydantic.utils import annotation_is_sequence


class FileField(FieldBase):
    type: str = "file"

    def __init__(
        self,
        accept: t.Optional[str] = None,
        field_info_args: t.Optional[t.Union[AttributeDict, t.Dict]] = None,
        multiple: bool = False,
        **kwargs: t.Any,
    ) -> None:
        self.multiple = multiple
        if field_info_args and field_info_args.annotation:
            self.multiple = annotation_is_sequence(field_info_args.annotation)

        super().__init__(
            field_info_args=field_info_args,
            multiple=self.multiple,
            accept=accept,
            **kwargs,
        )

    @property
    def python_type(self) -> t.Type:
        if self.multiple:
            return t.List[UploadFile]
        return UploadFile


class ImageFileField(FileField):
    def __init__(
        self,
        accept: str = "image/*",
        **kwargs: t.Any,
    ) -> None:
        super().__init__(accept=accept, **kwargs)
