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


ICONS = {
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "dashboard": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "pen": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "trash": '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/>',
}


@register.simple_tag
def icon(name, size=18):
    """Inline SVG icon (replaces the Font Awesome stylesheet, which blocked rendering)."""
    return mark_safe(
        f'<svg class="icon" width="{int(size)}" height="{int(size)}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true">{ICONS[name]}</svg>'
    )
