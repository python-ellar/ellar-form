import typing as t
from .base import FieldBase


class BooleanField(FieldBase):
    type: str = "checkbox"

    # language=html
    template: str = """
        {% if help_text %}
            <div>
              <input {{ 'checked' if data else '' }} type="{{type}}" {{attrs}}>
              <small>{{help_text}}</small>
            </div>
        {% else %}
            <input {{ 'checked' if data else '' }} type="{{type}}" {{attrs}}>
        {% endif %}
    """

    @property
    def python_type(self) -> t.Type:
        return bool

    def get_render_context(self, attrs: t.Dict) -> t.Tuple[t.Dict, t.Dict]:
        data = attrs.pop("value", self.data)
        return attrs, dict(data=data)
