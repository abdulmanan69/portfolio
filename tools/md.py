"""
A small markdown renderer for blog posts: headings, lists, code, quotes,
tables, links, images, bold and italic. No dependencies.

Moved unchanged from the old tools/build-blog.py.
"""

import html
import re


def inline(text):
    """Inline markdown -> HTML. Code spans are protected from the other rules."""
    spans = []

    def stash(m):
        spans.append(m.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
                  r'<img loading="lazy" alt="\1" src="\2">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    for i, code in enumerate(spans):
        text = text.replace("\x00%d\x00" % i,
                            "<code>%s</code>" % html.escape(code, quote=False))
    return text


def markdown(md):
    """Block-level renderer: headings, lists, code, quotes, tables."""
    out, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):                               # fenced code
            lang, i, buf = line[3:].strip(), i + 1, []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = ' class="language-%s"' % lang if lang else ""
            out.append("<pre><code%s>%s</code></pre>"
                       % (cls, html.escape("\n".join(buf), quote=False)))
            continue

        if re.match(r"^#{1,4} ", line):                          # heading
            level = len(line) - len(line.lstrip("#"))
            out.append("<h%d>%s</h%d>" % (level, inline(line[level:].strip()), level))
            i += 1
            continue

        if re.match(r"^(---|\*\*\*)\s*$", line):                 # rule
            out.append("<hr>")
            i += 1
            continue

        if line.startswith("|") and i + 1 < len(lines) and re.match(
                r"^\|[\s:|-]+\|$", lines[i + 1].strip()):        # table
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            thead = "".join("<th>%s</th>" % inline(c) for c in head)
            tbody = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r)
                for r in rows)
            out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>"
                       % (thead, tbody))
            continue

        if re.match(r"^\s*[-*] ", line) or re.match(r"^\s*\d+\. ", line):  # list
            ordered = bool(re.match(r"^\s*\d+\. ", line))
            items = []
            while i < len(lines):
                m = re.match(r"^\s*(?:[-*]|\d+\.) (.*)$", lines[i])
                if m:
                    items.append(m.group(1).strip())
                    i += 1
                elif lines[i].strip() and items and not lines[i].startswith(
                        ("#", "```", ">", "|")):
                    items[-1] += " " + lines[i].strip()          # wrapped line
                    i += 1
                else:
                    break
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>"
                       % (tag, "".join("<li>%s</li>" % inline(t) for t in items), tag))
            continue

        if line.startswith(">"):                                 # blockquote
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>%s</p></blockquote>" % inline(" ".join(buf)))
            continue

        if not line.strip():
            i += 1
            continue

        buf = []                                                 # paragraph
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(
                ("#", "```", ">", "|", "- ", "* ")) and not re.match(r"^\d+\. ", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))
    return "\n".join(out)
