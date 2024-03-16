# -*- coding: utf-8 -*-

import base64
import itertools
import re
import typing

import mistune
from django.template import loader
from django.template.context import Context, RequestContext


__all__ = [
    "mark_down",
]


# Also check customtexts_front.js that does the reverse with these.
EMAIL_CLASS = "yv8k02zi"
EMAIL_KEY = "yJrx6Rvvyn39u4La"


T = typing.TypeVar("T")


def remove_if_present(a_list: list[T], element: T):
    if element in a_list:
        a_list.remove(element)


class BasePlugin:
    NAME: str

    def __call__(self, md: mistune.Markdown) -> None:
        raise NotImplementedError

    @staticmethod
    def render(renderer: mistune.BaseRenderer, *args, **kwargs) -> str:
        # Function signature varies, see mistune.renderers.html.HTMLRenderer.render_token
        raise NotImplementedError


class InlinePlugin(BasePlugin):
    def register_inline(self, md: mistune.Markdown, name: str, pattern: str, before: str = "inline_html") -> None:
        md.inline.register(name, pattern, self.parse, before=before)
        if md.renderer:
            md.renderer.register(name, self.render)

    @classmethod
    def parse(cls, inline: mistune.InlineParser, m: re.Match, state: mistune.InlineState) -> int:
        raise NotImplementedError


class BlockPlugin(BasePlugin):
    def register_block(self, md: mistune.Markdown, name: str, pattern: str, before: str = "raw_html") -> None:
        md.block.register(name, pattern, self.parse, before=before)
        if md.renderer:
            md.renderer.register(name, self.render)

    @classmethod
    def parse(cls, block: mistune.BlockParser, m: re.Match, state: mistune.BlockState) -> int:
        raise NotImplementedError


class EmailPlugin(InlinePlugin):
    NAME = "email"

    def __call__(self, md: mistune.Markdown):
        self.register_inline(md, self.NAME, r"<email>\s*(?P<email_text>[^<]*)\s*</email>")

    @classmethod
    def parse(cls, inline, m, state) -> int:
        state.append_token({"type": cls.NAME, "raw": m.group("email_text")})
        return m.end()

    # noinspection PyMethodOverriding
    @staticmethod
    def render(renderer, address) -> str:
        enc = bytes(
            ord(a) ^ ord(k)
            for a, k in zip(address.replace("@", " <em>at</em> "), itertools.cycle(EMAIL_KEY))
        )
        safe = base64.b64encode(enc).decode().rstrip("=")
        html = '<code class="%s">' % EMAIL_CLASS + safe + "</code>"
        return html


class GlyphPlugin(InlinePlugin):
    NAME = "glyph"

    def __call__(self, md: mistune.Markdown):
        self.register_inline(md, self.NAME, r"<glyph \s*(?P<glyph_name>[\w-]+)\s*/>")

    @classmethod
    def parse(cls, inline, m, state) -> int:
        state.append_token({"type": cls.NAME, "raw": m.group("glyph_name")})
        return m.end()

    # noinspection PyMethodOverriding
    @staticmethod
    def render(renderer, glyph) -> str:
        html = '<span class="glyphicon glyphicon-%s"> </span>' % glyph
        return html


class AlertBoxPlugin(BlockPlugin):
    NAME = "alert_box"

    ALERT_TYPES = {
        "success",
        "info",
        "warning",
        "danger"
    }

    def __call__(self, md: mistune.Markdown):
        self.register_block(
            md,
            self.NAME,
            r"<alertbox\s+(?P<alert_type>\w+)\s*>"
            r"(?P<alert_text>[\s\S]*?)"
            r"</alertbox>",
            before="raw_html"
        )

    @classmethod
    def parse(cls, block, m, state) -> int:
        alert_box_type = m.group("alert_type")

        if alert_box_type not in cls.ALERT_TYPES:
            box_type_error = (
                f"Invalid argument to alertbox: \"{alert_box_type}\"."
                " Must have a single argument, any of: " + ", ".join(cls.ALERT_TYPES)
            )
            raise ValueError(box_type_error)

        text = m.group("alert_text")

        child_state = state.child_state(text)
        rules: list[str] = list(block.rules)
        rules.remove(cls.NAME)
        remove_if_present(rules, TemplatePlugin.NAME)
        block.parse(child_state, rules)

        token = {
            "type": cls.NAME,
            "attrs": {"alert_box_type": alert_box_type},
            "children": child_state.tokens,
        }

        state.append_token(token)
        return m.end() + 1

    # noinspection PyMethodOverriding
    @staticmethod
    def render(renderer, text, alert_box_type) -> str:
        html = '<div class="alert alert-%s" role="alert">' % alert_box_type
        html += text + "</div>"
        return html


class TemplatePlugin(BlockPlugin):
    NAME = "template"

    TEMPLATES = {
        "itemlist": "kirppu/vendor_item_list.html",
    }

    def __init__(self, context: Context | RequestContext):
        self._context = context

    def __call__(self, md: mistune.Markdown):
        templates = "|".join(self.TEMPLATES.keys())
        self.register_block(md, self.NAME, r"<(?P<template_type>%s)\s*/>" % templates)

    @classmethod
    def parse(cls, block: mistune.BlockParser, m: re.Match, state: mistune.BlockState) -> int:
        t_type = m.group("template_type")
        template = cls.TEMPLATES[t_type]

        state.append_token({
            "type": cls.NAME,
            "attrs": {"template_name": template},
        })
        return m.end() + 1

    # noinspection PyMethodOverriding
    def render(self, renderer: mistune.BaseRenderer, template_name: str) -> str:
        if self._context is None:
            import warnings
            warnings.warn("No context when trying to render a template %s" % template_name)
        context = self._context if self._context is None or isinstance(self._context, dict) else self._context.flatten()
        return loader.render_to_string(template_name, context)


def mark_down(text, context: typing.Optional[typing.Union[RequestContext, Context]] = None) -> str:
    m = mistune.create_markdown(
        escape=False,
        plugins=[
            'strikethrough',
            'footnotes',
            'table',
            EmailPlugin(),
            GlyphPlugin(),
            AlertBoxPlugin(),
            TemplatePlugin(context),
        ],
    )
    return m(text)


def main():
    text = """
# Heading

## Subheading

### Sub-subheading

- Un-ordered list item
  - Sub-item

1. Ordered list item

*emphasis*

**strong**

[Link title](https://...)

Email address: <email>email@example.org</email>

A glyph: <glyph volume-off />

<alertbox danger>Alert *text* content</alertbox>
    """
    print(mark_down(text))


if __name__ == '__main__':
    main()
