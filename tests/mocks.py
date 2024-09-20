from starlette.datastructures import FormData


def _convert_dict_to_list_of_tuples(data: dict, prefix: str = ""):
    result = []
    for key, value in data.items():
        if isinstance(value, (list, set, tuple)):
            for item in value:
                result.append((f"{prefix}{key}", item))
        elif isinstance(value, dict):
            result.extend(_convert_dict_to_list_of_tuples(value, f"{prefix}{key}."))
        else:
            result.append((f"{prefix}{key}", value))
    return result


class MockRequest:
    def __init__(self, data: dict) -> None:
        self._data = data

    async def form(self):
        data = _convert_dict_to_list_of_tuples(self._data)
        return FormData(data)

    @property
    def method(self):
        return "POST"


class MockHTTPConnection:
    def __init__(self, data: dict) -> None:
        self._data = data

    def get_request(self):
        return MockRequest(self._data)


class MockContext:
    def __init__(self, data: dict) -> None:
        self._data = data

    def switch_to_http_connection(self):
        return MockHTTPConnection(self._data)
