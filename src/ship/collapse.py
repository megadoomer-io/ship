import re

_HEADER_RE = re.compile(r"<(h[23])>(.*?)</\1>", re.DOTALL)
_TAG_STRIP_RE = re.compile(r"<[^>]+>")

COLLAPSE_RULES: dict[str, dict[str, bool]] = {
    "plan": {
        "Commitments": True,
        "GSTACK REVIEW REPORT": False,
        "Deferred": False,
        "Dropped": False,
        "Completed": False,
        "Carried Forward": False,
        "Active": False,
        "Blocked": False,
        "Retro Awareness": False,
        "Notes": False,
    },
    "retro": {
        "Plan vs Actual": True,
        "Highlights": True,
        "Trends": False,
    },
    "weekly": {
        "Highlights": True,
        "Themes": True,
        "By Project": False,
    },
}


def _strip_tags(html: str) -> str:
    return _TAG_STRIP_RE.sub("", html).strip()


def _is_open(text: str, rules: dict[str, bool] | None) -> bool:
    if not rules:
        return True
    plain = _strip_tags(text)
    for pattern, default_open in rules.items():
        if pattern.lower() in plain.lower():
            return default_open
    return True


def collapse_sections(html: str, content_type: str | None = None) -> str:
    if not content_type or not html:
        return html

    rules = COLLAPSE_RULES.get(content_type)
    if rules is None:
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

    for part in parts:
        if part["type"] == "header":
            level = part["level"]
            if level == 2:
                _close_h2()
                current_h2 = {
                    "inner_html": part["inner_html"],
                    "level": 2,
                    "open": _is_open(str(part["inner_html"]), rules),
                    "body": [],
                    "children": [],
                }
            elif level == 3:
                _close_h3()
                if current_h2 is not None:
                    current_h3 = {
                        "inner_html": part["inner_html"],
                        "level": 3,
                        "open": _is_open(str(part["inner_html"]), rules),
                        "body": [],
                    }
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

    for section in sections:
        open_attr = " open" if section["open"] else ""
        inner = str(section["inner_html"])
        out.append(f'<details class="section-collapse section-h2"{open_attr}><summary>{inner}</summary>')
        body = section["body"]
        assert isinstance(body, list)
        out.extend(str(b) for b in body)

        children = section.get("children", [])
        assert isinstance(children, list)
        for child in children:
            child_open = " open" if child["open"] else ""
            child_inner = str(child["inner_html"])
            out.append(f'<details class="section-collapse section-h3"{child_open}><summary>{child_inner}</summary>')
            child_body = child["body"]
            assert isinstance(child_body, list)
            out.extend(str(b) for b in child_body)
            out.append("</details>")

        out.append("</details>")

    return "".join(out)
