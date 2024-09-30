import typing as t
from .base import FieldBase
from .widget import FieldWidget


class BooleanFieldWidget(FieldWidget):
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

    def get_html_attrs(self, **extra_attrs: t.Any) -> t.Dict:
        attrs = super().get_html_attrs(**extra_attrs)
        attrs.pop("value", None)
        return attrs

    def get_render_context(self) -> t.Dict:
        ctx = super().get_render_context()
        ctx.update(data=self.field.data)
        return ctx


class BooleanField(FieldBase):
    type: str = "checkbox"
    widgetType: t.Type[FieldWidget] = BooleanFieldWidget

    @property
    def python_type(self) -> t.Type:
        return bool
