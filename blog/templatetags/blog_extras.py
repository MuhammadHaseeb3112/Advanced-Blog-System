"""Template helpers for post bodies.

render_content turns a small, safe subset of Markdown into HTML: "## " and
"### " headings, "- " lists, "> " quotes, ``` code blocks and `inline code`.
Everything is escaped first, so authors cannot inject HTML.
"""
import math
import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")


def _inline(text):
    text = escape(text)
    text = INLINE_CODE.sub(r"<code>\1</code>", text)
    return BOLD.sub(r"<strong>\1</strong>", text)


@register.filter
def render_content(value):
    lines = (value or "").replace("\r\n", "\n").split("\n")
    html, paragraph, items = [], [], []
    in_code, code = False, []

    def flush():
        if paragraph:
            html.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph.clear()
        if items:
            html.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                html.append(f"<pre><code>{escape(chr(10).join(code))}</code></pre>")
                code, in_code = [], False
            else:
                flush()
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if not stripped:
            flush()
        elif stripped.startswith("### "):
            flush()
            html.append(f"<h3>{_inline(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            flush()
            html.append(f"<h2>{_inline(stripped[3:])}</h2>")
        elif stripped.startswith("- "):
            if paragraph:
                flush()
            items.append(stripped[2:])
        elif stripped.startswith("> "):
            flush()
            html.append(f"<blockquote>{_inline(stripped[2:])}</blockquote>")
        else:
            if items:
                flush()
            paragraph.append(stripped)
    if in_code:
        html.append(f"<pre><code>{escape(chr(10).join(code))}</code></pre>")
    flush()
    return mark_safe("\n".join(html))


@register.filter
def read_time(value):
    """Minutes to read at about 220 words per minute."""
    words = len((value or "").split())
    return max(1, math.ceil(words / 220))


@register.filter
def display_name(user):
    return (user.get_full_name() or user.username) if user else ""
