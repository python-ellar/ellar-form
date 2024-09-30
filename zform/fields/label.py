import typing as t
import jinja2
from zform.fields.utils import html_params
from markupsafe import Markup


class FormLabel:
    """
    An HTML form label.

    Attributes:
        field_id (str): The ID of the associated form field.
        text (str): The text content of the label.
    """

    # language=html
    template = """
        <label {{attrs}}>{{text}}</label>
    """

    def __init__(self, field_id: t.Optional[str], text: t.Optional[str]):
        self.field_id = field_id
        self.text = text

    def __html__(self) -> str:
        """
        Return the HTML representation of the label.

        Returns:
            str: The HTML string of the label.
        """
        return self()

    def get_html_attrs(self, **extra_attrs: t.Any) -> t.Dict[str, t.Any]:
        extra_attrs.update(
            {
                "for": self.field_id,
            }
        )
        return extra_attrs

    def get_render_context(self) -> t.Dict[str, t.Any]:
        return {
            "text": self.text,
        }

    def __call__(self, **kwargs) -> str:
        """
        Render the label as an HTML string.

        Args:
            **kwargs: Additional HTML attributes for the label.

        Returns:
            str: The rendered HTML string of the label.
        """
        attrs = self.get_html_attrs(**kwargs)
        ctx = self.get_render_context()
        content = jinja2.Template(self.template).render(
            **ctx,
            attrs=html_params(**attrs),
        )
        return Markup(content)
