import datetime
from zform.fields.dates import (
    TimeZoneField,
    DateTimeLocalField,
    DateTimeField,
    DateField,
    TimeField,
)


class TestTimeZoneField:
    def test_default_timezones(self):
        field = TimeZoneField(name="timezone")
        assert len(field._choices) > 0
        assert all(isinstance(choice, tuple) for choice in field._choices)

    def test_custom_timezones(self):
        custom_zones = [
            ("UTC", "Coordinated Universal Time"),
            ("GMT", "Greenwich Mean Time"),
        ]
        field = TimeZoneField(name="timezone", time_zones=custom_zones)
        assert field._choices == custom_zones

    def test_render(self):
        field = TimeZoneField(name="timezone", required=True)
        rendered = str(field())
        assert '<select class="" id="timezone" name="timezone" required>' in rendered
        assert "<option value='UTC'>UTC</option>" in rendered
        assert "<option value='GMT'>GMT</option>" in rendered


class TestDateTimeLocalField:
    def test_type(self):
        field = DateTimeLocalField(name="datetime_local")
        assert field.type == "datetime-local"

    def test_data_alt_format(self):
        field = DateTimeLocalField(name="datetime_local", data_alt_format="Y-m-d H:i:S")
        assert field.attrs["data_alt_format"] == "Y-m-d H:i:S"

    def test_python_type(self):
        field = DateTimeLocalField(name="datetime_local")
        assert field.python_type == datetime.datetime

    def test_render(self):
        field = DateTimeLocalField(name="datetime_local")
        rendered = field()
        assert 'type="datetime-local"' in rendered
        assert 'name="datetime_local"' in rendered
        assert 'id="datetime_local"' in rendered


class TestDateTimeField:
    def test_type(self):
        field = DateTimeField(name="datetime")
        assert field.type == "datetime"

    def test_python_type(self):
        field = DateTimeField(name="datetime")
        assert field.python_type == datetime.datetime

    def test_render(self):
        field = DateTimeField(name="datetime")
        rendered = field()
        assert 'type="datetime"' in rendered
        assert 'name="datetime"' in rendered
        assert 'id="datetime"' in rendered


class TestDateField:
    def test_type(self):
        field = DateField(name="date")
        assert field.type == "date"

    def test_python_type(self):
        field = DateField(name="date")
        assert field.python_type == datetime.date

    def test_render(self):
        field = DateField(name="date")
        rendered = field()
        assert 'type="date"' in rendered
        assert 'name="date"' in rendered
        assert 'id="date"' in rendered


class TestTimeField:
    def test_type(self):
        field = TimeField(name="time")
        assert field.type == "time"

    def test_data_alt_format(self):
        field = TimeField(name="time", data_alt_format="H:i")
        assert field.attrs["data_alt_format"] == "H:i"

    def test_python_type(self):
        field = TimeField(name="time")
        assert field.python_type == datetime.time

    def test_render(self):
        field = TimeField(name="time").rebuild()
        rendered = field()
        assert 'type="time"' in rendered
        assert 'name="time"' in rendered
        assert 'id="time"' in rendered
