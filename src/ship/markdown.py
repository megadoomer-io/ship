import re

import mistune

_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
_WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]")
_TAG_RE = re.compile(r"(?<!\w)#([\w][\w/.-]+)")


def _strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text)


def _convert_wiki_links(text: str) -> str:
    def _replace(m: re.Match[str]) -> str:
        display = m.group(2) or m.group(1)
        return f"**{display}**"

    return _WIKI_LINK_RE.sub(_replace, text)


def _convert_tags(text: str) -> str:
    def _replace(m: re.Match[str]) -> str:
        tag = m.group(1)
        return f'<span class="tag">#{tag}</span>'

    return _TAG_RE.sub(_replace, text)


def _preprocess(text: str) -> str:
    text = _strip_frontmatter(text)
    text = _convert_wiki_links(text)
    text = _convert_tags(text)
    return text


_md = mistune.create_markdown(
    escape=False,
    plugins=["table", "task_lists"],
)


def render(text: str) -> str:
    preprocessed = _preprocess(text)
    result = _md(preprocessed)
    assert isinstance(result, str)
    return result
