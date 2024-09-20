import base64
import tempfile

import pytest
from mocks import MockContext


@pytest.fixture
def create_context():
    def _context(data):
        return MockContext(data)

    return _context


@pytest.fixture
def fake_valid_image_content():
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAAHNJREFUKFOdkLEKwCAMRM/JwUFwdPb"
        "/v8RPEDcdBQcHJyUt0hQ6hGY6Li8XEhVjXM45aK3xVXNOtNagcs6LRAgB1toX23tHSgkUpEopyxhzGRw"
        "+EHljjBv03oM3KJYP1lofkJoHJs3T/4Gi1aJjxO+RPnwDur2EF1gNZukAAAAASUVORK5CYII="
    )


@pytest.fixture
def fake_valid_image(fake_valid_image_content):
    file = tempfile.NamedTemporaryFile(suffix=".png")
    data = fake_valid_image_content
    file.write(data)
    file.seek(0)
    return file
