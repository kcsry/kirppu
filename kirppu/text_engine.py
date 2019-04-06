# -*- coding: utf-8 -*-

import re
import mistune

__author__ = 'codez'


class CustomTagLexer(mistune.BlockLexer):
    def __init__(self):
        super().__init__()
        self.default_rules = list(self.default_rules)
        self._custom_tags = {
            "alertbox": self._make_alert_box,
        }

    def parse_block_html(self, m):
        tag = m.group(1)
        if tag:
            action = self._custom_tags.get(tag)
            attrs = m.group(2).strip()
            text = m.group(3)
        else:
            # mistune does not parse empty block html further. Do it by hand.
            # Strip (trailing) whitespace and tag start '<' and end '/>' away.
            content = m.group(0).strip()[1:-2]
            content = content.split(" ", maxsplit=1)
            tag = content[0]
            if len(content) == 1:
                attrs = ""
            else:
                attrs = content[1]
            text = ""
            action = self._custom_tags.get(tag)

        if action:
            return action(tag, attrs, text)

        return super().parse_block_html(m)

    def _make_alert_box(self, tag, attrs, text):
        valid_attrs = {
            "success",
            "info",
            "warning",
            "danger"
        }
        if attrs not in valid_attrs:
            raise ValueError("Invalid argument to alertbox: \"" + attrs + "\"."
                             " Must have a single argument, any of: " + ", ".join(valid_attrs))

        # XXX: BootStrap specific extra content.
        self.tokens.append({
            'type': 'open_html',
            'tag': 'div',
            'extra': ' class="alert alert-%s" role="alert"' % attrs,
            'text': text
        })


class CustomInlines(mistune.InlineLexer):
    _glyph_pattern = re.compile(r"\w+")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._non_empty_tags = {
            "email": self._make_email
        }
        self._empty_tags = {
            "glyph": self._make_glyph
        }

    def output_inline_html(self, m):
        tag = m.group(1)
        non_empty = self._non_empty_tags.get(tag)
        if non_empty is not None:
            return non_empty(m)

        elif tag is None:
            # mistune does not parse empty inline html further. Do it by hand.
            # Strip tag start '<' and end '/>' away.
            content = m.group(0)[1:-2]  # type: str
            if " " in content:
                tag, attr = content.split(" ", maxsplit=1)
                attr = attr.strip()
            else:
                tag = content
                attr = ""

            empty = self._empty_tags.get(tag)
            if empty is not None:
                return empty(attr)

        return super().output_inline_html(m)

    def _make_email(self, m):
        text = m.group(3)
        return self.renderer.email(text)

    def _make_glyph(self, attr):
        if not attr or self._glyph_pattern.match(attr) is None:
            raise ValueError("glyph must have exactly one argument, the glyph name.")
        return self.renderer.glyph(attr)


class CustomTagRenderer(mistune.Renderer):
    def email(self, address):
        html = "<code>" + self.escape(address).replace("@", " <em>at</em> ") + "</code>"
        return html

    @staticmethod
    def glyph(glyph):
        # XXX: BootStrap specific format.
        html = '<span class="glyphicon glyphicon-%s"></span>' % glyph
        return html


def mark_down(text):
    renderer = CustomTagRenderer(escape=False)
    m = mistune.Markdown(
        renderer=renderer,
        inline=CustomInlines(renderer),
        block=CustomTagLexer(),
        parse_block_html=True,
    )
    return m(text)

