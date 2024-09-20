from datetime import datetime
from enum import IntEnum

from ellar.common import (
    Inject,
    ModuleRouter,
    Serializer,
    serialize_object,
)
from ellar.core.connection import Request
from ellar.openapi import OpenAPIDocumentBuilder
from ellar.pydantic import Field
from ellar.testing import Test
from zform import ZForm

mr = ModuleRouter("")


class Range(IntEnum):
    TWENTY = 20
    FIFTY = 50
    TWO_HUNDRED = 200


class FilterT(Serializer):
    to_datetime: datetime = Field(validation_alias="to")
    from_datetime: datetime = Field(validation_alias="from")
    range: Range = Range.TWENTY


@mr.post("/zform-schema")
def zform_params_schema(
    request: Inject[Request],
    form: ZForm[FilterT],
):
    if form.validate():
        return form.value.model_dump()
    return form.errors


test_module = Test.create_test_module(routers=(mr,))
app = test_module.create_application()


def test_request():
    client = test_module.get_test_client()
    response = client.post(
        "/zform-schema", data={"from": "1", "to": "2", "range": "20"}
    )
    assert response.json() == {
        "to_datetime": "1970-01-01T00:00:02Z",
        "from_datetime": "1970-01-01T00:00:01Z",
        "range": 20,
    }

    response = client.post(
        "/zform-schema", data={"from": "1", "to": "2", "range": "100"}
    )
    assert response.status_code == 200
    json = response.json()
    assert json == {"range": ["Input should be 20, 50 or 200"]}


def test_schema():
    document = serialize_object(OpenAPIDocumentBuilder().build_document(app))
    params = document["paths"]["/zform-schema"]["post"]["requestBody"]

    assert params == {
        "content": {
            "application/x-www-form-urlencoded": {
                "schema": {
                    "$ref": "#/components/schemas/body_zform_params_schema_zform_schema_post"
                }
            }
        },
        "required": True,
    }

    schema = document["components"]["schemas"][
        "body_zform_params_schema_zform_schema_post"
    ]
    assert schema == {
        "properties": {
            "form": {
                "$ref": "#/components/schemas/FilterT",
                "embed": True,
                "validate_on_write": True,
            }
        },
        "required": ["form"],
        "title": "body_zform_params_schema_zform_schema_post",
        "type": "object",
    }
