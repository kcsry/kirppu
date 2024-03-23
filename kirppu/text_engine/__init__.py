import mistune
from django.template.context import Context, RequestContext

from .alert_box import AlertBoxPlugin
from .monolithic import EmailPlugin, GlyphPlugin
from .template import TemplatePlugin

__all__ = [
    "mark_down",
]


def mark_down(text, context: RequestContext | Context | dict | None = None) -> str:
    m = mistune.create_markdown(
        escape=False,
        plugins=[
            "strikethrough",
            "footnotes",
            "table",
            EmailPlugin(),
            GlyphPlugin(),
            AlertBoxPlugin(),
            TemplatePlugin(context),
        ],
    )
    return m(text)
