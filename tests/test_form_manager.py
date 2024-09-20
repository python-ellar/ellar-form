import pytest
from pydantic import BaseModel, EmailStr
from ellar.common import ModuleRouter
from ellar.testing import Test

from zform import ZForm, FormManager
from zform.fields import StringField, EmailField


class UserFormModel(BaseModel):
    username: str
    email: EmailStr


@pytest.fixture
def user_form_manager():
    return FormManager.from_schema(UserFormModel)


def test_zform_manager_initialization(user_form_manager):
    assert isinstance(user_form_manager, FormManager)
    assert user_form_manager.model_field.type_ == UserFormModel
    assert len(list(user_form_manager)) == 2


def test_zform_manager_fields(user_form_manager):
    fields = list(user_form_manager)
    assert len(fields) == 2
    assert isinstance(fields[0], StringField)
    assert isinstance(fields[1], EmailField)


@pytest.mark.asyncio
async def test_zform_manager_validate_valid_data(create_context):
    ctx = create_context({"username": "testuser", "email": "test@example.com"})
    user_form_manager = FormManager.from_schema(UserFormModel, ctx=ctx)

    assert await user_form_manager.validate_async()
    assert user_form_manager.errors == {}

    assert user_form_manager.value == UserFormModel(
        username="testuser", email="test@example.com"
    )


@pytest.mark.asyncio
async def test_zform_manager_validate_invalid_data(create_context):
    ctx = create_context({"username": "testuser", "email": "invalid_email"})
    user_form_manager = FormManager.from_schema(
        UserFormModel,
        ctx=ctx,
    )

    is_valid = await user_form_manager.validate_async()

    assert not is_valid
    assert user_form_manager.errors["email"] == [
        "value is not a valid email address: An email address must have an @-sign."
    ]


def test_zform_manager_populate_form(user_form_manager):
    user_form_manager.populate_form(
        data={"username": "populateduser", "email": "populated@example.com"}
    )

    assert user_form_manager.data == {
        "username": "populateduser",
        "email": "populated@example.com",
    }


# Integration test with Ellar router
def test_zform_with_route_function_parameter():
    router = ModuleRouter("/")

    @router.http_route("/login", methods=["POST"])
    def login(form: ZForm[UserFormModel]):
        if form.validate():
            return {"status": "success", "data": form.value.dict()}
        return {"status": "error", "errors": form.errors}

    client = Test.create_test_module(routers=[router]).get_test_client()

    # Test with valid data
    response = client.post(
        "/login", data={"username": "testuser", "email": "test@example.com"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "data": {"username": "testuser", "email": "test@example.com"},
    }

    # Test with invalid data
    response = client.post(
        "/login", data={"username": "testuser", "email": "invalid_email"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert "errors" in response.json()


def test_zform_inline_instantiation():
    router = ModuleRouter("/")

    @router.http_route("/login", methods=["POST"])
    def login():
        form = FormManager.from_schema(UserFormModel)
        if form.validate():
            return {"status": "success", "data": form.value.dict()}
        return {"status": "error", "errors": form.errors}

    client = Test.create_test_module(routers=[router]).get_test_client()

    # Test with valid data
    response = client.post(
        "/login", data={"username": "testuser", "email": "test@example.com"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "data": {"username": "testuser", "email": "test@example.com"},
    }

    # Test with invalid data
    response = client.post(
        "/login", data={"username": "testuser", "email": "invalid_email"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert "errors" in response.json()
