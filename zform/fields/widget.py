import typing as t
import jinja2
from markupsafe import Markup
from zform.fields.utils import html_params

if t.TYPE_CHECKING:  # pragma: no cover
    from zform.fields.base import FieldBase


class FieldWidget:
    field: "FieldBase"
    """
    Widget class for rendering form fields.

    Attributes:
        field (FieldBase): The associated form field.
    """

    # language=HTML
    template = """
        {% if help_text %}
            <div>
              <input type="{{type}}" {{attrs}}>
              <small>{{help_text}}</small>
            </div>
        {% else %}
            <input type="{{type}}" {{attrs}}>
        {% endif %}
    """

    def __init__(self, field: "FieldBase"):
        """
        Initialize the widget with the associated form field.

        Args:
            field (FieldBase): The associated form field.
        """
        self.field = field

    def get_html_attrs(self, **extra_attrs: t.Any) -> t.Dict:
        """
        Get the HTML attributes of the field.
        Returns:
            t.Dict: The HTML attributes of the field.
        """
        extra_attrs.update(
            {
                "required": self.field.model_field.field_info.is_required(),
                "title": extra_attrs.get(
                    "title", self.field.model_field.field_info.title
                ),
                "value": self.field.data,
            }
        )
        return dict(self.field.attrs, **extra_attrs)

    def get_render_context(self) -> t.Dict:
        """
        Get the render context of the field.

        Returns:
            t.Dict: The render context of the field.
        """
        return {
            "field": self.field,
            "help_text": self.field.help_text,
            "type": t.cast(t.Any, self.field.type),
        }

    def render(self, **kwargs: t.Any) -> str:
        """
        Render the field as an HTML input element.

        Args:
            **attrs: Additional HTML attributes for the input element.

        Returns:
            str: The rendered HTML string of the input element.
        """
        extra_context = kwargs.pop("context", {})

        kwargs.update(
            name=self.field.model_field.alias,
            value=self.field.data,
            required=self.field.required,
        )
        kwargs.setdefault("id", self.field.id)

        attrs = self.get_html_attrs(**kwargs)
        ctx = self.get_render_context()
        ctx.update(extra_context)

        content = jinja2.Template(self.get_template_string()).render(
            attrs=html_params(**attrs),
            **ctx,
        )
        return Markup(content)

    def render_as_p(self, **kwargs) -> str:
        """
        Render the field as a paragraph.

        Args:
            **kwargs: Additional HTML attributes for the paragraph.

        Returns:
            str: The rendered HTML string of the paragraph.
        """
        return self.render(as_paragraph=True, **kwargs)

    def render_as_table(self, **kwargs) -> str:
        """
        Render the field as a table row.

        Args:
            **kwargs: Additional HTML attributes for the table row.

        Returns:
            str: The rendered HTML string of the table row.
        """
        return self.render(as_table=True, **kwargs)

    def get_template_string(self) -> str:
        """
        Get the template string for the field.

        Returns:
            str: The template string for the field.
        """
        return self.template
