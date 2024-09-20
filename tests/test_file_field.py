import pytest
import typing as t

from starlette.datastructures import Headers

from ellar.common.datastructures import UploadFile, ContentFile
from pydantic import BaseModel
from zform.fields import FileField, ImageFileField, FieldList
from zform.form import FormManager
from zform import ZFieldInfo


def test_file_field_rendering():
    field = FileField(name="document")
    rendered = field()

    assert 'type="file"' in rendered
    assert 'name="document"' in rendered
    assert 'id="document"' in rendered


def test_file_field_multiple():
    field = FileField(name="documents", multiple=True)
    rendered = field()

    assert 'type="file"' in rendered
    assert 'name="documents"' in rendered
    assert "multiple" in rendered


def test_file_field_accept():
    field = FileField(name="image", accept="image/*")
    rendered = field()

    assert 'type="file"' in rendered
    assert 'accept="image/*"' in rendered


class FileUploadModel(BaseModel):
    document: UploadFile
    images: t.List[UploadFile] = ZFieldInfo(FileField)


class FileUploadForm(BaseModel):
    document: UploadFile
    images: t.List[UploadFile] = ZFieldInfo(FileField())


def test_pydantic_model_for_list__picks_FieldList():
    class Model(BaseModel):
        files: t.List[UploadFile]

    form = FormManager.from_schema(Model)
    assert isinstance(form.get_field("files"), FieldList)


def test_file_field_pydantic_integration():
    form = FormManager.from_schema(FileUploadModel)

    assert isinstance(form.get_field("document"), FileField)
    assert isinstance(form.get_field("images"), FileField)

    assert form.get_field("images").multiple is True
    assert form.get_field("document").multiple is False


@pytest.mark.asyncio
async def test_file_field_processing(create_context):
    form = FormManager.from_schema(
        FileUploadModel,
        ctx=create_context(
            {
                "document": ContentFile(b"test content", name="test.txt"),
                "images": [
                    ContentFile(b"test content 2", name="test2.txt"),
                    ContentFile(b"test content 3", name="test3.txt"),
                ],
            }
        ),
    )
    assert form.validate()

    assert form.value.document.filename == "test.txt"
    assert form.value.document.content_type == "text/plain"
    assert len(form.value.images) == 2
    assert all(isinstance(file, UploadFile) for file in form.value.images)


def test_file_field_clear():
    field = FileField(name="document")
    field.process(ContentFile(b"test content", name="test.txt"))

    assert field.value is not None

    field.clear()

    assert field.value is None
    assert field.data is None

    assert field.raw_data is None
    assert field.errors == []


def test_image_file_field_rendering():
    field = ImageFileField(name="profile_picture")
    rendered = field()

    assert 'type="file"' in rendered
    assert 'name="profile_picture"' in rendered
    assert 'id="profile_picture"' in rendered
    assert 'accept="image/*"' in rendered


def test_image_file_field_custom_accept():
    field = ImageFileField(name="avatar", accept="image/png,image/jpeg")
    rendered = field()

    assert 'accept="image/png,image/jpeg"' in rendered


def test_image_file_field_multiple():
    field = ImageFileField(name="gallery", multiple=True)
    rendered = field()

    assert 'type="file"' in rendered
    assert 'name="gallery"' in rendered
    assert "multiple" in rendered
    assert 'accept="image/*"' in rendered


class ImageUploadModel(BaseModel):
    profile_picture: UploadFile = ZFieldInfo(ImageFileField)
    gallery: t.List[UploadFile] = ZFieldInfo(ImageFileField())


def test_image_file_field_pydantic_integration(create_context):
    form = FormManager.from_schema(ImageUploadModel)

    assert isinstance(form.get_field("profile_picture"), ImageFileField)
    assert isinstance(form.get_field("gallery"), ImageFileField)

    assert form.get_field("profile_picture").multiple is False
    assert form.get_field("gallery").multiple is True


def test_image_file_field_processing(create_context, fake_valid_image):
    image = UploadFile(
        filename=fake_valid_image.name,
        headers=Headers({"content-type": "image/png"}),
        file=fake_valid_image.file,
    )
    form = FormManager.from_schema(
        ImageUploadModel,
        ctx=create_context({"profile_picture": image, "gallery": [image, image]}),
    )
    assert form.validate()

    assert form.value.profile_picture.filename == image.filename
    assert form.value.profile_picture.content_type == image.headers["content-type"]

    assert len(form.value.gallery) == 2
    assert all(isinstance(file, UploadFile) for file in form.value.gallery)


def test_image_file_field_label():
    field = ImageFileField(name="profile_picture", label="Profile Picture")
    rendered = field.label()

    assert "Profile Picture" in rendered


def test_image_file_field_help_text():
    field = ImageFileField(name="profile_picture", help_text="Upload a profile picture")
    rendered = field()

    assert "Upload a profile picture" in rendered
