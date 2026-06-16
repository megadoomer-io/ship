import re

_HEADER_RE = re.compile(r"<(h[23])[^>]*>(.*?)</\1>", re.DOTALL)
_TAG_STRIP_RE = re.compile(r"<[^>]+>")


def _strip_tags(html: str) -> str:
    return _TAG_STRIP_RE.sub("", html).strip()


def collapse_sections(html: str, content_type: str | None = None) -> str:
    if not content_type or not html:
        return html

    parts: list[dict[str, object]] = []
    last_end = 0

    for m in _HEADER_RE.finditer(html):
        if m.start() > last_end:
            parts.append({"type": "content", "html": html[last_end : m.start()]})
        parts.append(
            {
                "type": "header",
                "tag": m.group(1),
                "level": int(str(m.group(1))[1]),
                "inner_html": m.group(2),
                "raw": m.group(0),
            }
        )
        last_end = m.end()

    if last_end < len(html):
        parts.append({"type": "content", "html": html[last_end:]})

    if not any(p["type"] == "header" for p in parts):
        return html

    sections: list[dict[str, object]] = []
    current_h2: dict[str, object] | None = None
    current_h3: dict[str, object] | None = None
    preamble: list[str] = []
    h2_index = 0

    def _close_h3() -> None:
        nonlocal current_h3
        if current_h3 is not None:
            assert current_h2 is not None
            children = current_h2.setdefault("children", [])
            assert isinstance(children, list)
            children.append(current_h3)
            current_h3 = None

    def _close_h2() -> None:
        nonlocal current_h2
        _close_h3()
        if current_h2 is not None:
            sections.append(current_h2)
            current_h2 = None

    h3_index = 0
    for part in parts:
        if part["type"] == "header":
            level = part["level"]
            if level == 2:
                _close_h2()
                current_h2 = {
                    "inner_html": part["inner_html"],
                    "level": 2,
                    "open": h2_index == 0,
                    "body": [],
                    "children": [],
                }
                h2_index += 1
                h3_index = 0
            elif level == 3:
                _close_h3()
                if current_h2 is not None:
                    is_first_h2 = h2_index == 1
                    current_h3 = {
                        "inner_html": part["inner_html"],
                        "level": 3,
                        "open": is_first_h2 and h3_index == 0,
                        "body": [],
                    }
                    h3_index += 1
                else:
                    preamble.append(str(part["raw"]))
        else:
            content_html = str(part["html"])
            if current_h3 is not None:
                body = current_h3["body"]
                assert isinstance(body, list)
                body.append(content_html)
            elif current_h2 is not None:
                body = current_h2["body"]
                assert isinstance(body, list)
                body.append(content_html)
            else:
                preamble.append(content_html)

    _close_h2()

    out: list[str] = []
    out.extend(preamble)
    seen_slugs: dict[str, int] = {}

    def _unique_slug(text: str) -> str:
        base = _strip_tags(text).lower().replace(" ", "-")[:60]
        count = seen_slugs.get(base, 0)
        seen_slugs[base] = count + 1
        return base if count == 0 else f"{base}-{count}"

    for section in sections:
        open_attr = " open" if section["open"] else ""
        inner = str(section["inner_html"])
        slug = _unique_slug(inner)
        out.append(
            f'<details class="section-collapse section-h2" data-section="{slug}"{open_attr}>'
            f"<summary>{inner}</summary>"
            f'<div class="section-content">'
        )
        body = section["body"]
        assert isinstance(body, list)
        out.extend(str(b) for b in body)

        children = section.get("children", [])
        assert isinstance(children, list)
        for child in children:
            child_open = " open" if child["open"] else ""
            child_inner = str(child["inner_html"])
            child_slug = _unique_slug(child_inner)
            out.append(
                f'<details class="section-collapse section-h3" data-section="{child_slug}"{child_open}>'
                f"<summary>{child_inner}</summary>"
                f'<div class="section-content">'
            )
            child_body = child["body"]
            assert isinstance(child_body, list)
            out.extend(str(b) for b in child_body)
            out.append("</div></details>")

        out.append("</div></details>")

    return "".join(out)
